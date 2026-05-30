import requests
import json
import time

# The official MTA real-time JSON feed you found
url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts.json"

# Note: If the MTA blocks the request with a 403 error, you just need to register 
# a free key at api.mta.info and add it here: {"x-api-key": "YOUR_KEY"}
headers = {}

try:
    response = requests.get(url, headers=headers)
    data = response.json()
    
    rss_items = ""
    
    # Loop through all current active service alerts
    for entity in data.get('entity', []):
        alert = entity.get('alert')
        if not alert:
            continue
            
        # Extract the main headline
        header_data = alert.get('header_text', {}).get('translation', [{}])[0]
        title = header_data.get('text', 'Subway Alert')
        
        # Extract the detailed explanation
        desc_data = alert.get('description_text', {}).get('translation', [{}])[0]
        description = desc_data.get('text', 'No details provided.')
        
        # Turn MTA's dots into actual line breaks
        title = title.replace(" • ", "\n🔹 ")
        description = description.replace(" • ", "\n🔹 ")

        # Note: We completely deleted the old lines that were breaking the XML!
        
        guid = entity.get('id', str(time.time()))
        
        # Build the RSS item block using CDATA tags to perfectly preserve the formatting
        rss_items += f"""
        <item>
            <title><![CDATA[{title}]]></title>
            <description><![CDATA[{description}]]></description>
            <guid isPermaLink="false">{guid}</guid>
        </item>"""
        
    # Wrap everything in standard RSS XML framing
    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>MTA Subway Live Alerts</title>
    <link>https://www.mta.info</link>
    <description>Live real-time service alerts for the NYC Subway system</description>
    <language>en-us</language>
    {rss_items}
</channel>
</rss>"""
    
    # Save it to a file
    with open("mta_subway_alerts.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed)
        
    print("Success! Generated fresh mta_subway_alerts.xml feed.")

except Exception as e:
    print(f"Error parsing data: {e}")
