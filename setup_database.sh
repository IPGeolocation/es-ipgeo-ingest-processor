#!/bin/bash

print_msg() {
  local color="$1"
  local msg="$2"
  case "$color" in
    "red")
      echo -e "\033[31m$msg\033[0m"
      ;;
    "green")
      echo -e "\033[32m$msg\033[0m"
      ;;
    "yellow")
      echo -e "\033[33m$msg\033[0m"
      ;;
    "blue")
      echo -e "\033[34m$msg\033[0m"
      ;;
    *)
      echo "$msg"
      ;;
  esac
}

if [[ "$EUID" -ne 0 ]]; then
  print_msg "red" "Please run as root using sudo"
  exit 1
fi

usage() {
  echo "Usage: $0 -a <api_key> -d <database_name> -t <data_directory> -e <extraction_directory>"
  exit 1
}

while getopts "a:d:t:e:" opt; do
  case $opt in
    a) api_key="$OPTARG" ;;
    d) database_name="$OPTARG" ;;
    t) data_directory="$OPTARG" ;;
    e) extraction_directory="$OPTARG" ;;
    *) usage ;;
  esac
done

if [[ -z "$api_key" || -z "$database_name" || -z "$data_directory" || -z "$extraction_directory" ]]; then
  usage
fi

if [[ -d "$extraction_directory" ]]; then
  print_msg "yellow" "Extraction directory exists, removing..."
  sudo rm -rf "$extraction_directory"
fi
print_msg "blue" "Creating extraction directory..."
sudo mkdir -p "$extraction_directory"

cd "$extraction_directory"

database_url="https://database.ipgeolocation.io/download/${database_name}?apiKey=${api_key}"
zip_path="${extraction_directory}/db.zip"

print_msg "blue" "Downloading database..."
if sudo curl -o "$zip_path" "$database_url"; then
  print_msg "green" "Database downloaded successfully."
else
  print_msg "red" "Failed to download database."
  exit 1
fi

print_msg "blue" "Unzipping database..."
if sudo unzip -o "$zip_path" -d "$extraction_directory"; then
  print_msg "green" "Database unzipped successfully."
else
  print_msg "red" "Failed to unzip database."
  exit 1
fi

if [[ -d "$data_directory" ]]; then
  print_msg "yellow" "Data directory exists, removing old MMDB files..."
  sudo rm -f "$data_directory"/*.mmdb
else
  print_msg "blue" "Creating data directory..."
  sudo mkdir -p "$data_directory"
fi

print_msg "blue" "Moving MMDB files to data directory..."
if sudo mv "$extraction_directory"/*.mmdb "$data_directory"; then
  print_msg "green" "MMDB files moved successfully."
else
  print_msg "red" "Failed to move MMDB files."
  exit 1
fi
print_msg "blue" "Moving cloud provider files to data directory..."
if sudo mv "$extraction_directory"/db-cloud-provider.csv.gz "$data_directory"; then
          print_msg "green" "MMDB files moved successfully."
  else
            print_msg "red" "Failed to move MMDB files."
              exit 1
fi

print_msg "blue" "Removing extraction directory..."
if sudo rm -rf "$extraction_directory"; then
  print_msg "green" "Extraction directory removed successfully."
else
  print_msg "red" "Failed to remove extraction directory."
  exit 1
fi

print_msg "green" "Database setup completed successfully."
