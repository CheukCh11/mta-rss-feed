import os
import time
import requests
import re
import html
import io
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont

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

# --- Official MTA Route Color Configuration ---
ROUTE_COLORS = {
    "1": "#EE352E", "2": "#EE352E", "3": "#EE352E",
    "4": "#00933C", "5": "#00933C", "5X": "#00933C", "6": "#00933C", "6X": "#00933C",
    "7": "#B933AD", "7X": "#B933AD",
    "A": "#0039A6", "C": "#0039A6", "E": "#0039A6",
    "B": "#FF6319", "D": "#FF6319", "F": "#FF6319", "M": "#FF6319",
    "G": "#6CBE45",
    "J": "#996633", "Z": "#996633",
    "L": "#A7A9AC",
    "N": "#FCCC0A", "Q": "#FCCC0A", "R": "#FCCC0A", "W": "#FCCC0A",
    "S": "#808183", "SIR": "#1C355E"
}

# Custom Discord Emoji Mapping
emoji_map = {
    "1": "<:1_:1513370572329848923>", "2": "<:2_:1513370588133982279>", "3": "<:3_:1513370608992391258>",
    "4": "<:4_:1513370622611292171>", "4X": "<:4X:1513370636498636922>", "5": "<:5_:1513370649400447057>",
    "5X": "<:5X:1513370700839129250>", "6": "<:6_:1513370713858510988>", "6X": "<:6X:1513370727078695053>",
    "7": "<:7_:1513370757110169801>", "7X": "<:7X:1513370771836371014>",
    "A": "<:R40_A:1513367966597513349>", "B": "<:R40_B:1513367992405331979>", "C": "<:R40_C:1513368006279958759>",
    "D": "<:R40_D:1513368028065300590>", "E": "<:R40_E:1513368054438957056>", "F": "<:R40_F:1513368073174781972>",
    "FS": "<:SF:1513375190078193754>", "G": "<:R40_G:1513368105672249495>", "H": "<:R40_H:1513368122160054422>",
    "J": "<:R40_J:1513368138316775525>", "L": "<:R40_L:1513368154204799066>", "M": "<:R40_M:1513368176463843379>",
    "N": "<:R40_N:1513368198001590292>", "Q": "<:R40_Q:1513368214023700490>", "QX": "<:R40_QDiamond:1513368236224151685>",
    "R": "<:R40_R:1513368269409620148>", "S": "<:R40_S:1513368289663778836>", "W": "<:R40_W:1513368397994266715>",
    "Z": "<:R40_Z:1513368415354617997>", "SIR": "<:SIR:1513371050941874389>"
}

