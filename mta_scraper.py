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
            
            # --- NEW: Extract the official MTA Category ---
            # GTFS parsers sometimes format extension keys differently, so we check both common paths
            mercury_alert = alert.get('transit_realtime.mercury_alert', alert.get('mercury_alert', {}))
            alert_type = mercury_alert.get('alert_type', 'Service Update')
            
            # Perfect layout separation using clean lines
            title = title.replace(" • ", "\n🔹 ")
            description = description.replace(" • ", "\n🔹 ")
            
            # --- NEW: Swap text icons for real emojis ---
            title = title.replace("[shuttle bus icon]", "🚌")
            description = description.replace("[shuttle bus icon]", "🚌")
            
            title = title.replace("[accessibility icon]", "♿")
            description = description.replace("[accessibility icon]", "♿")
            
            # (Optional) Clean up empty brackets if the MTA leaves any behind
            description = description.replace("[]", "")
            
            # --- Dynamically change the card color and icon based on precise categories ---
            alert_type_lower = alert_type.lower()
            
            # 1. Catch ALL planned/scheduled work first so sub-text doesn't trigger emergency colors
            if "planned" in alert_type_lower or "reduced service" in alert_type_lower:
                card_color = 16750848 # Orange for scheduled changes/construction
                icon = "🚧"
                
            # 2. Catch unexpected emergency disruptions next
            elif "suspended" in alert_type_lower:
                card_color = 16711680 # Red for sudden line shutdowns
                icon = "🛑"
            elif "delay" in alert_type_lower:
                card_color = 16711680 # Red for active delays
                icon = "⚠️"
                
            # 3. Catch positive service adjustments (Good news!)
            elif "extra service" in alert_type_lower:
                card_color = 3066993 # Green for bonus trains
                icon = "✨"
                
            # 4. Catch general station announcements and informational notices
            elif "station notice" in alert_type_lower:
                card_color = 3447003 # Blue for general station info
                icon = "📢"
                
            # 5. Fallback default if the MTA invents a new category later
            else:
                card_color = 3447003 # Blue
                icon = "ℹ️"
            
           # --- NEW: Extract the affected train lines ---
            informed_entities = alert.get('informed_entity', [])
            affected_routes = []
            
            for ie in informed_entities:
                route_id = ie.get('route_id')
                # Grab valid route IDs and avoid duplicates (MTA data can be repetitive)
                if route_id and route_id not in affected_routes:
                    affected_routes.append(route_id)
            
            # Format the extracted lines into a [N][R] string
            route_tags = "".join([f"[{r}]" for r in affected_routes])
            
            # Build the final title string. If there are routes, append them.
            final_title = f"{icon} | {alert_type}"
            if route_tags:
                final_title += f" {route_tags}"
            
            # Construct the Discord layout card payload
            payload = {
                "embeds": [{
                    "title": final_title,
                    "description": f"**{title}**\n\n{description}",
                    "color": card_color
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
