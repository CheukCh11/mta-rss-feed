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
            
        # Extract the main headline (Header Text)
        header_data = alert.get('header_text', {}).get('translation', [{}])[0]
        title = header_data.get('text', 'Subway Alert')
        
        # Extract the detailed explanation (Description Text)
        desc_data = alert.get('description_text', {}).get('translation', [{}])[0]
        description = desc_data.get('text', 'No details provided.')
        
        # NEW: Turn those annoying compressed dots into clean, new lines for Discord
        title = title.replace(" • ", "\n🔹 ")
        description = description.replace(" • ", "\n🔹 ")

        # Clean up text to prevent XML breaking errors
        title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        description = description.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        guid = entity.get('id', str(time.time()))
        
        # Build the RSS item block
        rss_items += f"""
        <item>
            <title>{title}</title>
            <description>{description}</description>
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
