"""Application factory for Digital Evidence Collector."""
import hmac
import logging
import os
import secrets
import sqlite3

from flask import Flask, abort, render_template, request, session

from . import database

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

CATEGORIES = ["Screenshot", "Document", "Log File", "Network Capture", "Other"]
ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".pdf", ".txt", ".csv", ".log",
    ".docx", ".pcap", ".pcapng",
}


def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_path=os.path.join(BASE_DIR, "instance"),
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )
    app.config.update(
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
        DATABASE=os.path.join(app.instance_path, "evidence.db"),
        EVIDENCE_DIR=os.path.join(app.instance_path, "evidence_files"),
    )
    # The secret key signs the session cookie (CSRF token and flash messages).
    # A random key per start is fine for a local demo.
    app.config["SECRET_KEY"] = os.environ.get("EVIDENCE_SECRET_KEY") or secrets.token_hex(32)
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    os.makedirs(app.config["EVIDENCE_DIR"], exist_ok=True)
    database.init_db(app.config["DATABASE"])
    app.teardown_appcontext(database.close_db)

    # ---- CSRF protection (session-based token) ----
    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(16)
        return session["csrf_token"]

    app.jinja_env.globals["csrf_token"] = csrf_token
    app.jinja_env.globals["CATEGORIES"] = CATEGORIES

    @app.before_request
    def check_csrf():
        if request.method == "POST":
            sent = request.form.get("csrf_token", "")
            expected = session.get("csrf_token", "")
            if not expected or not hmac.compare_digest(sent, expected):
                abort(400, "The form has expired or is invalid. Reload the page and try again.")

    # ---- Template filters ----
    @app.template_filter("filesize")
    def filesize(value):
        size = float(value)
        if size < 1024:
            return "%d B" % size
        for unit in ("KB", "MB"):
            size /= 1024
            if size < 1024 or unit == "MB":
                return "%.1f %s" % (size, unit)

    @app.template_filter("utc")
    def utc(value):
        return "%s UTC" % value if value else "-"

    # ---- Error pages ----
    def error_page(status, title, message):
        return render_template("error.html", status=status, title=title,
                               message=message), status

    @app.errorhandler(400)
    def bad_request(err):
        return error_page(400, "Request rejected", err.description)

    @app.errorhandler(404)
    def not_found(err):
        return render_template("404.html", message=getattr(err, "description", "")), 404

    @app.errorhandler(405)
    def method_not_allowed(_err):
        return error_page(405, "Method not allowed",
                          "This address does not accept that kind of request.")

    @app.errorhandler(413)
    def too_large(_err):
        return render_template("413.html"), 413

    @app.errorhandler(sqlite3.Error)
    def database_error(err):
        app.logger.error("Database error: %s", err, exc_info=True)
        return error_page(500, "Database error",
                          "The evidence database could not be used. Check the terminal for details.")

    @app.errorhandler(500)
    def server_error(_err):
        return error_page(500, "Unexpected error",
                          "Something went wrong. Check the terminal for details.")

    from .routes import bp
    app.register_blueprint(bp)
    return app
