import sqlite3
from datetime import datetime
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def migrate_db():
    """Add new columns to existing DB without breaking existing data."""
    with get_conn() as conn:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
        new_cols = {
            "cover_letter": "TEXT",
        }
        for col, col_type in new_cols.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE jobs ADD COLUMN {col} {col_type}")
        conn.commit()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Job info
                job_id              TEXT UNIQUE,
                company_name        TEXT,
                job_title           TEXT,
                job_url             TEXT,
                job_description     TEXT,
                location            TEXT,
                remote_type         TEXT,
                salary_range        TEXT,

                -- Claude analysis
                match_score         INTEGER,
                match_notes         TEXT,

                -- Application
                cv_version          TEXT,
                cv_changes          TEXT,
                applied_date        TEXT,
                apply_method        TEXT,

                -- Status
                status              TEXT DEFAULT 'Scraped',

                -- Follow-up
                recruiter_name      TEXT,
                recruiter_contact   TEXT,
                last_followup_date  TEXT,
                next_followup_date  TEXT,

                -- Notes
                notes               TEXT,
                cover_letter        TEXT,

                -- Metadata
                scraped_date        TEXT,
                updated_date        TEXT
            )
        """)
        conn.commit()


def job_exists(job_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        return row is not None


def insert_job(job: dict) -> int:
    now = datetime.now().isoformat()
    job = {**job, "scraped_date": now, "updated_date": now}
    cols = ", ".join(job.keys())
    placeholders = ", ".join("?" * len(job))
    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT OR IGNORE INTO jobs ({cols}) VALUES ({placeholders})",
            list(job.values()),
        )
        conn.commit()
        return cur.lastrowid


def update_job(job_id: int, fields: dict):
    fields = {**fields, "updated_date": datetime.now().isoformat()}
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    with get_conn() as conn:
        conn.execute(
            f"UPDATE jobs SET {set_clause} WHERE id = ?",
            [*fields.values(), job_id],
        )
        conn.commit()


def get_all_jobs() -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY scraped_date DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_job_by_linkedin_id(linkedin_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (linkedin_id,)
        ).fetchone()
        return dict(row) if row else None


def get_job(job_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        return dict(row) if row else None


def get_stats() -> dict:
    with get_conn() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'Applied'"
        ).fetchone()[0]
        by_status = conn.execute(
            "SELECT status, COUNT(*) as count FROM jobs GROUP BY status"
        ).fetchall()
        return {
            "total_applied": total,
            "by_status": {r["status"]: r["count"] for r in by_status},
        }
