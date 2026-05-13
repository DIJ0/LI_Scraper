import os
from datetime import datetime

from config import AUTO_APPLY_ENABLED, AUTO_APPLY_THRESHOLD, MIN_NOTIFY_SCORE, CV_REWRITE_THRESHOLD, QA_TITLE_KEYWORDS
from db import init_db, migrate_db, job_exists, insert_job, update_job, get_job_by_linkedin_id
from scraper import scrape_jobs
from cv_rewriter import score_job, rewrite_cv, generate_cover_letter
from bot import notify_new_job, notify_auto_applied, notify_run_summary, send_cover_letter
from obsidian_writer import write_job_note
from apply import easy_apply


def run():
    init_db()
    migrate_db()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{ts}] Starting scan  |  AUTO_APPLY_ENABLED={AUTO_APPLY_ENABLED}")

    raw_jobs = scrape_jobs()
    print(f"Scraped {len(raw_jobs)} jobs total\n")

    new_count      = 0
    auto_applied   = 0
    for_review     = 0

    # ── Persist all new jobs to DB first, before any CV analysis ─────────────
    for job in raw_jobs:
        if not job_exists(job["job_id"]):
            insert_job({**job, "status": "Scraped"})

    # ── Now process each new job ───────────────────────────────────────────────
    for job in raw_jobs:
        db_job = get_job_by_linkedin_id(job["job_id"])
        if db_job and db_job.get("match_score") is not None:
            continue  # already processed in a previous run

        new_count += 1
        title_lower = job["job_title"].lower()
        is_qa_role  = any(kw in title_lower for kw in QA_TITLE_KEYWORDS)

        if not is_qa_role:
            print(f"-- {job['job_title']} @ {job['company_name']}  [title filtered]")
            continue

        print(f">> {job['job_title']} @ {job['company_name']}")

        db_id = get_job_by_linkedin_id(job["job_id"])["id"]
        job["id"] = db_id

        # ── Step 1: score only (cheap) ────────────────────────────────────────
        try:
            scored = score_job(job)
            job["match_score"] = scored["match_score"]
            job["match_notes"] = scored["match_notes"]
            print(f"  Match score: {job['match_score']}%")
        except Exception as e:
            print(f"  Scoring failed: {e}")
            job.setdefault("match_score", 0)
            job.setdefault("match_notes", "")

        update_job(db_id, {
            "match_score": job["match_score"],
            "match_notes": job["match_notes"],
        })

        # ── Step 2: rewrite CV only if score is good enough ───────────────────
        if job["match_score"] >= CV_REWRITE_THRESHOLD:
            try:
                rewritten = rewrite_cv(job)
                job["cv_changes"] = rewritten["cv_changes"]
                job["cv_version"] = rewritten["cv_path"]
                update_job(db_id, {
                    "cv_changes": job["cv_changes"],
                    "cv_version": job["cv_version"],
                })
                print(f"  CV rewritten -> {os.path.basename(job['cv_version'])}")
            except Exception as e:
                print(f"  CV rewrite failed: {e}")
        else:
            print(f"  Score {job['match_score']}% < {CV_REWRITE_THRESHOLD}% -- skipping CV rewrite")

        # ── Obsidian note ──────────────────────────────────────────────────────
        try:
            write_job_note(job)
        except Exception as e:
            print(f"  Obsidian write failed: {e}")

        score    = job.get("match_score", 0)
        cv_path  = job.get("cv_version", "")

        # ── Apply or review ────────────────────────────────────────────────────
        if score < MIN_NOTIFY_SCORE:
            print(f"  Score {score}% < {MIN_NOTIFY_SCORE}% minimum -- skipping notification")
            continue

        # ── Generate cover letter only for jobs that also get a CV rewrite ──────
        cover_letter = ""
        if score >= CV_REWRITE_THRESHOLD:
            try:
                cover_letter = generate_cover_letter(job)
                update_job(db_id, {"cover_letter": cover_letter})
                print(f"  Cover letter generated")
            except Exception as e:
                print(f"  Cover letter failed: {e}")

        if AUTO_APPLY_ENABLED and score >= AUTO_APPLY_THRESHOLD:
            print(f"  Score {score}% >= threshold -- auto-applying")
            applied = easy_apply(job["job_url"])
            if applied:
                update_job(db_id, {
                    "status":       "Applied",
                    "applied_date": datetime.now().isoformat(),
                    "apply_method": "EasyApply",
                })
                notify_auto_applied(job)
                auto_applied += 1
            else:
                notify_new_job(job, cv_path)
                if cover_letter:
                    send_cover_letter(job, cover_letter)
                for_review += 1
        else:
            print(f"  Score {score}% -- sending for review")
            notify_new_job(job, cv_path)
            if cover_letter:
                send_cover_letter(job, cover_letter)
            for_review += 1

    notify_run_summary(len(raw_jobs), new_count, auto_applied, for_review)
    print(f"\nDone — new: {new_count}  auto-applied: {auto_applied}  review: {for_review}")


if __name__ == "__main__":
    run()
