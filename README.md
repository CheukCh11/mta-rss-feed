# mta-rss-feed | An MTA Old-School Service Alerter for Discord
An automated Python utility that fetches live NYC Subway alerts from the official MTA API and broadcasts them to a Discord channel via webhooks. 

Instead of plain text alerts, this bot dynamically generates a pixel-perfect replica of the classic, discontinued official MTA Service Alert graphics on the fly—complete with authentic typography and route bullets.

---

## The Features

* **Dynamic Graphics Engine:** Combines custom rollsign assets (`IRT`, `IND`, `Others`) and authentic Helvetica-Bold typography to build header banners on the fly.
* **Smart Text Scraper:** Outsmarts inconsistent API metadata by reading the human-written dispatcher logs to extract accurate schedule timeframes.
* **Native Discord Integration:** * Uses Discord's relative timestamps (`Posted 10 minutes ago`), which automatically adjust to every user's local timezone.
  * Translates inline MTA text flags (like `[A]` or `[shuttle bus icon]`) into custom server emojis and crisp Discord layout syntax.
* **Anti-Spam Filter:** Tracks active incidents using a local cache file to guarantee an alert is only posted once.

---

## 📂 Repository Structure

```text
├── .github/workflows/
│   └── update_feed.yml       # GitHub Actions cron runner (Basically joins a queue every 5 mins)
├── Rollsigns/
│   ├── IRT/                  # Numbered train line bullets (1-7)
│   ├── IND/                  # Lettered train line bullets (A-Z)
│   └── Others/               # SIR.png, mta_logo.png, and Helvetica-Bold.ttf
├── bullets/                  # This is unused.
├── mta_scraper.py            # Main processing & image rendering script
├── seen_alerts.txt           # Automatically generated log to track sent alerts
└── README.md
```
---

## 🛠️ Setup & Deployment
**1. Prerequisites**
* The script runs automatically via **GitHub Actions**, utilizing the following **Python** dependencies:
  * **requests** — For fetching API data and hitting Discord webhooks.
  * **pillow** — The image processing engine handling banner composition.

**2. GitHub Secrets Configuration**
* To protect your Discord channel from unauthorized access, the webhook URL is hidden as a repository secret.
  * Go to your GitHub Repository Settings -> Secrets and variables -> Actions.
  * Click New repository secret.
  * Name it exactly: DISCORD_WEBHOOK_URL
  * Paste your Discord Webhook URL into the value box and save.

---

## 📝 Disclaimer
*This is an unofficial, fan-made open-source transit utility. It is purely for hobby, historical preservation, and educational community tracking. It is not affiliated with, managed by, or endorsed by the **Metropolitan Transportation Authority (MTA)**.*
