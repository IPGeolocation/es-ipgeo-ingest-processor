# Installation Guide for IPGeolocation Ingest Processor Plugin

This guide provides detailed instructions for installing the IPGeolocation Ingest Processor plugin in Elasticsearch. The installation process has been tested on Linux (Ubuntu 22.04).

## Prerequisites

### 1. Java 21
You must have Java 21 installed on your system. Follow this guide to install Java 21 on Linux: [Install Java 21 on Linux](https://www.oracle.com/java/technologies/javase/jdk21-archive-downloads.html).

### 2. Elasticsearch 8.13.3
Install Elasticsearch 8.13.3, the version the published plugin build is compiled for. Follow the official Elasticsearch documentation for installation instructions based on your operating system: [Install ELK Stack](https://www.elastic.co/guide/en/elastic-stack/current/installing-elastic-stack.html).

> **Note**: The published build (plugin version 1.0.0) is built for Elasticsearch 8.13.3 and requires JDK 21. Any other Elasticsearch version needs a build compiled for that version; see the next step.

## Installation Instructions

### 1. Download and Prepare the Files

To proceed with the installation, you will need the zip file provided in the repository and the shell script (`setup_database.sh`) included in this repository. First, complete the prerequisites and then clone the repository:

```sh
git clone https://github.com/IPGeolocation/es-ipgeo-ingest-processor.git
cd es-ipgeo-ingest-processor
```

### 2. Match the Elasticsearch Version

Classic Elasticsearch plugins must be built for each Elasticsearch release, and Elasticsearch checks the version when it installs and loads the plugin. The zip in this repository is built for Elasticsearch 8.13.3 (`elasticsearch.version=8.13.3` in its `plugin-descriptor.properties`). If you run a different version, [contact support](https://ipgeolocation.io/contact.html) for a build compiled for it, and test it before deployment. Do not edit `elasticsearch.version` to make this build install on another version: that skips the check but does not rebuild the plugin.

### 3. Install the Plugin

You can install the plugin by specifying the Elasticsearch plugins directory and the path to the zip file:

```sh
sudo /usr/share/elasticsearch/bin/elasticsearch-plugin install file:/home/elk-plugin/es-ipgeo-ingest-processor.zip
```
> **Note**: `/home/elk-plugin` is the home directory of the server where the plugin is being installed.

This command will output a confirmation message indicating that the plugin has been installed successfully and that Elasticsearch needs to be restarted.

### 4. Run the Setup Database Script

Before restarting Elasticsearch, run the setup database script to configure the necessary databases. To see the usage of this script, run:

```sh
sudo ./setup_database.sh
```

This will display the following usage information:

```sh
Usage: ./setup_database.sh -a <api_key> -d <database_name> -t <data_directory> -e <extraction_directory>
```

- **API Key (`-a <api_key>`)**: Your IPGeolocation API key.
- **Database Name (`-d <database_name>`)**: The name of the database you are using from IPGeolocation.
- **Data Directory (`-t <data_directory>`)**: The configuration directory of Elasticsearch on your system. For Debian packages, this is usually `/etc/elasticsearch/`.
- **Extraction Directory (`-e <extraction_directory>`)**: Any directory on your system where temporary files can be extracted.

Make sure to run this script with `sudo` and provide the required arguments. Here is an example command:

```sh
sudo ./setup_database.sh -a <api_key> -d <database_name> -t /etc/elasticsearch/ipgeo -e /home/elk-plugin/ipgeo
```

You do not need to create the `extraction_directory` (e.g., `ipgeo` above) manually. The script will create it if it does not exist and then delete it once the process is complete. This script will download the necessary database from IPGeolocation.io and place the required files in the plugin directory (e.g., `/etc/elasticsearch/ipgeo`).

To obtain your API key and database name, please contact our support: [Contact Support](https://ipgeolocation.io/contact.html).

### 5. Verify Database Download

Verify that the databases have been downloaded and placed correctly:

```sh
sudo ls -lah /etc/elasticsearch/ipgeo
```

If you see files in the folder, it means the setup was successful, and you are ready to restart Elasticsearch.

### 6. Restart Elasticsearch

Restart Elasticsearch depending on how it was installed:

```sh
sudo systemctl restart elasticsearch.service
```

If it restarts without errors, it means the plugin has been installed successfully.

## Conclusion

By following these steps, you should have the IPGeo Ingest Processor plugin installed and configured correctly with your Elasticsearch setup. If you encounter any issues or need further assistance, please [contact our support](https://ipgeolocation.io/contact.html).
