"""All page routes."""
import logging
import os
import sqlite3
import uuid

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, send_file, url_for)
from werkzeug.utils import secure_filename

from . import ALLOWED_EXTENSIONS, CATEGORIES, database as db
from .hashing import sha256_file

bp = Blueprint("main", __name__)
log = logging.getLogger(__name__)


def evidence_path(stored_filename):
    """Absolute path of a stored file, guaranteed to sit directly in the evidence dir."""
    base = os.path.realpath(current_app.config["EVIDENCE_DIR"])
    path = os.path.realpath(os.path.join(base, stored_filename))
    if os.path.dirname(path) != base:
        return None
    return path


def _remove_quietly(path):
    try:
        os.remove(path)
    except OSError:
        pass


@bp.route("/")
def dashboard():
    return render_template(
        "dashboard.html",
        total=db.count_evidence(),
        checks=db.count_verifications(),
        recent=db.recent_evidence(5),
    )


@bp.route("/evidence")
def records():
    query = request.args.get("q", "").strip()
    return render_template("evidence_records.html",
                           records=db.list_evidence(query), query=query)


def _collect_form(errors=None, status=200):
    return render_template("collect.html", errors=errors or [],
                           form=request.form, max_mb=20), status


@bp.route("/collect", methods=["GET", "POST"])
def collect():
    if request.method == "GET":
        return _collect_form()

    name = request.form.get("evidence_name", "").strip()
    category = request.form.get("evidence_category", "")
    collected_by = request.form.get("collected_by", "").strip()
    description = request.form.get("description", "").strip()
    upload = request.files.get("evidence_file")

    errors = []
    original = ""
    extension = ""
    if upload is None or not upload.filename:
        errors.append("Choose an evidence file to upload.")
    else:
        original = secure_filename(upload.filename)
        extension = os.path.splitext(original)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            errors.append("File type not supported. Allowed types: %s." %
                          ", ".join(sorted(ALLOWED_EXTENSIONS)))
    if not name:
        errors.append("Enter an evidence name.")
    elif len(name) > 200:
        errors.append("Evidence name must be 200 characters or fewer.")
    if category not in CATEGORIES:
        errors.append("Choose an evidence category from the list.")
    if not collected_by:
        errors.append("Enter the name of the investigator collecting this evidence.")
    elif len(collected_by) > 100:
        errors.append("Investigator name must be 100 characters or fewer.")
    if len(description) > 2000:
        errors.append("Description must be 2000 characters or fewer.")
    if errors:
        return _collect_form(errors, 400)

    # Server-generated name: the user's filename never touches the filesystem.
    stored = uuid.uuid4().hex + extension
    path = evidence_path(stored)
    try:
        upload.save(path)
        size = os.path.getsize(path)
    except OSError as exc:
        log.error("Could not store upload: %s", exc, exc_info=True)
        _remove_quietly(path)
        return _collect_form(["The file could not be saved. Check the terminal for details."], 500)

    if size == 0:
        _remove_quietly(path)
        return _collect_form(["The uploaded file is empty."], 400)

    try:
        digest = sha256_file(path)
        code = db.insert_evidence(name, original, stored, category,
                                  description, collected_by, size, digest)
    except (sqlite3.Error, OSError) as exc:
        log.error("Collection failed, removing stored file: %s", exc, exc_info=True)
        _remove_quietly(path)
        return _collect_form(["The evidence could not be recorded, so the file was not kept. "
                              "Check the terminal for details."], 500)

    flash("Evidence collected. Record %s was created and its SHA-256 hash was saved." % code,
          "success")
    return redirect(url_for("main.details", code=code))


def _get_or_404(code):
    record = db.get_evidence(code)
    if record is None:
        abort(404, "No evidence record exists with that ID.")
    return record


@bp.route("/evidence/<code>")
def details(code):
    record = _get_or_404(code)
    history = db.list_verifications(record["id"])
    return render_template("evidence_details.html", e=record, history=history,
                           latest=history[0] if history else None)


@bp.route("/evidence/<code>/download")
def download(code):
    record = _get_or_404(code)
    path = evidence_path(record["stored_filename"])
    if path is None or not os.path.isfile(path):
        abort(404, "The stored evidence file could not be found, so it cannot be downloaded.")
    try:
        return send_file(path, as_attachment=True,
                         download_name=record["original_filename"],
                         mimetype="application/octet-stream")
    except OSError as exc:
        log.error("Download failed for %s: %s", code, exc, exc_info=True)
        abort(500)


@bp.route("/evidence/<code>/verify", methods=["POST"])
def verify(code):
    record = _get_or_404(code)
    path = evidence_path(record["stored_filename"])
    expected = record["sha256_hash"]

    actual = None
    if path is None or not os.path.isfile(path):
        status = "MISSING"
    else:
        try:
            actual = sha256_file(path)
        except FileNotFoundError:
            status = "MISSING"
        except OSError as exc:
            log.error("Verification read error for %s: %s", code, exc, exc_info=True)
            flash("The evidence file exists but could not be read. Check the terminal for details.",
                  "error")
            return redirect(url_for("main.details", code=code))
        else:
            status = "MATCH" if actual == expected else "MISMATCH"

    # Only the log is written. The original recorded hash is never changed.
    db.add_verification(record["id"], expected, actual, status)
    messages = {
        "MATCH": "MATCH: the calculated hash equals the original hash. "
                 "The stored file is consistent with its recorded hash.",
        "MISMATCH": "MISMATCH: the calculated hash differs from the original hash. "
                    "The evidence file has changed since the original hash was recorded.",
        "MISSING": "MISSING: the stored evidence file cannot be found.",
    }
    flash(messages[status], status.lower())
    return redirect(url_for("main.details", code=code) + "#integrity")
