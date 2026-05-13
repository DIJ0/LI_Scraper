import os
import re
from config import OBSIDIAN_VAULT_PATH, OBSIDIAN_JOBS_FOLDER


def _safe_filename(text: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", text).strip()


def _note_path(job: dict) -> str:
    folder = os.path.join(OBSIDIAN_VAULT_PATH, OBSIDIAN_JOBS_FOLDER)
    os.makedirs(folder, exist_ok=True)
    name = _safe_filename(f"{job['company_name']} - {job['job_title']}.md")
    return os.path.join(folder, name)


def write_job_note(job: dict):
    path = _note_path(job)
    score = job.get("match_score", 0)
    cv_file = os.path.basename(job.get("cv_version") or "") or "_not generated_"

    content = f"""---
company: "{job.get('company_name', '')}"
title: "{job.get('job_title', '')}"
status: {job.get('status', 'Scraped')}
match_score: {score}
applied_date: "{job.get('applied_date', '')}"
location: "{job.get('location', '')}"
remote_type: "{job.get('remote_type', '')}"
salary: "{job.get('salary_range', '')}"
job_url: "{job.get('job_url', '')}"
cv_version: "{cv_file}"
tags: [job-application]
---

## Why it's a match
{job.get('match_notes') or '_No analysis yet_'}

## CV changes made
{job.get('cv_changes') or '_No changes recorded_'}

## Job description
{job.get('job_description', '')}

## My notes

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def update_note_status(job: dict):
    path = _note_path(job)
    if not os.path.exists(path):
        write_job_note(job)
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(
        r"^status: .*$", f"status: {job['status']}", content, flags=re.MULTILINE
    )
    if job.get("applied_date"):
        content = re.sub(
            r'^applied_date: ".*"$',
            f'applied_date: "{job["applied_date"]}"',
            content,
            flags=re.MULTILINE,
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
