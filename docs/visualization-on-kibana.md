If you need to install the IPGeolocation Ingest Processor plugin, please refer to [installation.md](installation.md) for detailed instructions on how to install the plugin.

If you have already completed the installation and the plugin is installed, please go through this guide to understand how to visualize the Elasticsearch index containing simple or log documents enriched with geolocation, timezone, currency, and security data on Kibana map. Please refer to [usage-with-es.md](usage-with-es.md) or [usage-with-logstash.md](usage-with-logstash.md) first to learn how to use the IPGeolocation IPGeo Ingest Processor plugin. If you have already gone through these guides, it means you have an index with enriched documents in your Elasticsearch.

### Visualizing Geolocation Data on Kibana Map

1. **Access Kibana Dashboard**

   Open your web browser and navigate to the Kibana dashboard using the following URL: 

   ```
   http://<YOUR_SERVER_IP>:5601
   ```

   Replace `<YOUR_SERVER_IP>` with the actual IP address of your server.

2. **Create Data View**

   - From the sidebar, navigate to **Management > Stack Management**.
   - In the sidebar, go to **Kibana > Data Views**.
   - Click on **Create New Data View**.
   - In the form, provide a name for your data view.
   - In the **Index pattern** field, specify the name of the index where your geolocation enriched documents are indexed.
   - Click on **Save Data View** to save it in Kibana.

3. **Create a New Visualization**

   - From the sidebar of the dashboard, go to **Analytics > Visualize Library**.
   - Click on **Create New Visualization**.
   - Select **Maps** from the available options.

4. **Add Layer to the Map**

   - A map will open, and on the side, there will be an option to **Add Layer**. Click on it.
   - From the dropdown, select the data view that you created previously.
   - Once selected, if you used `geo_point` as the type for the location field during index mapping, you will see the visualization of the data on the map.

### Explanation and Additional Details

- **Management > Stack Management**: This section allows you to manage various aspects of the Elastic Stack, including Kibana settings, Elasticsearch indices, and more.
- **Kibana > Data Views**: Data views (formerly known as index patterns) allow Kibana to understand and interpret the data stored in your Elasticsearch indices.
- **Create New Data View**: This step is crucial as it lets Kibana know which indices to query for your data visualizations.
- **Analytics > Visualize Library**: This section contains all your saved visualizations and offers tools to create new ones.
- **Maps**: The Maps visualization in Kibana lets you create interactive maps to visualize geospatial data.

### Adding and Customizing Layers

- **Add Layer**: This feature allows you to add different data sources to your map visualization.
- **Select Data View**: Ensure you select the data view that corresponds to your geolocation enriched index.
- **Geo_point**: If your mapping for the `location` field is set to `geo_point`, Kibana will be able to plot your data points on the map accurately.

Once you have added the layer and selected the correct data view, Kibana will display the geolocation data on the map. You can further customize the visualization by adjusting the layer settings, adding filters, and applying different styling options to enhance the presentation of your data.

Here’s a screenshot of what your map visualization might look like:

![Kibana Map Visualization](/images/kibana-visualization.png)

### Advantages and Use Cases of Data Visualization with Geolocation Data on Kibana Maps

#### Advantages

1. **Enhanced Data Understanding**:
   - Visualizing data on a map provides an intuitive way to understand geographic patterns and trends. It makes it easier to identify clusters, outliers, and spatial relationships that might be missed in traditional tabular data.
   
2. **Improved Decision Making**:
   - By seeing where events are happening, organizations can make more informed decisions. For example, a company can identify regions with high sales or areas that need more resources based on customer activity.
   
3. **Real-Time Monitoring**:
   - Kibana Maps can be used to monitor real-time data. For instance, a logistics company can track the location of its vehicles in real-time, helping them to optimize routes and improve delivery times.
   
4. **Enhanced Security Analysis**:
   - Security teams can use geolocation data to monitor and analyze the origins of network traffic, helping them identify potential threats based on geographic patterns.
   
5. **Better Customer Insights**:
   - Businesses can gain valuable insights into customer behavior by analyzing the geographic distribution of their users. This can help in targeted marketing and improving customer service.
   
6. **Resource Optimization**:
   - By understanding the geographic distribution of resources, organizations can optimize their deployment. For example, a utility company can visualize the locations of their assets and plan maintenance schedules more efficiently.

#### Use Cases

1. **Network Security Monitoring**:
   - Security teams can use geolocation data to identify and respond to suspicious activity based on the geographic origin of traffic. By visualizing IP addresses on a map, they can quickly see if there are any unusual patterns, such as traffic from unexpected countries or regions known for cyber attacks.

2. **Logistics and Fleet Management**:
   - Logistics companies can track their fleet of vehicles in real-time. By visualizing vehicle locations on a map, they can optimize routes, reduce fuel consumption, and improve delivery times. Real-time tracking also helps in ensuring the safety of the drivers and the cargo.

3. **Sales and Marketing Analysis**:
   - Businesses can analyze sales data geographically to identify high-performing regions and potential markets. This information can guide marketing strategies and sales efforts. For example, a company can visualize customer purchases to see which areas generate the most revenue.

4. **Customer Service Optimization**:
   - Customer service teams can use geolocation data to provide better support. By knowing the geographic distribution of their customers, they can tailor their services to meet regional demands and provide localized support.

5. **Public Health Monitoring**:
   - Health organizations can track the spread of diseases geographically. By visualizing case data on a map, they can identify hotspots and allocate resources more effectively. This approach was widely used during the COVID-19 pandemic to monitor and respond to outbreaks.

6. **Urban Planning and Development**:
   - City planners and developers can use geolocation data to understand population distribution and plan infrastructure projects accordingly. For example, they can visualize the locations of public facilities and identify areas that need additional services.

7. **Environmental Monitoring**:
   - Environmental agencies can track pollution levels, weather patterns, and natural disasters geographically. By visualizing environmental data on a map, they can respond more effectively to environmental challenges and plan mitigation strategies.

8. **Retail Store Analysis**:
   - Retail chains can use geolocation data to analyze the performance of different store locations. By visualizing sales data on a map, they can identify underperforming stores and decide whether to invest in marketing or close down certain locations.

9. **Travel and Tourism Insights**:
   - Travel companies can analyze geolocation data to understand tourist behavior. By visualizing where tourists are coming from and where they are going, companies can tailor their services and marketing campaigns to attract more visitors.

10. **Emergency Response Coordination**:
    - Emergency services can use geolocation data to coordinate their response efforts. By visualizing the locations of incidents and available resources, they can dispatch emergency personnel more effectively and save lives.

### Conclusion

Data visualization using geolocation data on Kibana Maps provides significant advantages by turning raw data into actionable insights. Whether for security monitoring, logistics management, sales analysis, or public health tracking, visualizing geospatial data helps organizations make better decisions, optimize resources, and enhance their overall operations. By leveraging the power of Kibana Maps, users can gain a deeper understanding of their data and respond more effectively to the challenges and opportunities they face.