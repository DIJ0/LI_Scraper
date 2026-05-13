import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def _url(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"


def send_message(text: str):
    requests.post(_url("sendMessage"), json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }, timeout=10)


def send_document(file_path: str, caption: str = ""):
    with open(file_path, "rb") as f:
        requests.post(_url("sendDocument"), data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML",
        }, files={"document": f}, timeout=30)


def notify_new_job(job: dict, cv_path: str = ""):
    score = job.get("match_score", 0)
    score_bar = "🟢" if score >= 85 else ("🟡" if score >= 65 else "🔴")
    msg = (
        f"{score_bar} <b>New Job Match — {score}%</b>\n\n"
        f"<b>{job['job_title']}</b> @ {job['company_name']}\n"
        f"📍 {job.get('location', 'N/A')}  |  {job.get('remote_type', '')}\n"
        f"💰 {job.get('salary_range') or 'Salary not listed'}\n\n"
        f"<i>{job.get('match_notes', '')}</i>\n\n"
        f"🔗 <a href=\"{job['job_url']}\">View on LinkedIn</a>"
    )
    send_message(msg)
    if cv_path:
        try:
            send_document(cv_path, caption=f"Tailored CV — {job['company_name']}")
        except Exception as e:
            send_message(f"⚠️ Could not attach CV: {e}")


def send_cover_letter(job: dict, cover_letter: str):
    msg = (
        f"📝 <b>Cover Letter — {job['job_title']} @ {job['company_name']}</b>\n\n"
        f"{cover_letter}"
    )
    send_message(msg)


def notify_auto_applied(job: dict):
    send_message(
        f"✅ <b>Auto-Applied</b>\n\n"
        f"<b>{job['job_title']}</b> @ {job['company_name']}\n"
        f"🎯 Match score: {job.get('match_score', '?')}%\n"
        f"🔗 <a href=\"{job['job_url']}\">View on LinkedIn</a>"
    )


def notify_run_summary(total_scraped: int, new_jobs: int, auto_applied: int, for_review: int):
    send_message(
        f"🔄 <b>Scan complete</b>\n\n"
        f"Jobs scraped:     {total_scraped}\n"
        f"New matches:      {new_jobs}\n"
        f"Auto-applied:     {auto_applied}\n"
        f"Sent for review:  {for_review}"
    )
