"""
Reprocess all scraped jobs:
- Re-score with Claude
- Rewrite CV (Summary + Core Skills only)
- Generate cover letter
- Update DB + Obsidian notes
Does NOT re-scrape LinkedIn.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from config import CV_REWRITE_THRESHOLD
from db import init_db, migrate_db, get_all_jobs, update_job
from cv_rewriter import score_job, rewrite_cv, generate_cover_letter
from obsidian_writer import write_job_note


def run():
    init_db()
    migrate_db()

    jobs = get_all_jobs()
    print(f"Reprocessing {len(jobs)} jobs...\n")

    for job in jobs:
        print(f">> {job['job_title']} @ {job['company_name']}")

        # Score
        try:
            scored = score_job(job)
            job["match_score"] = scored["match_score"]
            job["match_notes"] = scored["match_notes"]
            auto_status = "Archived" if job["match_score"] < 40 else job.get("status", "Scraped")
            update_job(job["id"], {
                "match_score": job["match_score"],
                "match_notes": job["match_notes"],
                "status":      auto_status,
            })
            print(f"   Score: {job['match_score']}%")
        except Exception as e:
            print(f"   Score failed: {e}")
            continue

        if job["match_score"] < 40:
            continue

        # CV rewrite (only if score good enough)
        if job["match_score"] >= 60:
            try:
                rewritten = rewrite_cv(job)
                job["cv_version"] = rewritten["cv_path"]
                job["cv_changes"] = rewritten["cv_changes"]
                update_job(job["id"], {
                    "cv_version": job["cv_version"],
                    "cv_changes": job["cv_changes"],
                })
                print(f"   CV rewritten")
            except Exception as e:
                print(f"   CV rewrite failed: {e}")

        # Cover letter (only for jobs that also get a CV rewrite)
        if job["match_score"] >= CV_REWRITE_THRESHOLD:
            try:
                cover = generate_cover_letter(job)
                job["cover_letter"] = cover
                update_job(job["id"], {"cover_letter": cover})
                print(f"   Cover letter generated")
            except Exception as e:
                print(f"   Cover letter failed: {e}")

        # Obsidian note
        try:
            write_job_note(job)
        except Exception as e:
            print(f"   Obsidian failed: {e}")

        print()

    print("Done. Refresh the dashboard.")


if __name__ == "__main__":
    run()
