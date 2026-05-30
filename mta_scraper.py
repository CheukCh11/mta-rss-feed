import os
import time
import requests

# MTA Endpoint
url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts.json"

# Pull the secret webhook link from GitHub settings
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

if not webhook_url:
    print("Error: DISCORD_WEBHOOK_URL is missing!")
    exit(1)

# File to track alerts we have already posted so we don't spam the server
seen_file = "seen_alerts.txt"
if os.path.exists(seen_file):
    with open(seen_file, "r") as f:
        seen_ids = set(f.read().splitlines())
else:
    seen_ids = set()

try:
    response = requests.get(url)
    data = response.json()
    
    current_entities = data.get('entity', [])
    
    for entity in current_entities:
        alert_id = entity.get('id')
        alert = entity.get('alert')
        if not alert or not alert_id:
            continue
            
        # If this is a brand-new alert, process and send it
        if alert_id not in seen_ids:
            header_data = alert.get('header_text', {}).get('translation', [{}])[0]
            title = header_data.get('text', 'Subway Alert')
            
            desc_data = alert.get('description_text', {}).get('translation', [{}])[0]
            description = desc_data.get('text', 'No details provided.')
            
            # Perfect layout separation using clean lines
            title = title.replace(" • ", "\n🔹 ")
            description = description.replace(" • ", "\n🔹 ")
            
            # Construct the Discord layout card payload
            payload = {
                "embeds": [{
                    "title": "🚨 MTA Subway Alert",
                    "description": f"**{title}**\n\n{description}",
                    "color": 16750848 # Subway Orange
                }]
            }
            
            # Fire it directly to your Discord channel instantly
            requests.post(webhook_url, json=payload)
            print(f"Sent alert {alert_id} to Discord.")
            
    # Save the current list of active IDs so we remember them next time
    active_ids = [e.get('id') for e in current_entities if e.get('id')]
    with open(seen_file, "w") as f:
        f.write("\n".join(active_ids))
        
    print("Successfully updated tracking logs.")

except Exception as e:
    print(f"Error running pipeline: {e}")
