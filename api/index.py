import os
import sys
import traceback
from flask import Flask, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot_core import check_and_notify

app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def run(path):
    expected = os.getenv("CRON_SECRET")
    if expected:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {expected}":
            return jsonify({"error": "unauthorized"}), 401

    try:
        check_and_notify()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
