#!/bin/bash

print_msg() {
  printf '%s\n' "$2"
}

setup_database() (
  set -eo pipefail
  umask 077
  api_key="${IPGEOLOCATION_API_KEY:-}" database_name="" data_directory="" extraction_directory=""
  opt="" work="" stage="" lock="" committed=0 lock_owned=0
  files=() installed=()
  unset IPGEOLOCATION_API_KEY

  fail() { printf '%s\n' "$*" >&2; exit 1; }

  cleanup() {
    local status=$? name rollback_failed=0
    trap - EXIT INT TERM
    set +e
    if [[ "$committed" -eq 0 && -n "$stage" ]]; then
      for name in "${installed[@]}"; do
        if [[ -f "$stage/backup/$name" ]]; then
          mv -f -- "$stage/backup/$name" "$data_directory/$name" || rollback_failed=1
        else
          rm -f -- "$data_directory/$name" || rollback_failed=1
        fi
      done
    fi
    if [[ "$rollback_failed" -eq 0 ]]; then
      [[ -z "$stage" ]] || rm -rf -- "$stage" || status=1
    else
      printf 'Could not restore all files. Backups remain in %s\n' "$stage" >&2
      status=1
    fi
    [[ -z "$work" ]] || rm -rf -- "$work" || status=1
    [[ "$lock_owned" -eq 0 ]] || rmdir -- "$lock" || status=1
    exit "$status"
  }
  trap cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM

  OPTIND=1
  while getopts "a:d:t:e:" opt; do
    case "$opt" in
      a) api_key="$OPTARG" ;;
      d) database_name="$OPTARG" ;;
      t) data_directory="$OPTARG" ;;
      e) extraction_directory="$OPTARG" ;;
      *) fail "Usage: $0 -a <api_key> -d <database_name> -t <data_directory> -e <extraction_directory>" ;;
    esac
  done
  shift "$((OPTIND - 1))"
  [[ $# -eq 0 && -n "$api_key" && -n "$database_name" && -n "$data_directory" && -n "$extraction_directory" ]] ||
    fail "Usage: $0 -a <api_key> -d <database_name> -t <data_directory> -e <extraction_directory>"
  [[ "$database_name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || fail "Invalid database name."
  [[ "$api_key" != *$'\n'* && "$api_key" != *$'\r'* ]] || fail "Invalid API key."

  for opt in curl unzip java gzip mktemp stat; do
    command -v "$opt" >/dev/null || fail "Required command is missing: $opt"
  done

  secure_path() {
    local path="$1" owner mode
    while :; do
      if [[ -e "$path" || -L "$path" ]]; then
        [[ -d "$path" && ! -L "$path" ]] || fail "Use a real directory, not a symbolic link: $path"
        if owner=$(stat -c '%u' "$path" 2>/dev/null); then
          mode=$(stat -c '%a' "$path")
        else
          owner=$(stat -f '%u' "$path")
          mode=$(stat -f '%p' "$path")
        fi
        [[ "$owner" -eq 0 || "$owner" -eq "$EUID" ]] || fail "Directory must be owned by the current user or root: $path"
        if (( (8#$mode & 0022) != 0 )); then
          (( owner == 0 && (8#$mode & 01000) != 0 )) || fail "Directory must not be writable by other users: $path"
        fi
      fi
      [[ "$path" == "/" ]] && break
      path=$(dirname -- "$path")
    done
  }

  absolute_path() {
    local path="$1" base
    [[ "$path" == /* ]] || path="$PWD/$path"
    while [[ ! -e "$path" && ! -L "$path" ]]; do
      base="/$(basename -- "$path")${base:-}"
      path=$(dirname -- "$path")
    done
    [[ -d "$path" && ! -L "$path" ]] || fail "Directory is not usable: $path"
    secure_path "$path"
    printf '%s%s\n' "$(cd -P -- "$path" && pwd)" "${base:-}"
  }

  extraction_directory=$(absolute_path "$extraction_directory")
  data_directory=$(absolute_path "$data_directory")
  [[ "$data_directory" != "/" && "$extraction_directory" != "/" ]] || fail "Do not use the filesystem root as a setup directory."
  secure_path "$extraction_directory"
  secure_path "$data_directory"
  (umask 022; mkdir -p -- "$data_directory")
  mkdir -p -- "$extraction_directory"
  secure_path "$data_directory"
  secure_path "$extraction_directory"
  data_directory=$(cd -P -- "$data_directory" && pwd)
  extraction_directory=$(cd -P -- "$extraction_directory" && pwd)
  [[ "$data_directory" != "/" && "$extraction_directory" != "/" ]] || fail "Do not use the filesystem root as a setup directory."
  secure_path "$data_directory"
  secure_path "$extraction_directory"
  lock="$data_directory/.ipgeo-setup.lock"
  mkdir -- "$lock" 2>/dev/null || fail "Another setup may be running: $lock"
  lock_owned=1
  work=$(mktemp -d "$extraction_directory/.ipgeo-download.XXXXXXXX")
  stage=$(mktemp -d "$data_directory/.ipgeo-stage.XXXXXXXX")
  mkdir -- "$work/candidate" "$stage/new" "$stage/backup"

  local script_directory bundle jar_entry escaped_key
  script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
  bundle="$script_directory/es-ipgeo-ingest-processor.zip"
  [[ -f "$bundle" ]] || fail "Keep es-ipgeo-ingest-processor.zip beside setup_database.sh."
  jar_entry=$(unzip -Z -1 "$bundle" | grep -E '^es-ipgeo-ingest-processor-[0-9.]+-jar-with-dependencies\.jar$')
  [[ -n "$jar_entry" && "$jar_entry" != *$'\n'* ]] || fail "The plugin ZIP must contain exactly one plugin JAR."
  unzip -p "$bundle" "$jar_entry" > "$work/plugin.jar"

  escaped_key="${api_key//\\/\\\\}"
  escaped_key="${escaped_key//\"/\\\"}"
  printf 'url = "https://database.ipgeolocation.io/download/%s"\nget\ndata-urlencode = "apiKey=%s"\n' "$database_name" "$escaped_key" > "$work/request.conf"
  unset api_key escaped_key
  print_msg blue "Downloading database..."
  if ! curl --config "$work/request.conf" --fail --silent --show-error --location \
      --proto '=https' --proto-redir '=https' --connect-timeout 30 --speed-time 120 --speed-limit 1 \
      --output "$work/db.zip" 2>"$work/download.log"; then
    fail "Database download failed. Existing database files were not changed."
  fi
  rm -f -- "$work/request.conf"
  unzip -tqq "$work/db.zip" >"$work/archive.log" 2>&1 || fail "The downloaded ZIP is invalid."
  unzip -Z -1 "$work/db.zip" > "$work/entries"
  local entry existing
  while IFS= read -r entry; do
    case "$entry" in
      *.mmdb|db-cloud-provider.csv.gz)
        [[ "$entry" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || fail "Invalid database path in ZIP."
        for existing in "${files[@]}"; do
          [[ "$existing" != "$entry" ]] || fail "Duplicate database file in ZIP: $entry"
        done
        files+=("$entry")
        unzip -p "$work/db.zip" "$entry" > "$work/candidate/$entry" || fail "Could not read database file: $entry"
        ;;
    esac
  done < "$work/entries"

  java -cp "$work/plugin.jar" io.ipgeolocation.ingest.ipgeo.DatabaseValidator "$work/candidate" \
    > "$work/validation.log" 2>&1 || fail "Downloaded database files could not be validated."

  for entry in "${files[@]}"; do
    existing="$data_directory/$entry"
    [[ ! -L "$existing" ]] || fail "Refusing to replace a symbolic link: $entry"
    if [[ -e "$existing" ]]; then
      [[ -f "$existing" ]] || fail "Database destination is not a regular file: $entry"
      cp -p -- "$existing" "$stage/backup/$entry"
      cp -p -- "$existing" "$stage/new/$entry"
      cat -- "$work/candidate/$entry" > "$stage/new/$entry"
    else
      cp -- "$work/candidate/$entry" "$stage/new/$entry"
      chmod 644 "$stage/new/$entry"
    fi
  done
  for entry in "${files[@]}"; do
    installed+=("$entry")
    mv -f -- "$stage/new/$entry" "$data_directory/$entry"
  done
  committed=1
  print_msg green "Database setup completed successfully."
)

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  if [[ "$EUID" -ne 0 ]]; then
    print_msg red "Please run as root using sudo"
    exit 1
  fi
  setup_database "$@"
fi
