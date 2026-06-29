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
    "A": "<:A_:1519910953469083718>", "B": "<:B_:1519910970082852987>", "C": "<:C_:1519910988927733810>",
    "D": "<:D_:1519911006229364839>", "E": "<:E_:1519911024516661278>", "F": "<:F_:1519911041193218099>", "FX": "<:FX:1519911066480545952>",
    "FS": "<:SF:1513375190078193754>", "G": "<:G_:1519911086223130654>", "GS": "<:S_:1519911303584546927>", "H": "<:H_:1519911108872507544>",
    "J": "<:J_:1519911154980487178>", "L": "<:L_:1519911184973824180>", "M": "<:M_:1519911204892704828>",
    "N": "<:N_:1519911225205456996>", "Q": "<:Q_:1519911242871865454>", "QX": "<:QX:1519911260085424258>",
    "R": "<:R_:1519911278573781092>", "S": "<:S_:1519911303584546927>", "W": "<:W_:1519911331736588368>",
    "Z": "<:Z_:1519911351340765315>", "SIR": "<:SIR:1513371050941874389>", "SI": "<:SIR:1513371050941874389>",
}

# --- Custom Image File Mapping ---
bullet_image_map = {
    "1": "IRT/1.png", "2": "IRT/2.png", "3": "IRT/3.png", "4": "IRT/4.png", "4X": "IRT/4X.png",
    "5": "IRT/5.png", "5X": "IRT/5X.png", "6": "IRT/6.png", "6X": "IRT/6X.png", "7": "IRT/7.png", "7X": "IRT/7X.png",
    "A": "IND/A.png", "B": "IND/B.png", "C": "IND/C.png", "D": "IND/D.png", "E": "IND/E.png",
    "F": "IND/F.png", "FX": "IND/FX.png", "FS": "IND/SF.png", "G": "IND/G.png", "GS": "IND/S.png",    
    "H": "IND/H.png", "J": "IND/J.png", "L": "IND/L.png", "M": "IND/M.png", "N": "IND/N.png",
    "Q": "IND/Q.png", "QX": "IND/QX.png", "R": "IND/R.png", "S": "IND/S.png", "W": "IND/W.png", "Z": "IND/Z.png",
    "SIR": "Others/SIR.png", "SI": "Others/SIR.png",
}

