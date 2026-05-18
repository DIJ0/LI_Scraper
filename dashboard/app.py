import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, jsonify, request, send_file
from db import get_all_jobs, get_job, update_job, get_stats
from obsidian_writer import update_note_status
from config import GENERATED_CVS_DIR, DASHBOARD_HOST, DASHBOARD_PORT

app = Flask(__name__)

STATUSES = ["Scraped", "Applied", "Phone Screen", "Interview", "Offer", "Rejected", "Ghosted", "Archived"]


@app.route("/")
def index():
    return render_template("index.html", statuses=STATUSES)


@app.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = get_job(job_id)
    if not job:
        return "Not found", 404
    return render_template("job.html", job=job, statuses=STATUSES)


# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/jobs")
def api_jobs():
    return jsonify(get_all_jobs())


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


@app.route("/api/jobs/<int:job_id>", methods=["GET"])
def api_job(job_id):
    job = get_job(job_id)
    return (jsonify(job) if job else (jsonify({"error": "Not found"}), 404))


@app.route("/api/jobs/<int:job_id>/status", methods=["POST"])
def api_update_status(job_id):
    new_status = request.json.get("status")
    if new_status not in STATUSES:
        return jsonify({"error": "Invalid status"}), 400
    update_job(job_id, {"status": new_status})
    try:
        update_note_status(get_job(job_id))
    except Exception:
        pass
    return jsonify({"ok": True})


@app.route("/api/jobs/<int:job_id>/notes", methods=["POST"])
def api_update_notes(job_id):
    data = request.json or {}
    update_job(job_id, {
        "notes":              data.get("notes", ""),
        "recruiter_name":     data.get("recruiter_name", ""),
        "recruiter_contact":  data.get("recruiter_contact", ""),
        "next_followup_date": data.get("next_followup_date", ""),
    })
    return jsonify({"ok": True})


@app.route("/cv/<path:filename>")
def serve_cv(filename):
    return send_file(os.path.join(GENERATED_CVS_DIR, filename))


if __name__ == "__main__":
    app.run(debug=True, host=DASHBOARD_HOST, port=DASHBOARD_PORT)
