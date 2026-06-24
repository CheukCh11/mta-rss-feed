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
