# ES IPGeo Ingest Processor

The Elastic Search IPGeo Ingest Processor contains the [es-ipgeo-ingest-processor.zip](https://github.com/IPGeolocation/es-ipgeo-ingest-processor), an Elasticsearch ingest processor plugin designed to enrich documents containing an IP address with geolocation, currency, security, and timezone data using the ipgeolocation.io databases. Depending on the type of ipgeolocation.io database you are using, you can access various types of data such as country, city, latitude, longitude, timezone, currency information, and security details.

The enriched documents can then be used for visualization in Kibana, providing a powerful way to analyze and display geospatial data. The processor can also be integrated with Logstash to enrich real-time logs, index them into Elasticsearch, and then visualize the data in Kibana. This repository contains all the instructions and examples for installation and usage with Elasticsearch, Logstash, and Kibana.

For more information on available databases, visit [ipgeolocation.io databases information](https://ipgeolocation.io/db-pricing.html).

## Features

- **Geolocation Enrichment**: Automatically enriches documents with detailed geolocation data such as country, city, latitude, longitude and much more.
- **Currency Information**: Adds currency data based on the IP address location.
- **Security Details**: Includes security-related information such as whether the IP is a known attacker, proxy, or belongs to a cloud provider.
- **Timezone Data**: Provides timezone information for the IP address, including the current time and offset.

## Installation

Please refer to [installation.md](https://github.com/IPGeolocation/es-ipgeo-ingest-processor/blob/main/docs/installation.md) for detailed instructions on how to install the plugin.

### Installation Overview

1. **Prerequisites**: Ensure you have Java 21 and the latest version of the ELK stack installed.
2. **Download and Prepare Files**: Clone the repository and prepare the required zip and shell script files.
3. **Configure Plugin Version**: Set the appropriate Elasticsearch version in the `plugin-descriptor.properties` file.
4. **Install the Plugin**: Use the Elasticsearch plugin installation command to install the plugin.
5. **Run the Setup Database Script**: Configure and download the necessary databases using the provided script.
6. **Verify Installation**: Ensure the databases are correctly placed and restart Elasticsearch.

## Usage With Elasticsearch

Refer to [usage-with-es.md](https://github.com/IPGeolocation/es-ipgeo-ingest-processor/blob/main/docs/usage-with-es.md) for detailed instructions on how to use this plugin with Elasticsearch, including example configurations and sample data.

### ES Usage Highlights

- **Creating Pipelines**: Learn how to create ingest pipelines that use the IPGeo processor to enrich incoming documents.
- **Field Configuration**: Understand the various fields and options available in the processor configuration.
- **Index Creation**: Create Elasticsearch indices with appropriate mappings to store enriched documents.
- **Document Ingestion**: Insert documents into your Elasticsearch index using the configured pipeline to see enrichment in action.

## Usage with Logstash

Check out [usage-with-logstash.md](https://github.com/IPGeolocation/es-ipgeo-ingest-processor/blob/main/docs/usage-with-logstash.md) for guidance on integrating this plugin with Logstash.

### Logstash Integration Overview

- **Configuration File Setup**: Create and configure Logstash pipeline files to read logs and enrich them using the IPGeo processor.
- **Real-Time Log Enrichment**: Set up Logstash to process and enrich real-time logs with geolocation, currency, security, and timezone data.
- **Indexing Logs in Elasticsearch**: Index the enriched logs into Elasticsearch for further analysis and visualization.

## Usage with Kibana

For using this plugin with Kibana, see [visualization-on-kibana.md](https://github.com/IPGeolocation/es-ipgeo-ingest-processor/blob/main/docs/visualization-on-kibana.md).

### Kibana Integration Overview

- **Data View Creation**: Set up data views in Kibana to recognize and utilize the enriched fields.
- **Map Visualization**: Create interactive maps in Kibana to visualize geospatial data.
- **Dashboard Setup**: Build comprehensive dashboards to display and analyze enriched data effectively.

## Additional Details

### Data Enrichment Capabilities

The IPGeo Ingest Processor leverages the powerful databases from ipgeolocation.io to provide extensive data enrichment capabilities. This includes:

- **Country and City Information**: Adds precise location details based on the IP address.
- **ISP and Organization Data**: Provides information about the internet service provider and organization associated with the IP address.
- **Security Threat Analysis**: Identifies potential security threats by checking if the IP address is known for malicious activities.
- **Customizable Fields**: Allows users to specify which fields to include or exclude from the enrichment process, providing flexibility based on specific use cases.

### Benefits of Using IPGeo Ingest Processor

- **Enhanced Analytics**: By enriching your documents with geolocation data, you can perform more detailed and meaningful analysis.
- **Improved Decision Making**: Visualizing geospatial data helps in making informed decisions based on the geographic distribution of your data.
- **Real-Time Insights**: Integrating with Logstash enables real-time log enrichment, allowing you to monitor and respond to events as they happen.
- **Comprehensive Visualization**: Using Kibana, you can create powerful visualizations and dashboards to track and analyze geospatial data effectively.

### Practical Use Cases

- **Network Security Monitoring**: Identify and respond to suspicious activities by analyzing the geographic origin of network traffic.
- **Sales and Marketing Analysis**: Understand the geographic distribution of your customers and tailor marketing strategies accordingly.
- **Logistics and Fleet Management**: Track the real-time location of vehicles and optimize routes for efficiency.
- **Public Health Monitoring**: Track the spread of diseases geographically and allocate resources effectively.

By following the detailed guides and leveraging the capabilities of the IPGeo Ingest Processor, you can significantly enhance your Elasticsearch, Logstash, and Kibana workflows with enriched geolocation data.
