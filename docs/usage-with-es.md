If you need to install the IPGeolocation Ingest Processor plugin, please refer to [installation.md](docs/installation.md) for detailed instructions on how to install the plugin.

If you have already completed the installation and the plugin is installed, please go through this guide to understand how to use the processor with ES to enrich your documents with different types of data.

### Creating a Pipeline with the 'ipgeo' Processor

The IPGeo Ingest Processor comes with the following options:

| Field            | Required | Description                                                                                                                                           |
|------------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| `field`          | Yes      | Represents the field in which the IP address will be present in the document.                                                                           |
| `database_version` | Yes      | Represents the version of the database being used. IPGeolocation offers seven databases starting from DB-I to DB-VII. Details can be found [here](https://ipgeolocation.io/db-pricing.html). |
| `target_field`   | No       | The field that will hold the geographical information looked up from the IPGeolocation database. Default is `ipgeo`.                                   |
| `ignore_missing` | No       | If true and the field does not exist, the processor exits quietly without modifying the document. Default is `false`.                                  |
| `language`       | No       | IPGeolocation database supports different language translations. The default is `en` (English).                                                        |
| `fields`         | No       | Used to specify which fields to include while querying the database.                                                                                   |
| `excludes`       | No       | Used to specify which fields to exclude while querying the database.                                                                                   |
| `include`        | No       | Used to specify additional data to include in the response. Details on these fields can be found in the [API documentation](https://ipgeolocation.io/documentation/ip-geolocation-api.html). |

### Creating a Simple Pipeline

Let's create a simple pipeline with the default fields, including `timezone` and `security`:

```sh
curl -X PUT "http://localhost:9200/_ingest/pipeline/ipgeo_test_pipeline" -H 'Content-Type: application/json' -d'
{
  "description": "Pipeline to enrich logs with IP geo information",
  "processors": [
    {
      "ipgeo": {
        "field": "ip",
        "database_version": "DB-VI",
        "ignore_missing": true,
        "include": "security,timezone"
      }
    }
  ]
}
'
```

> **Note**: Security information will only be included if the purchased database version supports it.

### Creating an Index

If the pipeline creation passes without an error, proceed with creating an index:

```sh
curl -H 'Content-Type: application/json' -XPUT 'http://localhost:9200/ipgeo_test_index' -d '
{
  "mappings": {
    "properties": {
      "ipgeo": {
        "properties": {
          "location": {
            "type": "geo_point"
          }
        }
      }
    }
  }
}'
```

The `location` field will be a JSON object containing latitude and longitude. We specify its type as `geo_point` to enable visualization in Kibana. It is not mandatory to declare it unless you plan to visualize the data.

### Inserting a Document

Once the index is created without errors, insert a document into the index using the pipeline to enrich it with geolocation, timezone, currency, and security data:

```sh
curl -X POST "http://localhost:9200/ipgeo_test_index/_doc?pipeline=ipgeo_test_pipeline" -H "Content-Type: application/json" -d '{
  "identifier": "github", 
  "service": "test", 
  "os": "linux", 
  "ip": "192.30.253.113"
}'
```

### Retrieving a Document

Retrieve the document using the following command:

```sh
curl -XGET 'http://localhost:9200/ipgeo_test_index/_search?q=identifier:github&pretty'
```

Example response:

```json
{
  "took": 9,
  "timed_out": false,
  "_shards": {
    "total": 1,
    "successful": 1,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 6,
      "relation": "eq"
    },
    "max_score": 0.074107975,
    "hits": [
      {
        "_index": "ipgeo_test_index",
        "_id": "Krllho8B3cYCrrQIERag",
        "_score": 0.074107975,
        "_source": {
          "identifier": "github",
          "os": "linux",
          "service": "test",
          "ipgeo": {
            "continent_name": "North America",
            "country_tld": ".us",
            "calling_code": "+1",
            "languages": "en-US,es-US,haw,fr",
            "city": "San Francisco",
            "continent_code": "NA",
            "time_zone": {
              "offset": -7.0,
              "dst_savings": 1000,
              "name": "America/Los_Angeles",
              "current_time_unix": 1715946721,
              "current_time": "2024-05-17 04:52:01.693-0700",
              "is_dst": true
            },
            "geoname_id": "5326621",
            "zipcode": "94107-2008",
            "security": {
              "is_cloud_provider": false,
              "is_spam": false,
              "is_known_attacker": false,
              "is_anonymous": false,
              "is_tor": false,
              "is_bot": false,
              "threat_score": 0,
              "is_proxy": false,
              "proxy_type": ""
            },
            "district": "",
            "country_code2": "US",
            "country_name": "United States",
            "is_eu": false,
            "country_code3": "USA",
            "state_prov": "California",
            "currency": {
              "symbol": "$",
              "code": "USD",
              "name": "US Dollar"
            },
            "location": {
              "lon": -122.39117,
              "lat": 37.78229
            },
            "country_capital": "Washington, D.C.",
            "country_flag": "https://ipgeolocation.io/static/flags/us_64.png"
          },
          "ip": "192.30.253.113"
        }
      }
    ]
  }
}
```

And that's it! You have a fully enriched document with geolocation, timezone, security, and currency data in your Elasticsearch index, which can be visualized in Kibana as well. To further read on how the results after indexing can be visualized on Kibana. For more information, please refer to our [visualization-on-kibana.md](docs/visualization-on-kibana.md).
