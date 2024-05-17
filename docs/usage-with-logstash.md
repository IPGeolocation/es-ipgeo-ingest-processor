If you need to install the IPGeolocation Ingest Processor plugin, please refer to [installation.md](installation.md) for detailed instructions on how to install the plugin.

If you have already completed the installation and the plugin is installed, please go through this guide to understand how to use the processor with Logstash for real-time logs enrichment and indexing.

In this guide, `/usr/share/logstash/bin/logstash` refers to the Logstash executable, which is used to run Logstash with specific configuration files. The `nginx_logstash.conf` file refers to a custom configuration file used for enriching logs with the IPGeo processor.

### Creating the Logstash Configuration File

First, let's create the `nginx_logstash.conf` file. You can name this file anything with a `.conf` extension. In this example, we are using `nginx_logstash.conf` because we will be enriching the documents of an Nginx logs file (`access.log`).

Create a file in `/usr/share/logstash/bin/logstash` named `nginx_logstash.conf` with the following content:

```plaintext
input {
  file {
    path => "/home/elk-plugin/access.log.1"
    start_position => "beginning"
    sincedb_path => "/dev/null"
  }
}

filter {
  grok {
    match => {
      "message" => "%{IPORHOST:ip}"
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "nginx_access_logs"
    pipeline => "ipgeo_pipeline"
  }
}
```

### Explanation of the Configuration File

- **Input Section**:
  - `file`: This plugin reads logs from a specified file.
    - `path`: Specifies the path to the log file. Replace `/home/elk-plugin/access.log.1` with the path to your log file.
    - `start_position`: Set to `beginning` to start reading the log file from the beginning.
    - `sincedb_path`: Set to `/dev/null` to disable the sincedb feature, which keeps track of the current position in the file. This ensures that the file is read from the beginning each time Logstash is started.

- **Filter Section**:
  - `grok`: This plugin parses unstructured log data into structured data.
    - `match`: Specifies the pattern to match in the log messages. In this example, `%{IPORHOST:ip}` extracts the IP address from the log message and stores it in the `ip` field.

- **Output Section**:
  - `elasticsearch`: This plugin outputs the logs to Elasticsearch.
    - `hosts`: Specifies the Elasticsearch hosts. Here, it is set to `localhost:9200`.
    - `index`: Specifies the name of the Elasticsearch index where the logs will be stored. In this example, it is `nginx_access_logs`.
    - `pipeline`: Specifies the name of the ingest pipeline in Elasticsearch that will process the logs. In this example, it is `ipgeo_pipeline`.

### Setting Up Elasticsearch

Replace `/home/elk-plugin/access.log.1` with the path to your logs file. You can use different grok patterns if you are using different log files. For more information, refer to the official documentation: [Logstash Grok Filter Plugin](https://www.elastic.co/guide/en/logstash/current/plugins-filters-grok.html). Save the configuration file.

Next, create the index mentioned in the configuration file. You can name this index anything, but ensure to update the configuration file accordingly. Create a pipeline with the IPGeo processor. For further help on how to create an index and pipeline with the IPGeo processor, please refer to [usage-with-es.md](usage-with-es.md). Make sure to declare the correct field key for the IP address as specified in your configuration file. In this example, we are using `"message" => "%{IPORHOST:ip}"`, so the IP will be extracted and should be declared as `"field": "ip"` in the IPGeo processor. If you want to visualize the enriched logs in Kibana later, make sure to declare the type of the location field as `geo_point` in the mapping. Details are already available in the [usage-with-es.md](usage-with-es.md) file.

### Running Logstash

Once both the index and pipeline are created, verify they are working by adding and retrieving a document. Details are available in the [usage-with-es.md](usage-with-es.md) file. After everything is set up, restart your Logstash. If you are using a system service to run Logstash, use the following command:

```sh
sudo systemctl restart logstash.service
```

Otherwise, you can start it directly using:

```sh
sudo /usr/share/logstash/bin/logstash -f nginx_logstash.conf
```

Pass the name of your configuration file in the `-f` argument. Once done, Logstash will start enriching and indexing the logs into your Elasticsearch index. To verify that logs are being indexed, use the following command:

```sh
curl -X GET "localhost:9200/nginx_access_logs/_count"
```

As the log file updates, Logstash will continue to enrich and index the logs into your Elasticsearch index. You can use this index for real-time data visualization in Kibana. For more information, please refer to our [visualization-on-kibana.md](visualization-on-kibana.md).