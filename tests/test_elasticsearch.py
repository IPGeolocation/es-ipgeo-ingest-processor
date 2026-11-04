import gzip
import json
import os
from pathlib import Path
import time
import unittest
import urllib.request


BASE = os.environ.get("ELASTICSEARCH_TEST_URL", "http://127.0.0.1:19201")


def request(method, path, value=None):
    body = None if value is None else json.dumps(value).encode()
    req = urllib.request.Request(BASE + path, data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def simulate(options=None, source=None):
    config = {"field": "ip", "database_version": "DB-IV"}
    config.update(options or {})
    return request("POST", "/_ingest/pipeline/_simulate", {
        "pipeline": {"processors": [{"ipgeo": config}]},
        "docs": [{"_source": {"ip": "8.8.8.8"} if source is None else source}]
    })["docs"][0]


class ElasticsearchTest(unittest.TestCase):
    def test_installed_version(self):
        self.assertEqual("8.13.3", request("GET", "/")["version"]["number"])
        nodes = request("GET", "/_nodes/plugins")["nodes"].values()
        for node in nodes:
            plugin = next(p for p in node["plugins"] if p["name"] == "ipgeo")
            self.assertEqual("1.0.1", plugin["version"])

    def test_database_versions_and_languages(self):
        for version in ("DB-I", "DB-II", "DB-III", "DB-IV", "DB-V", "DB-VI", "DB-VII"):
            for ip in ("8.8.8.8", "2001:4860::8888"):
                for language, country in (("en", "United States"), ("ar", "الولايات المتحدة")):
                    with self.subTest(version=version, ip=ip, language=language):
                        result = simulate({"database_version": version, "language": language,
                                           "include": "security"}, {"ip": ip})
                        geo = result["doc"]["_source"]["ipgeo"]
                        self.assertEqual(country, geo["country_name"])
                        self.assertEqual(version in ("DB-II", "DB-IV", "DB-VI", "DB-VII"), "location" in geo)
                        self.assertEqual(version in ("DB-V", "DB-VI", "DB-VII"), "security" in geo)

    def test_field_selection_and_nested_target(self):
        self.assertEqual({"country_name": "United States"}, simulate({"fields": "country_name"})["doc"]["_source"]["ipgeo"])
        geo = simulate({"fields": "country_name,latitude,longitude", "excludes": "country_name"})["doc"]["_source"]["ipgeo"]
        self.assertEqual({"location"}, set(geo))
        result = simulate({"target_field": "enrichment.geo", "language": "ar"})["doc"]["_source"]
        self.assertEqual("الولايات المتحدة", result["enrichment"]["geo"]["country_name"])
        result = simulate({"fields": "latitude"})["doc"]["_source"]["ipgeo"]
        self.assertEqual({"latitude"}, set(result))

    def test_missing_invalid_and_unknown_addresses(self):
        for source in ({}, {"ip": None}):
            self.assertEqual(source, simulate({"ignore_missing": True}, source)["doc"]["_source"])
            self.assertIn("error", simulate(source=source))
        for value in ("not-an-ip", "999.1.1.1", "example.com", 123):
            self.assertIn("error", simulate(source={"ip": value}))
        self.assertEqual({"ip": "1.1.1.1"}, simulate(source={"ip": "1.1.1.1"})["doc"]["_source"])

    def test_indexing_with_geo_point_mapping(self):
        request("PUT", "/_ingest/pipeline/ipgeo-package-check", {"processors": [{"ipgeo": {
            "field": "ip", "database_version": "DB-IV", "language": "ar"
        }}]})
        request("PUT", "/ipgeo-package-check", {"settings": {"number_of_replicas": 0}, "mappings": {"properties": {
            "ipgeo": {"properties": {"location": {"type": "geo_point"}}}
        }}})
        try:
            request("PUT", "/ipgeo-package-check/_doc/1?pipeline=ipgeo-package-check&refresh=true", {"ip": "8.8.8.8"})
            source = request("GET", "/ipgeo-package-check/_doc/1")["_source"]
            self.assertEqual("الولايات المتحدة", source["ipgeo"]["country_name"])
            self.assertIn("location", source["ipgeo"])
        finally:
            request("DELETE", "/ipgeo-package-check")
            request("DELETE", "/_ingest/pipeline/ipgeo-package-check")

    def test_atomic_cloud_file_replacement_reloads(self):
        directory = os.environ.get("ELASTICSEARCH_TEST_CONFIG")
        if not directory:
            self.skipTest("ELASTICSEARCH_TEST_CONFIG is needed for the file-watcher check")
        target = Path(directory) / "ipgeo/db-cloud-provider.csv.gz"
        original = target.read_bytes()
        def score():
            return simulate({"database_version": "DB-VII", "include": "security"})["doc"]["_source"]["ipgeo"]["security"]["threat_score"]
        def replace(data, expected):
            temporary = target.with_suffix(".new")
            temporary.write_bytes(data)
            temporary.replace(target)
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if score() == expected:
                    return
                time.sleep(.2)
            self.fail("Cloud-provider data was not reloaded")
        self.assertEqual(15, score())
        try:
            replace(gzip.compress(b"Other Provider\n", mtime=0), 10)
        finally:
            replace(original, 15)


if __name__ == "__main__":
    unittest.main(verbosity=2)
