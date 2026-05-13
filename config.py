import os
from dotenv import load_dotenv

load_dotenv()  # reads credentials from .env — never commit that file

# ── LinkedIn credentials ──────────────────────────────────────────────────────
LINKEDIN_EMAIL    = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# ── Job search criteria ───────────────────────────────────────────────────────
JOB_TITLES = [
    "Senior QA Engineer",
    "QA Engineer",
    "QA Tech Lead",
]
LOCATION_NAME           = "Kfar Saba, Israel"
LOCATION_DISTANCE_MILES = 50          # ~79 km
SEARCH_REMOTE           = True
DATE_POSTED_FILTER      = "r86400"    # r86400=24h | r604800=week | r2592000=month

# LinkedIn search filters (tighten to reduce noise)
# Experience level: 2=Entry 3=Associate 4=Mid-Senior 5=Director
EXPERIENCE_LEVELS       = "3,4"       # Associate + Mid-Senior
# Job type: F=Full-time C=Contract P=Part-time
JOB_TYPES               = "F,P"         # Full-time and Part-time
# Job function: it=Information Technology
JOB_FUNCTION            = "it"        # IT jobs only

# ── Title pre-filter (skip Claude entirely if title doesn't match) ────────────
# Job must contain at least one of these keywords (case-insensitive)
QA_TITLE_KEYWORDS = [
    "qa", "quality assurance", "quality engineer", "quality lead",
    "test", "tester", "testing", "sdet", "automation engineer",
    "qc", "quality control",
]

# ── Apply settings ────────────────────────────────────────────────────────────
AUTO_APPLY_ENABLED   = False          # ← set True when ready to auto-apply
AUTO_APPLY_THRESHOLD = 85             # auto-apply only if match score >= this
MIN_NOTIFY_SCORE     = 50             # skip Telegram notification below this score
CV_REWRITE_THRESHOLD = 60             # rewrite CV only if match score >= this

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

# ── Claude / Anthropic ────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL      = "claude-sonnet-4-6"

# ── Personal / CV ────────────────────────────────────────────────────────────
LINKEDIN_URL = "linkedin.com/in/dimaeidler"

# ── Obsidian ──────────────────────────────────────────────────────────────────
OBSIDIAN_VAULT_PATH  = r"C:\Users\graph\bot\vault"
OBSIDIAN_JOBS_FOLDER = "Job Applications"

# ── File paths ────────────────────────────────────────────────────────────────
BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
BASE_CV_PATH      = os.path.join(BASE_DIR, "cvs", "Dima_Eidler_CV.docx")
GENERATED_CVS_DIR = os.path.join(BASE_DIR, "cvs", "generated")
DB_PATH           = os.path.join(BASE_DIR, "data", "jobs.db")
COOKIES_PATH      = os.path.join(BASE_DIR, "data", "linkedin_cookies.json")

# ── Dashboard ─────────────────────────────────────────────────────────────────
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 5000