def generate_mta_banner(affected_routes, banner_text="Service Alert"):
    """Generates an image mimicking the classic MTA graphics using custom assets and dynamic text."""
    width, height = 1200, 450
    img = Image.new("RGB", (width, height), color="#FFFFFF")
    draw = ImageDraw.Draw(img)
    
    # 1. Draw the Black Top Header Bar
    draw.rectangle([0, 0, width, 130], fill="#000000")
    
    # Load NYCTA Standard font / Helvetica from the Others folder
    custom_font_path = "Rollsigns/Others/Helvetica-Bold.otf" 
    try:
        if os.path.exists(custom_font_path):
            font_header = ImageFont.truetype(custom_font_path, 75)
        else:
            font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
    except IOError:
        font_header = ImageFont.load_default()

    draw.text((40, 25), banner_text, font=font_header, fill="#FFFFFF")
    
    # --- Draw the right-aligned MTA Logo ---
    try:
        mta_logo = Image.open("Rollsigns/Others/mta_logo (1).png").convert("RGBA")
        target_height = 85
        aspect_ratio = mta_logo.width / mta_logo.height
        target_width = int(target_height * aspect_ratio)
        mta_logo = mta_logo.resize((target_width, target_height), Image.Resampling.LANCZOS)
        logo_x = width - target_width - 40
        logo_y = (130 - target_height) // 2
        img.paste(mta_logo, (logo_x, logo_y), mta_logo)
    except IOError:
        draw.text((width - 160, 25), "MTA", font=font_header, fill="#FFFFFF")
    
    # 2. Draw the Route Bullets
    if not affected_routes:
        affected_routes = ["S"] 
        
    bullet_size = 200
    spacing = 40
    
    total_bullets_width = (len(affected_routes) * bullet_size) + ((len(affected_routes) - 1) * spacing)
    start_x = (width - total_bullets_width) // 2
    center_y = 290 
    start_y = center_y - (bullet_size // 2)
    
    for route in affected_routes:
        filename = bullet_image_map.get(route, f"Others/{route}.png")
        bullet_path = f"Rollsigns/{filename}"
        
        if os.path.exists(bullet_path):
            custom_bullet = Image.open(bullet_path).convert("RGBA")
            custom_bullet = custom_bullet.resize((bullet_size, bullet_size), Image.Resampling.LANCZOS)
            img.paste(custom_bullet, (start_x, start_y), custom_bullet)
            
        else:
            color_hex = ROUTE_COLORS.get(route, "#808183")
            text_color = "#000000" if route in ["N", "Q", "R", "W"] else "#FFFFFF"
            
            draw.ellipse([start_x, start_y, start_x + bullet_size, start_y + bullet_size], fill=color_hex)
            clean_route_text = route.replace("X", "")
            
            try:
                if os.path.exists(custom_font_path):
                    font_bullet = ImageFont.truetype(custom_font_path, 115)
                else:
                    font_bullet = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 115)
            except IOError:
                font_bullet = ImageFont.load_default()
                
            tw = draw.textlength(clean_route_text, font=font_bullet) if hasattr(draw, "textlength") else font_bullet.getsize(clean_route_text)[0]
            text_x = start_x + (bullet_size - tw) // 2
            text_y = center_y - (bullet_size // 2.5)
            draw.text((text_x, int(text_y)), clean_route_text, font=font_bullet, fill=text_color)

        start_x += bullet_size + spacing

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
    text = text.replace("<i>", "*").replace("</i>", "*").replace("<em>", "*").replace("</em>", "*")
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace("\u200c", "").replace("\u200b", "").replace("â€Œ", "").replace("Â", "")
    return re.sub(r'\n{3,}', '\n\n', text).strip()

try:
    response = requests.get(url)
    data = response.json()
    current_entities = data.get('entity', [])
    
    new_alerts_processed = 0
    
    for entity in current_entities:
        alert_id = entity.get('id')
        alert = entity.get('alert')
        if not alert or not alert_id:
            continue
            
        if alert_id not in seen_ids:
            new_alerts_processed += 1
            header_translations = alert.get('header_text', {}).get('translation', [])
            title = format_html_to_discord(extract_best_text(header_translations, "Subway Alert"))
            
            desc_translations = alert.get('description_text', {}).get('translation', [])
            raw_desc_text = extract_best_text(desc_translations, "No details provided.")
            description = format_html_to_discord(raw_desc_text)
            
            mercury_alert = alert.get('transit_realtime.mercury_alert', alert.get('mercury_alert', {}))
            alert_type = mercury_alert.get('alert_type', 'Service Update')
            
            description = description.replace(" • ", "\n🔹 ")
            description = description.replace("[shuttle bus icon]", "🚌").replace("[accessibility icon]", "♿").replace("[airplane icon]", "✈️")
            title = title.replace(" • ", "\n🔹 ").replace("[shuttle bus icon]", "🚌").replace("[accessibility icon]", "♿").replace("[airplane icon]", "✈️")
            
            # --- Date Scrubber ---
            raw_lines = description.split('\n')
            filtered_desc_lines = []
            extracted_text_dates = []
            
            date_keywords = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", 
                             "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "AM", "PM", "Beginning", "Starts", "Until"]
            
            for line in raw_lines:
                has_number = any(char.isdigit() for char in line)
                is_schedule_line = '**' in line and has_number and any(k in line for k in date_keywords)
                
                if is_schedule_line:
                    clean_date = line.replace('🔹', '').replace('**', '').replace('-#', '').replace('*', '').strip()
                    if clean_date and clean_date not in extracted_text_dates and len(clean_date) > 8:
                        extracted_text_dates.append(f"• {clean_date}")
                else:
                    filtered_desc_lines.append(line)
                    
            description = '\n'.join(filtered_desc_lines).strip()

            for route, emoji_code in emoji_map.items():
                title = title.replace(f"[{route}]", emoji_code)
                description = description.replace(f"[{route}]", emoji_code)
            description = description.replace("[]", "")
            
            alert_type_lower = alert_type.lower()
            
            if "planned" in alert_type_lower or "reduced" in alert_type_lower or "change" in alert_type_lower:
                card_color, icon = 16750848, "🚧"
                banner_text = "Service Change" 
            elif "suspended" in alert_type_lower:
                card_color, icon = 16711680, "🛑"
                banner_text = "Service Suspended"
            elif "delay" in alert_type_lower:
                card_color, icon = 16711680, "⚠️"
                banner_text = "Service Alert"
            elif "extra" in alert_type_lower or "special" in alert_type_lower:
                card_color, icon = 3066993, "✨"
                banner_text = "Special Service"
            else:
                card_color, icon = 3447003, "📢"
                banner_text = "Service Alert"
                
            informed_entities = alert.get('informed_entity', [])
            affected_routes = []
            for ie in informed_entities:
                route_id = ie.get('route_id')
                if route_id and route_id not in affected_routes:
                    affected_routes.append(route_id)
            
            route_tags = "".join([emoji_map.get(r, f"[{r}]") for r in affected_routes])
            final_title = f"{icon} | {alert_type}" + (f" {route_tags}" if route_tags else "")
            
            embed_data = {
                "title": final_title,
                "description": f"{title}\n\n{description}",
                "color": card_color,
                "image": {
                    "url": "attachment://mta_banner.png"
                }
            }
            
            active_periods = alert.get('active_period', [])
            schedule_lines = []
            is_planned_work = any(k in alert_type_lower for k in ["planned", "reduced", "suspended", "change"])
            
            if is_planned_work:
                has_valid_metadata = active_periods and any(p.get('start') and p.get('end') for p in active_periods)
                
                if has_valid_metadata:
                    for p in active_periods[:15]:
                        p_start, p_end = p.get('start'), p.get('end')
                        if p_start and p_end:
                            schedule_lines.append(f"• <t:{p_start}:f> to <t:{p_end}:f>")
                        elif p_start:
                            schedule_lines.append(f"• Starts <t:{p_start}:f>")
                else:
                    schedule_lines = extracted_text_dates
                
                if schedule_lines:
                    embed_data["fields"] = [{"name": "📅 Scheduled Timeframes", "value": "\n".join(schedule_lines[:15]), "inline": False}]
            
            posted_timestamp = mercury_alert.get('updated_at', mercury_alert.get('created_at'))
            if posted_timestamp:
                try:
                    embed_data["timestamp"] = datetime.fromtimestamp(int(posted_timestamp), tz=timezone.utc).isoformat().replace("+00:00", "Z")
                    embed_data["footer"] = {"text": "MTA Official Post Time"}
                    embed_data["description"] += f"\n\n-# 🕒 Posted <t:{posted_timestamp}:R>"
                except: pass
            
            image_stream = generate_mta_banner(affected_routes, banner_text)
            
            payload = {"embeds": [embed_data]}
            files = {
                "payload_json": (None, json.dumps(payload), "application/json"),
                "file": ("mta_banner.png", image_stream, "image/png")
            }
            
            requests.post(webhook_url, files=files)
            print(f"Sent detailed graphical alert {alert_id} to Discord.")
            
    # --- NEW: "All Clear" Status Heartbeat Logic ---
    # If the endpoint checked everything and found nothing new to report, send a clean heartbeat.
    if new_alerts_processed == 0:
        current_unix = int(time.time())
        status_embed = {
            "title": "✅ Live Feed Connected",
            "description": f"Ms. Silly has searched around and concluded that there are **no new alerts available**. hooray!!! :3\n\n-# 🔄 Last verified: <t:{current_unix}:f> (<t:{current_unix}:R>)",
            "color": 3066993  # Clean green line
        }
        requests.post(webhook_url, json={"embeds": [status_embed]})
        print("No new updates found. Transmitted all-clear status signal to Discord.")

    active_ids = [e.get('id') for e in current_entities if e.get('id')]
    with open(seen_file, "w") as f:
        f.write("\n".join(active_ids))
    print("Tracking logs successfully updated.")

except Exception as e:
    print(f"Error running pipeline: {e}")
