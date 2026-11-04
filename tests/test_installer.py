import base64
import gzip
import http.client
import http.server
import io
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import time
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
KEY = "TEST_ONLY_NOT_A_REAL_KEY"
GEO = "db-ip-geolocation.mmdb"
CLOUD = "db-cloud-provider.csv.gz"


def archive(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as bundle:
        for name, content in entries:
            bundle.writestr(name, content)
    return output.getvalue()


class InstallerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory(prefix="ipgeo-http-")
        cls.server_dir = Path(cls.shared.name).resolve()
        cls.good = [(GEO, (ROOT / "tests/fixtures" / GEO).read_bytes()),
                    (CLOUD, gzip.compress(b"Example Network\n", mtime=0))]
        cls.cases = {
            "valid": {"status": 200, "body": archive(cls.good)},
            "slow": {"status": 200, "body": archive(cls.good), "delay": 3000},
            "unauthorized": {"status": 401, "body": b"Unauthorized"},
            "server-error": {"status": 500, "body": b"Server error"},
            "truncated": {"status": 200, "body": archive(cls.good)[:80]},
            "not-zip": {"status": 200, "body": b"not a zip"},
            "missing-geo": {"status": 200, "body": archive(cls.good[1:])},
            "missing-cloud": {"status": 200, "body": archive(cls.good[:1])},
            "bad-mmdb": {"status": 200, "body": archive([(GEO, b"bad"), cls.good[1]])},
            "bad-gzip": {"status": 200, "body": archive([cls.good[0], (CLOUD, b"bad")])},
            "empty-csv": {"status": 200, "body": archive([cls.good[0], (CLOUD, gzip.compress(b""))])},
            "bad-csv": {"status": 200, "body": archive([cls.good[0], (CLOUD, gzip.compress(b"one,two\n"))])},
            "traversal": {"status": 200, "body": archive(cls.good + [("../outside.mmdb", b"bad")])},
            "duplicate": {"status": 200, "body": archive(cls.good + [cls.good[0]])},
            "unrelated": {"status": 200, "body": archive(cls.good + [("../outside.txt", b"ignored")])},
        }
        mock = cls.server_dir / "postman"
        shutil.copytree(ROOT / "postman/simulations/database-installer", mock)
        (mock / "mock/cases.json").write_text(json.dumps({
            name: dict(case, body=base64.b64encode(case["body"]).decode())
            for name, case in cls.cases.items()
        }))
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            cls.mock_port = probe.getsockname()[1]
        cls.log = (cls.server_dir / "postman.ndjson").open("w+")
        cls.mock = subprocess.Popen([
            "postman", "simulation", "run", str(mock / "simulation.yaml"),
            "--port", str(cls.mock_port), "--output", "ndjson", "--no-history"
        ], stdout=cls.log, stderr=cls.log)
        cls.addClassCleanup(cls.stop_mock)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if '"event":"listening"' in (cls.server_dir / "postman.ndjson").read_text():
                break
            if cls.mock.poll() is not None:
                raise RuntimeError((cls.server_dir / "postman.ndjson").read_text())
            time.sleep(.1)
        else:
            raise RuntimeError("Postman did not start")
        cert, key = cls.server_dir / "cert.pem", cls.server_dir / "key.pem"
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
            "-subj", "/CN=database.ipgeolocation.io", "-addext",
            "subjectAltName=DNS:database.ipgeolocation.io", "-keyout", str(key), "-out", str(cert)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        class Bridge(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                connection = http.client.HTTPConnection("127.0.0.1", cls.mock_port, timeout=15)
                connection.request("GET", "/database" + self.path)
                response = connection.getresponse()
                data = response.read()
                self.send_response(response.status)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ssl.SSLEOFError):
                    pass
                connection.close()
            def log_message(self, *args):
                pass
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Bridge)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.addClassCleanup(cls.server.shutdown)
        cls.addClassCleanup(cls.server.server_close)
        cls.curl = shutil.which("curl")
        cls.cert = str(cert)

    @classmethod
    def stop_mock(cls):
        cls.mock.terminate()
        cls.mock.wait(timeout=10)
        cls.log.close()
        cls.shared.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ipgeo-installer-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.data = self.base / "data"
        self.extract = self.base / "extract"
        self.data.mkdir()
        self.extract.mkdir()
        (self.data / GEO).write_bytes(b"previous geo")
        (self.data / GEO).chmod(0o640)
        (self.data / CLOUD).write_bytes(b"previous cloud")
        (self.data / "other.mmdb").write_bytes(b"unrelated database")
        (self.extract / "keep.txt").write_text("existing file")

    def start(self, case="valid", fault="", flags=None, env_key=True, key=KEY):
        env = os.environ.copy()
        if env_key:
            env["IPGEOLOCATION_API_KEY"] = key
        else:
            env.pop("IPGEOLOCATION_API_KEY", None)
        env.update(TEST_CURL=self.curl, TEST_CERT=self.cert,
                   TEST_TLS_PORT=str(self.server.server_port), TEST_ARGS=str(self.base / "curl-args"))
        script = '''
curl() {
  printf '%s\\n' "$@" > "$TEST_ARGS"
  [[ -z "${IPGEOLOCATION_API_KEY:-}" ]] || return 99
  "$TEST_CURL" --noproxy '*' --cacert "$TEST_CERT" --connect-to "database.ipgeolocation.io:443:127.0.0.1:$TEST_TLS_PORT" "$@"
}
source "$1"
shift
''' + fault + '\nsetup_database "$@"\n'
        args = flags if flags is not None else ["-d", case, "-t", str(self.data), "-e", str(self.extract)]
        self.output = (self.base / ("output-" + str(time.monotonic_ns()))).open("w+")
        self.addCleanup(self.output.close)
        return subprocess.Popen(["bash", "-c", script, "test-installer", str(ROOT / "setup_database.sh"), *args],
                                cwd=self.base, env=env, stdout=self.output, stderr=self.output, start_new_session=True)

    def run_case(self, case="valid", **kwargs):
        process = self.start(case, **kwargs)
        code = process.wait(timeout=30)
        self.output.seek(0)
        output = self.output.read()
        self.assertNotIn(KEY, output)
        if (self.base / "curl-args").exists():
            args = (self.base / "curl-args").read_text()
            self.assertNotIn(KEY, args)
            self.assertNotIn("apiKey=", args)
        return code, output

    def assert_preserved(self):
        self.assertEqual(b"previous geo", (self.data / GEO).read_bytes())
        self.assertEqual(b"previous cloud", (self.data / CLOUD).read_bytes())
        self.assert_unrelated()

    def assert_unrelated(self):
        self.assertEqual(b"unrelated database", (self.data / "other.mmdb").read_bytes())
        self.assertEqual("existing file", (self.extract / "keep.txt").read_text())
        self.assertFalse(list(self.data.glob(".ipgeo-*")))
        self.assertFalse(list(self.extract.glob(".ipgeo-*")))

    def test_success_preserves_other_files_and_permissions(self):
        self.assertEqual(0, self.run_case()[0])
        self.assertEqual(self.good[0][1], (self.data / GEO).read_bytes())
        self.assertEqual(0o640, (self.data / GEO).stat().st_mode & 0o777)
        self.assert_unrelated()

    def test_failed_downloads_preserve_existing_databases(self):
        for name in self.cases:
            if name in ("valid", "slow", "unrelated"):
                continue
            with self.subTest(name=name):
                self.assertNotEqual(0, self.run_case(name)[0])
                self.assert_preserved()

    def test_never_extracts_unrelated_archive_paths(self):
        self.assertEqual(0, self.run_case("unrelated")[0])
        self.assertFalse((self.base / "outside.txt").exists())
        self.assert_unrelated()

    def test_existing_api_key_flag(self):
        args = ["-a", KEY, "-d", "valid", "-t", str(self.data), "-e", str(self.extract)]
        self.assertEqual(0, self.run_case(flags=args, env_key=False)[0])

    def test_overlapping_and_relative_directories(self):
        for data, extract in [("same space", "same space"), ("parent/data", "parent"), ("data2", "data2/extract")]:
            with self.subTest(data=data, extract=extract):
                args = ["-d", "valid", "-t", data, "-e", extract]
                self.assertEqual(0, self.run_case(flags=args)[0])
                self.assertEqual(self.good[0][1], (self.base / data / GEO).read_bytes())
                self.assertEqual(0o644, (self.base / data / GEO).stat().st_mode & 0o777)

    def test_symbolic_link_destination_is_rejected(self):
        victim = self.base / "victim"
        victim.write_text("unchanged")
        (self.data / GEO).unlink()
        (self.data / GEO).symlink_to(victim)
        self.assertNotEqual(0, self.run_case()[0])
        self.assertEqual("unchanged", victim.read_text())
        self.assertTrue((self.data / GEO).is_symlink())
        self.assert_unrelated()

    def test_symbolic_link_and_writable_directories_are_rejected(self):
        link = self.base / "link"
        link.symlink_to(self.data, target_is_directory=True)
        for path in (str(link), "/"):
            args = ["-d", "valid", "-t", path, "-e", str(self.extract)]
            self.assertNotEqual(0, self.run_case(flags=args)[0])
        self.extract.chmod(0o777)
        self.assertNotEqual(0, self.run_case()[0])
        self.assert_preserved()

    def test_failure_after_first_replacement_rolls_back(self):
        fault = '''mv() { if [[ "$*" == *"/new/db-cloud-provider.csv.gz"* ]]; then return 1; fi; command mv "$@"; }'''
        self.assertNotEqual(0, self.run_case(fault=fault)[0])
        self.assert_preserved()

    def test_termination_after_first_replacement_rolls_back(self):
        fault = '''mv() { command mv "$@" || return; if [[ "$*" == *"/new/db-ip-geolocation.mmdb"* ]]; then python3 -c 'import os, signal; os.kill(os.getppid(), signal.SIGTERM)'; fi; }'''
        self.assertEqual(143, self.run_case(fault=fault)[0])
        self.assert_preserved()

    def test_concurrent_update_is_rejected(self):
        first = self.start("slow")
        deadline = time.monotonic() + 10
        while not (self.data / ".ipgeo-setup.lock").exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertNotEqual(0, self.run_case()[0])
        self.assertEqual(0, first.wait(timeout=30))
        self.assert_unrelated()

    def test_directory_swap_is_rejected(self):
        victim = self.base / "victim"
        victim.mkdir()
        (victim / "keep").write_text("unchanged")
        fault = '''mkdir() { command mkdir "$@" || return; if [[ "$*" == *"/extract" ]]; then command rmdir "$PWD/new-data"; command ln -s "$PWD/victim" "$PWD/new-data"; fi; }'''
        args = ["-d", "valid", "-t", str(self.base / "new-data"), "-e", str(self.extract)]
        self.assertNotEqual(0, self.run_case(fault=fault, flags=args)[0])
        self.assertEqual(["keep"], sorted(p.name for p in victim.iterdir()))

    def test_cleanup_failure_still_releases_lock(self):
        fault = '''rm() { if [[ "$*" == *"/.ipgeo-stage."* ]]; then return 1; fi; command rm "$@"; }'''
        self.assertNotEqual(0, self.run_case(fault=fault)[0])
        self.assertFalse((self.data / ".ipgeo-setup.lock").exists())
        self.assertFalse(list(self.extract.glob(".ipgeo-*")))
        self.assertEqual(self.good[0][1], (self.data / GEO).read_bytes())

    def test_missing_arguments_show_usage(self):
        code, output = self.run_case(flags=[], env_key=False)
        self.assertNotEqual(0, code)
        self.assertIn("Usage:", output)
        self.assert_preserved()

    def test_invalid_inputs_fail_before_download(self):
        for key in ("line\nbreak", "line\rbreak"):
            self.assertNotEqual(0, self.run_case(key=key)[0])
        self.assertNotEqual(0, self.run_case("../database")[0])
        self.assertFalse((self.base / "curl-args").exists())
        self.assert_preserved()

    def test_command_entry_and_service_user_readability(self):
        args = ["bash", str(ROOT / "setup_database.sh"), "-d", "valid",
                "-t", str(self.data), "-e", str(self.extract)]
        env = os.environ.copy()
        env["IPGEOLOCATION_API_KEY"] = KEY
        if os.geteuid() != 0:
            result = subprocess.run(args, env=env, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("Please run as root", result.stdout)
            self.assert_preserved()
            return
        self.base.chmod(0o755)
        self.data.chmod(0o755)
        os.chown(self.data / GEO, 65534, 65534)
        (self.data / CLOUD).unlink()
        commands = self.base / "bin"
        commands.mkdir()
        wrapper = commands / "curl"
        wrapper.write_text('''#!/bin/bash
exec "$TEST_CURL" --noproxy '*' --cacert "$TEST_CERT" --connect-to "database.ipgeolocation.io:443:127.0.0.1:$TEST_TLS_PORT" "$@"
''')
        wrapper.chmod(0o755)
        env.update(PATH=str(commands) + os.pathsep + env["PATH"], TEST_CURL=self.curl,
                   TEST_CERT=self.cert, TEST_TLS_PORT=str(self.server.server_port))
        result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(65534, (self.data / GEO).stat().st_uid)
        self.assertEqual(65534, (self.data / GEO).stat().st_gid)
        self.assertEqual(0o640, (self.data / GEO).stat().st_mode & 0o777)
        for name, expected in self.good:
            result = subprocess.run(["cat", str(self.data / name)], user=65534, group=65534, capture_output=True)
            self.assertEqual(0, result.returncode)
            self.assertEqual(expected, result.stdout)
        self.assert_unrelated()

    def test_requests_reached_the_simulation(self):
        self.assertEqual(0, self.run_case()[0])
        log = (self.server_dir / "postman.ndjson").read_text()
        self.assertIn('"event":"request"', log)
        self.assertIn("/download/valid", log)


if __name__ == "__main__":
    unittest.main(verbosity=2)
