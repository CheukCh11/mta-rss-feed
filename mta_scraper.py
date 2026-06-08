import os
import time
import requests
import re

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

# --- Custom Discord Emoji Mapping ---
emoji_map = {
    "1": "<:1_:1513370572329848923>",
    "2": "<:2_:1513370588133982279>",
    "3": "<:3_:1513370608992391258>",
    "4": "<:4_:1513370622611292171>",
    "4X": "<:4X:1513370636498636922>",
    "5": "<:5_:1513370649400447057>",
    "5X": "<:5X:1513370700839129250>",
    "6": "<:6_:1513370713858510988>",
    "6X": "<:6X:1513370727078695053>",
    "7": "<:7_:1513370757110169801>",
    "7X": "<:7X:1513370771836371014>",
    "A": "<:R40_A:1513367966597513349>",
    "B": "<:R40_B:1513367992405331979>",
    "C": "<:R40_C:1513368006279958759>",
    "D": "<:R40_D:1513368028065300590>",
    "E": "<:R40_E:1513368054438957056>",
    "F": "<:R40_F:1513368073174781972>",
    "FS": "<:SF:1513375190078193754>",
    "G": "<:R40_G:1513368105672249495>",
    "H": "<:R40_H:1513368122160054422>",
    "J": "<:R40_J:1513368138316775525>",
    "L": "<:R40_L:1513368154204799066>",
    "M": "<:R40_M:1513368176463843379>",
    "N": "<:R40_N:1513368198001590292>",
    "Q": "<:R40_Q:1513368214023700490>",
    "QX": "<:R40_QDiamond:1513368236224151685>",
    "R": "<:R40_R:1513368269409620148>",
    "GS": "<:R40_S:1513368289663778836>",
    "W": "<:R40_W:1513368397994266715>",
    "Z": "<:R40_Z:1513368415354617997>",
    "SIR": "<:SIR:1513371050941874389>"
}

def extract_best_text(translation_list, default_text="No details provided."):
    """Hunts for the HTML version of the MTA text first, falls back to standard english."""
    if not translation_list:
        return default_text
        
    best_text = None
    for t in translation_list:
        if t.get('language') == 'en-html':
            best_text = t.get('text')
            break
            
    if not best_text:
        for t in translation_list:
            if t.get('language') == 'en':
                best_text = t.get('text')
                break
                
    if not best_text:
        best_text = translation_list[0].get('text', default_text)
        
    return best_text

def format_html_to_discord(text):
    """Converts MTA HTML tags into Discord Markdown and scrubs all garbage HTML tags."""
    # Convert bolding
    text = text.replace("<b>", "**").replace("</b>", "**")
    text = text.replace("<strong>", "**").replace("</strong>", "**")
    
    # Convert italics
    text = text.replace("<i>", "*").replace("</i>", "*")
    text = text.replace("<em>", "*").replace("</em>", "*")
    
    # Convert HTML line breaks & paragraph ends into actual formatting
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = text.replace("</p>", "\n\n")
    text = text.replace("</div>", "\n")
    
    # Strip out ANY remaining raw HTML tags (like <p>, <span>)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up weird zero-width non-joiner bugs
    text = text.replace("\u200c", "").replace("\u200b", "").replace("â€Œ", "")
    
    return text.strip()

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
            
            header_translations = alert.get('header_text', {}).get('translation', [])
            title = extract_best_text(header_translations, "Subway Alert")
            title = format_html_to_discord(title)
            
            desc_translations = alert.get('description_text', {}).get('translation', [])
            description = extract_best_text(desc_translations, "No details provided.")
            description = format_html_to_discord(description)
            
            # Extract the official MTA Category
            mercury_alert = alert.get('transit_realtime.mercury_alert', alert.get('mercury_alert', {}))
            alert_type = mercury_alert.get('alert_type', 'Service Update')
            
            # Clean layout separation
            title = title.replace(" • ", "\n🔹 ")
            description = description.replace(" • ", "\n🔹 ")
            
            # Swap text icons for real emojis
            title = title.replace("[shuttle bus icon]", "🚌")
            description = description.replace("[shuttle bus icon]", "🚌")
            
            title = title.replace("[accessibility icon]", "♿")
            description = description.replace("[accessibility icon]", "♿")
            
            # Swap bracketed train lines for real emojis in the text
            for route, emoji_code in emoji_map.items():
                bracket_tag = f"[{route}]"
                title = title.replace(bracket_tag, emoji_code)
                description = description.replace(bracket_tag, emoji_code)
            
            description = description.replace("[]", "")
            
            # Dynamically change the card color and icon
            alert_type_lower = alert_type.lower()
            
            if "planned" in alert_type_lower or "reduced service" in alert_type_lower:
                card_color = 16750848 # Orange
                icon = "🚧"
            elif "suspended" in alert_type_lower:
                card_color = 16711680 # Red
                icon = "🛑"
            elif "delay" in alert_type_lower:
                card_color = 16711680 # Red
                icon = "⚠️"
            elif "extra service" in alert_type_lower:
                card_color = 3066993 # Green
                icon = "✨"
            elif "station notice" in alert_type_lower:
                card_color = 3447003 # Blue
                icon = "📢"
            else:
                card_color = 3447003 # Blue
                icon = "ℹ️"
            
            # Extract affected train lines for the title header
            informed_entities = alert.get('informed_entity', [])
            affected_routes = []
            
            for ie in informed_entities:
                route_id = ie.get('route_id')
                if route_id and route_id not in affected_routes:
                    affected_routes.append(route_id)
            
            route_tags = "".join([emoji_map.get(r, f"[{r}]") for r in affected_routes])
            
            final_title = f"{icon} | {alert_type}"
            if route_tags:
                final_title += f" {route_tags}"
            
            # --- FIX: Removed the outer asterisks around {title} to stop Markdown clashing ---
            payload = {
                "embeds": [{
                    "title": final_title,
                    "description": f"{title}\n\n{description}",
                    "color": card_color
                }]
            }
            
            requests.post(webhook_url, json=payload)
            print(f"Sent alert {alert_id} to Discord.")
            
    # Save the active IDs
    active_ids = [e.get('id') for e in current_entities if e.get('id')]
    with open(seen_file, "w") as f:
        f.write("\n".join(active_ids))
        
    print("Successfully updated tracking logs.")

except Exception as e:
    print(f"Error running pipeline: {e}")
