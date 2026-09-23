"""
WelfareAI - Multilingual Welfare-Entitlement Screening Assistant
Flask Web Application
"""

import os
import json
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify
)
from logic.eligibility_engine import EligibilityEngine, load_json_file
from database.db import log_screening_event, get_screening_stats, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "welfareai-hackathon-demo-key-2026")

# Initialize database and eligibility engine
init_db()
engine = EligibilityEngine()

KERALA_DISTRICTS = [
    "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod",
    "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad",
    "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"
]


@app.context_processor
def inject_global_data():
    lang = session.get("lang", "en")
    terms = engine.terminology
    # Helper translation accessor
    def t(key, default=""):
        entry = terms.get(key, {})
        return entry.get(lang, entry.get("en", default or key))

    return {
        "lang": lang,
        "t": t,
        "districts": KERALA_DISTRICTS
    }


@app.route("/")
def index():
    demo_profiles = load_json_file("household_profiles.json")
    stats = get_screening_stats()
    return render_template(
        "index.html",
        demo_profiles=demo_profiles,
        stats=stats
    )


@app.route("/set-language/<lang>")
def set_language(lang):
    if lang in ("en", "ml"):
        session["lang"] = lang
    next_url = request.args.get("next") or request.referrer or url_for("index")
    # Ensure next_url is a relative internal path to prevent open redirects
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("index")
    return redirect(next_url)


@app.route("/screening")
def screening():
    try:
        step = int(request.args.get("step", 1))
    except (ValueError, TypeError):
        step = 1
    if step < 1 or step > 4:
        step = 1

    profile_id = request.args.get("profile")

    # If demo profile requested, preload it into session
    if profile_id:
        profiles = load_json_file("household_profiles.json")
        matched = next((p for p in profiles if p["id"] == profile_id), None)
        if matched:
            session["household"] = dict(matched["data"])
            session["demo_profile_id"] = profile_id

    household = session.get("household", {})
    return render_template("screening.html", step=step, household=household)


@app.route("/save-step", methods=["POST"])
def save_step():
    """Saves partial step data and moves to next step or review."""
    household = session.get("household", {})
    if not isinstance(household, dict):
        household = {}

    # Capture any submitted form fields
    for field in ["occupation", "annual_income", "age", "family_size", "gender", "district", "has_disability"]:
        if field in request.form:
            val = request.form.get(field)
            if val is not None and str(val).strip() != "":
                household[field] = str(val).strip()
            else:
                household[field] = None

    session["household"] = household
    session.modified = True
    next_action = request.form.get("action", "next")
    try:
        current_step = int(request.form.get("current_step", 1))
    except (ValueError, TypeError):
        current_step = 1

    if next_action == "back":
        prev_step = max(1, current_step - 1)
        return redirect(url_for("screening", step=prev_step))
    elif next_action == "review" or current_step >= 4:
        return redirect(url_for("review"))
    else:
        return redirect(url_for("screening", step=current_step + 1))


@app.route("/review")
def review():
    household = session.get("household", {})
    if not household:
        return redirect(url_for("screening", step=1))
    return render_template("review.html", household=household)


@app.route("/screen", methods=["POST"])
def screen():
    """Form submission endpoint to run screening."""
    household = session.get("household", {})
    lang = session.get("lang", "en")

    # Run engine to count and log audit event
    results = engine.screen_household(household, lang=lang)

    # Log anonymous audit event
    log_screening_event(
        occupation=household.get("occupation"),
        district=household.get("district"),
        eligible_count=results["summary"]["eligible_count"],
        more_info_count=results["summary"]["more_info_count"],
        language=lang
    )

    return redirect(url_for("results"))


@app.route("/results")
def results():
    household = session.get("household", {})
    if not household:
        return redirect(url_for("screening", step=1))

    lang = session.get("lang", "en")
    results_data = engine.screen_household(household, lang=lang)

    return render_template("results.html", results=results_data, household=household)


@app.route("/reset")
def reset():
    session.pop("household", None)
    session.pop("demo_profile_id", None)
    return redirect(url_for("index"))


# JSON API ENDPOINTS FOR CLIENT JS AND TESTS

@app.route("/api/screen", methods=["POST"])
def api_screen():
    data = request.get_json(force=True) or {}
    lang = data.get("lang") or session.get("lang", "en")
    results = engine.screen_household(data, lang=lang)
    return jsonify(results)


@app.route("/api/demo-households")
def api_demo_households():
    profiles = load_json_file("household_profiles.json")
    return jsonify(profiles)


@app.route("/api/akshaya")
def api_akshaya():
    district = request.args.get("district", "Ernakulam")
    lang = session.get("lang", "en")
    centres = engine.get_akshaya_for_district(district, lang=lang)
    return jsonify(centres)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("index.html", error="The requested page was not found."), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("index.html", error="An internal error occurred. Please try again."), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    try:
        app.run(host="127.0.0.1", port=port, debug=True)
    except OSError as e:
        if port == 5000 and "Address already in use" in str(e):
            print(f"\n[!] Port 5000 is occupied (e.g. macOS AirPlay Receiver). Launching on http://127.0.0.1:5001 instead...\n")
            app.run(host="127.0.0.1", port=5001, debug=True)
        else:
            raise
