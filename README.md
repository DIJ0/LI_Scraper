# LIhelper — LinkedIn Job Hunt Automation

Automated LinkedIn job scraper, CV tailor, and application tracker. Runs on a schedule, scores every job with Claude AI, rewrites your CV summary and skills section for the best matches, and sends Telegram notifications with the tailored CV and a ready-to-paste cover letter.

---

## Features

- **Scheduled scraping** — Runs via Windows Task Scheduler (e.g. 4×/day). Searches LinkedIn by job title, location, date posted, experience level, and job function.
- **Title pre-filter** — Skips Claude API calls entirely for jobs that clearly don't match (saves cost).
- **Claude AI scoring** — Scores each job 0–100% by comparing the job description to your CV. Includes a short analysis of why it matched or didn't.
- **CV tailoring** — For jobs scoring ≥ 60%, rewrites only the **Summary** and **Core Skills** sections of your DOCX CV. Professional Experience and all other sections are never touched.
- **Cover letter generation** — Produces a concise 3-paragraph cover letter tailored to the company for every job that gets a CV rewrite.
- **Telegram notifications** — Sends job details, the tailored CV as a file attachment, and the cover letter text for easy copy-pasting.
- **Auto-apply** — Optional LinkedIn Easy Apply automation for jobs scoring ≥ 85% (disabled by default).
- **Web dashboard** — Local Flask app with three views:
  - **Kanban** — Drag cards between statuses (Scraped → Applied → Interview → Offer → Rejected)
  - **Table** — Sortable list of all jobs
  - **Stats** — Score distribution chart and status summary
- **Job detail page** — Match score + Claude analysis, tailored CV download, cover letter with one-click copy, recruiter info, follow-up date, and personal notes.
- **Obsidian integration** — Writes a markdown note per job to your vault with frontmatter, match analysis, and job description.
- **Score color coding** — Green ≥ 80%, Yellow ≥ 60%, Red < 60%.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Scraping | Playwright (Chromium, headless=False, random delays) |
| AI | Anthropic Claude API (`claude-sonnet-4-6`) |
| CV editing | python-docx (modifies sections in-place) |
| Database | SQLite |
| Dashboard | Flask + Bootstrap 5 + Chart.js + SortableJS |
| Notifications | Telegram Bot API |
| Scheduling | Windows Task Scheduler |
| Notes | Obsidian markdown vault |

---

## Project Structure

```
LIhelper/
├── main.py              # Entry point — scrape + score + notify
├── reprocess.py         # Re-score existing DB jobs without scraping
├── scraper.py           # Playwright LinkedIn scraper
├── cv_rewriter.py       # Claude CV tailoring + cover letter generation
├── bot.py               # Telegram notifications
├── db.py                # SQLite helpers
├── obsidian_writer.py   # Obsidian markdown notes
├── apply.py             # LinkedIn Easy Apply automation
├── config.py            # All settings (credentials via .env)
├── requirements.txt
├── .env.example         # Credential template — copy to .env and fill in
├── dashboard/
│   ├── app.py           # Flask app
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html   # Kanban + Table + Stats
│   │   └── job.html     # Job detail page
│   └── static/css/
│       └── style.css
├── cvs/                 # Place your base CV here (DOCX format)
│   └── generated/       # Auto-generated tailored CVs (git-ignored)
└── data/                # SQLite DB + LinkedIn cookies (git-ignored)
```

---

## Setup

### Prerequisites

- Python 3.11+
- A [Telegram bot](https://core.telegram.org/bots#botfather) and your chat ID
- An [Anthropic API key](https://console.anthropic.com/)
- LinkedIn account
- [Obsidian](https://obsidian.md/) (optional)

### Install

```bash
git clone https://github.com/DIJ0/LI_Scraper.git
cd LI_Scraper
pip install -r requirements.txt
playwright install chromium
```

### Configure credentials

```bash
cp .env.example .env
```

Edit `.env` with your real values:

```
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ANTHROPIC_API_KEY=your_anthropic_key
```

To get your Telegram chat ID: send `/start` to your bot, then call `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy the `chat.id` value.

### Configure search & thresholds

Edit `config.py`:

| Setting | Default | Description |
|---|---|---|
| `LOCATION_NAME` | `"Kfar Saba, Israel"` | LinkedIn location |
| `LOCATION_DISTANCE_MILES` | `50` | Search radius (~79 km) |
| `SEARCH_REMOTE` | `True` | Include remote jobs |
| `DATE_POSTED_FILTER` | `"r86400"` | Last 24 h (`r604800` = week) |
| `EXPERIENCE_LEVELS` | `"3,4"` | Associate + Mid-Senior |
| `JOB_TITLES` | QA/testing roles | List of titles to search |
| `QA_TITLE_KEYWORDS` | QA/test keywords | Title pre-filter list |
| `CV_REWRITE_THRESHOLD` | `60` | Min score to tailor CV + write cover letter |
| `MIN_NOTIFY_SCORE` | `60` | Min score to send Telegram alert |
| `AUTO_APPLY_ENABLED` | `False` | Enable Easy Apply automation |
| `AUTO_APPLY_THRESHOLD` | `85` | Min score to auto-apply |
| `OBSIDIAN_VAULT_PATH` | *(set your path)* | Obsidian vault directory |
| `LINKEDIN_URL` | *(set your URL)* | Your LinkedIn profile URL (used in CV header) |

### Add your CV

Place your CV in DOCX format at:

```
cvs/Dima_Eidler_CV.docx
```

Or update `BASE_CV_PATH` in `config.py` to point to your file. The tool modifies only the **Summary** and **Core Skills** sections — everything else is preserved exactly as-is.

---

## Running

```bash
# Run a full scrape + score + notify cycle
python main.py

# Re-score all existing DB jobs without scraping LinkedIn again
python reprocess.py

# Start the web dashboard (http://127.0.0.1:5000)
python dashboard/app.py
```

### Schedule with Windows Task Scheduler

Create a Basic Task that runs:

- **Program:** `python`
- **Arguments:** `C:\path\to\LIhelper\main.py`
- **Start in:** `C:\path\to\LIhelper`

Suggested trigger times: 08:00, 11:00, 15:00, 17:00.

---

## Important Notes

- **LinkedIn ToS:** Automated scraping may violate LinkedIn's terms of service. Use responsibly and at your own risk.
- **API cost:** With title pre-filtering and score gating, typical usage is roughly $5–10/month at 4 runs/day.
- **Auto-apply is off by default:** Test the scoring thoroughly before enabling `AUTO_APPLY_ENABLED`.
- **CV safety:** Only the Summary and Core Skills sections are ever modified. The tailoring runs on a fresh copy of your base CV each time.

---

## License

MIT
