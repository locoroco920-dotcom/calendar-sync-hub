import os
import subprocess
import threading
import time
import logging
from flask import Flask, send_file, jsonify
from flask_cors import CORS
from scraper import run_scraper
from create_ics import generate_ics_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, origins=[
    'https://locoroco920-dotcom.github.io',
    'http://localhost:5173',   # local dev
    'http://localhost:4173',   # local preview
])

# Lock to prevent concurrent scraper runs
_update_lock = threading.Lock()
_last_update = 0.0
# Minimum seconds between updates (5 minutes)
UPDATE_COOLDOWN = 300

# GitHub repo URL — set GITHUB_TOKEN env var on Render
GITHUB_REPO = os.environ.get(
    'GITHUB_REPO',
    'https://github.com/locoroco920-dotcom/calendar-sync-hub.git'
)


def _git_push():
    """Commit and push updated files to GitHub using a Personal Access Token."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        logging.warning("GITHUB_TOKEN not set — skipping git push.")
        return False

    repo_url = GITHUB_REPO.replace(
        'https://', f'https://x-access-token:{token}@'
    )

    try:
        subprocess.run(['git', 'config', 'user.email', 'bot@meadowlands-tracker.com'], check=True)
        subprocess.run(['git', 'config', 'user.name', 'Meadowlands Bot'], check=True)
        subprocess.run(['git', 'add', 'events.csv', 'public/events.ics'], check=True)
        result = subprocess.run(
            ['git', 'commit', '-m', f'Auto-update events: {time.strftime("%Y-%m-%d %H:%M")}'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            if 'nothing to commit' in result.stdout + result.stderr:
                logging.info("No changes to commit.")
                return True
            logging.error(f"Git commit failed: {result.stderr}")
            return False
        subprocess.run(['git', 'push', repo_url, 'main'], check=True,
                       capture_output=True, text=True)
        logging.info("Pushed updated events to GitHub.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Git push failed: {e}")
        return False


def _run_update():
    """Run the scraper pipeline: scrape → generate ICS → push to GitHub."""
    try:
        logging.info("Starting update pipeline...")
        # Clear old CSV so we get fresh data
        if os.path.exists("events.csv"):
            os.remove("events.csv")
        run_scraper()
        generate_ics_file("public/events.ics")
        _git_push()
        logging.info("Update pipeline complete.")
    except Exception as e:
        logging.error(f"Update pipeline failed: {e}")


@app.route('/api/update', methods=['POST'])
def trigger_update():
    """Trigger a background scraper run. Returns immediately.
    Respects a cooldown to avoid hammering source sites."""
    global _last_update

    now = time.time()
    if now - _last_update < UPDATE_COOLDOWN:
        remaining = int(UPDATE_COOLDOWN - (now - _last_update))
        return jsonify({
            "status": "skipped",
            "message": f"Last update was recent. Next update available in {remaining}s."
        }), 200

    if not _update_lock.acquire(blocking=False):
        return jsonify({
            "status": "in_progress",
            "message": "An update is already running."
        }), 200

    _last_update = now

    def run_and_release():
        try:
            _run_update()
        finally:
            _update_lock.release()

    thread = threading.Thread(target=run_and_release, daemon=True)
    thread.start()

    return jsonify({"status": "started", "message": "Update started."}), 202


@app.route('/api/events.ics', methods=['GET'])
def serve_ics():
    """Serve the current ICS file."""
    ics_path = os.path.join(os.path.dirname(__file__), 'public', 'events.ics')
    if os.path.exists(ics_path):
        return send_file(ics_path, mimetype='text/calendar')
    return jsonify({"error": "No events file yet."}), 404


@app.route('/api/health', methods=['GET'])
def health():
    """Health check."""
    has_ics = os.path.exists(os.path.join(os.path.dirname(__file__), 'public', 'events.ics'))
    return jsonify({
        "status": "ok",
        "has_events": has_ics,
        "last_update": _last_update if _last_update > 0 else None
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    # Run an initial update on startup so there's data available
    logging.info("Running initial scrape on startup...")
    _run_update()
    _last_update = time.time()
    app.run(host='0.0.0.0', port=port)