def generate_mta_banner(affected_routes):
    """Generates an image mimicking the classic official MTA Service Alert graphics."""
    width, height = 1200, 450
    img = Image.new("RGB", (width, height), color="#FFFFFF")
    draw = ImageDraw.Draw(img)
    
    # 1. Draw the Black Top Header Bar
    draw.rectangle([0, 0, width, 130], fill="#000000")
    
    # Attempt to load fonts (Standard paths on GitHub Linux runners)
    try:
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
        font_bullet = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 95)
    except IOError:
        font_header = font_bullet = ImageFont.load_default()

    # Draw Header Text
    draw.text((40, 35), "Service Alert", font=font_header, fill="#FFFFFF")
    
    # Draw right-aligned fallback "MTA" indicator text
    draw.text((width - 160, 35), "MTA", font=font_header, fill="#FFFFFF")
    
    # 2. Draw the Route Bullets centered in the white canvas area
    if not affected_routes:
        affected_routes = ["S"] # Fallback structural shape
        
    bullet_radius = 85
    bullet_diameter = bullet_radius * 2
    spacing = 40
    
    total_bullets_width = (len(affected_routes) * bullet_diameter) + ((len(affected_routes) - 1) * spacing)
    start_x = (width - total_bullets_width) // 2
    center_y = 290 
    
    for route in affected_routes:
        color_hex = ROUTE_COLORS.get(route, "#808183") # Fallback to grey if unknown
        text_color = "#000000" if route in ["N", "Q", "R", "W"] else "#FFFFFF"
        
        # Draw Circle boundary
        x0 = start_x
        y0 = center_y - bullet_radius
        x1 = start_x + bullet_diameter
        y1 = center_y + bullet_radius
        
        draw.ellipse([x0, y0, x1, y1], fill=color_hex)
        
        # Draw Route Character Center Text
        # Convert sub-variants like 6X or 7X to standard names for clean display inside bullets
        clean_route_text = route.replace("X", "")
        
        # Handle string bounding box setups safely across Pillow versions
        tw = draw.textlength(clean_route_text, font=font_bullet) if hasattr(draw, "textlength") else font_bullet.getsize(clean_route_text)[0]
        text_x = start_x + (bullet_diameter - tw) // 2
        text_y = center_y - (bullet_radius // 1.25)
        
        draw.text((text_x, text_y), clean_route_text, font=font_bullet, fill=text_color)
        start_x += bullet_diameter + spacing

    # Export out raw stream object
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def extract_best_text(translation_list, default_text="No details provided."):
    if not translation_list: return default_text
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
    return best_text if best_text else translation_list[0].get('text', default_text)

def format_html_to_discord(text):
    text = html.unescape(text).replace("\r\n", "\n")
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = text.replace("</p>", "\n\n").replace("</div>", "\n")
    text = text.replace("<b>", "**").replace("</b>", "**").replace("<strong>", "**").replace("</strong>", "**")
    
    date_pattern = r'\*\*\s*((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-zA-Z]*|Beginning|Starts|From|Until|Through|Every|All)[^*]+)\*\*'
    text = re.sub(date_pattern, r'\n\n-# *\1*', text)
    text = re.sub(r'([a-zA-Z0-9])\*\*(?=\w)', r'\1 **', text)
    
    text = text.replace("<i>", "*").replace("</i>", "*").replace("<em>", "*").replace("</em>", "*")
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace("\u200c", "").replace("\u200b", "").replace("â€Œ", "").replace("Â", "")
    return re.sub(r'\n{3,}', '\n\n', text).strip()

try:
    response = requests.get(url)
    data = response.json()
    current_entities = data.get('entity', [])
    
    for entity in current_entities:
        alert_id = entity.get('id')
        alert = entity.get('alert')
        if not alert or not alert_id:
            continue
            
        if alert_id not in seen_ids:
            header_translations = alert.get('header_text', {}).get('translation', [])
            title = format_html_to_discord(extract_best_text(header_translations, "Subway Alert"))
            
            desc_translations = alert.get('description_text', {}).get('translation', [])
            description = format_html_to_discord(extract_best_text(desc_translations, "No details provided."))
            
            mercury_alert = alert.get('transit_realtime.mercury_alert', alert.get('mercury_alert', {}))
            alert_type = mercury_alert.get('alert_type', 'Service Update')
            
            title = title.replace(" • ", "\n🔹 ").replace("[shuttle bus icon]", "🚌").replace("[accessibility icon]", "♿").replace("[airplane icon]", "✈️")
            description = description.replace(" • ", "\n🔹 ").replace("[shuttle bus icon]", "🚌").replace("[accessibility icon]", "♿").replace("[airplane icon]", "✈️")
            
            for route, emoji_code in emoji_map.items():
                title = title.replace(f"[{route}]", emoji_code)
                description = description.replace(f"[{route}]", emoji_code)
            description = description.replace("[]", "")
            
            alert_type_lower = alert_type.lower()
            if "planned" in alert_type_lower or "reduced service" in alert_type_lower:
                card_color, icon = 16750848, "🚧"
            elif "suspended" in alert_type_lower:
                card_color, icon = 16711680, "🛑"
            elif "delay" in alert_type_lower:
                card_color, icon = 16711680, "⚠️"
            elif "extra service" in alert_type_lower:
                card_color, icon = 3066993, "✨"
            else:
                card_color, icon = 3447003, "📢"
            
            informed_entities = alert.get('informed_entity', [])
            affected_routes = []
            for ie in informed_entities:
                route_id = ie.get('route_id')
                if route_id and route_id not in affected_routes:
                    affected_routes.append(route_id)
            
            route_tags = "".join([emoji_map.get(r, f"[{r}]") for r in affected_routes])
            final_title = f"{icon} | {alert_type}" + (f" {route_tags}" if route_tags else "")
            
            # Base embed parameters
            embed_data = {
                "title": final_title,
                "description": f"{title}\n\n{description}",
                "color": card_color,
                # --- Map out reference to our dynamic multipart file stream attachment ---
                "image": {
                    "url": "attachment://mta_banner.png"
                }
            }
            
            # Active Period Timeframes Extraction
            active_periods = alert.get('active_period', [])
            schedule_lines = []
            if active_periods and any(k in alert_type_lower for k in ["planned", "reduced", "suspended"]):
                for p in active_periods[:3]:
                    p_start, p_end = p.get('start'), p.get('end')
                    if p_start and p_end:
                        schedule_lines.append(f"• <t:{p_start}:f> to <t:{p_end}:f>")
                    elif p_start:
                        schedule_lines.append(f"• Starts <t:{p_start}:f>")
                if len(active_periods) > 3:
                    schedule_lines.append(f"*(+ {len(active_periods) - 3} more update windows)*")
                if schedule_lines:
                    embed_data["fields"] = [{"name": "📅 Scheduled Timeframe", "value": "\n".join(schedule_lines), "inline": False}]
            
            posted_timestamp = mercury_alert.get('updated_at', mercury_alert.get('created_at'))
            if posted_timestamp:
                try:
                    embed_data["timestamp"] = datetime.fromtimestamp(int(posted_timestamp), tz=timezone.utc).isoformat().replace("+00:00", "Z")
                    embed_data["footer"] = {"text": "MTA Official Post Time"}
                except: pass
            
            # --- Dynamic Image Engine Processing ---
            image_stream = generate_mta_banner(affected_routes)
            
            # Prepare Multipart-form data delivery structure
            import json
            payload = {"embeds": [embed_data]}
            
            files = {
                "payload_json": (None, json.dumps(payload), "application/json"),
                "file": ("mta_banner.png", image_stream, "image/png")
            }
            
            requests.post(webhook_url, files=files)
            print(f"Sent detailed graphical alert {alert_id} to Discord.")
            
    active_ids = [e.get('id') for e in current_entities if e.get('id')]
    with open(seen_file, "w") as f:
        f.write("\n".join(active_ids))
    print("Tracking logs successfully updated.")

except Exception as e:
    print(f"Error running pipeline: {e}")
