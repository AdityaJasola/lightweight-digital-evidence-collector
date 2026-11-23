"""Automated tests. Each test uses a temporary database and evidence folder."""
import hashlib
import io
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evidence_app import create_app  # noqa: E402

TOKEN = "test-token"
SAMPLE = b"Sample evidence content: line 1\nline 2\n"


class EvidenceTestCase(unittest.TestCase):
    def make_app(self):
        return create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": os.path.join(self.tmp, "test.db"),
            "EVIDENCE_DIR": os.path.join(self.tmp, "files"),
        })

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="evidence_test_")
        self.app = self.make_app()
        self.client = self.app.test_client()
        with self.client.session_transaction() as sess:
            sess["csrf_token"] = TOKEN

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- helpers ----
    def upload(self, content=SAMPLE, filename="notes.txt", name="Test evidence",
               category="Document", by="Investigator A", description="A test",
               follow=False, token=TOKEN):
        data = {
            "csrf_token": token,
            "evidence_name": name,
            "evidence_category": category,
            "collected_by": by,
            "description": description,
            "evidence_file": (io.BytesIO(content), filename),
        }
        return self.client.post("/collect", data=data,
                                content_type="multipart/form-data",
                                follow_redirects=follow)

    def rows(self, sql, params=()):
        conn = sqlite3.connect(self.app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def collect_one(self, **kw):
        resp = self.upload(**kw)
        self.assertEqual(resp.status_code, 302)
        self.client.get(resp.headers["Location"])  # shows and clears the flash message
        return self.rows("SELECT * FROM evidence ORDER BY id DESC")[0]

    def post_verify(self, code):
        return self.client.post("/evidence/%s/verify" % code,
                                data={"csrf_token": TOKEN}, follow_redirects=True)

    def stored_path(self, row):
        return os.path.join(self.app.config["EVIDENCE_DIR"], row["stored_filename"])

    # ---- tests ----
    def test_01_app_starts_and_pages_load(self):
        for url in ("/", "/evidence", "/collect"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(self.client.get("/static/css/style.css").status_code, 200)
        self.assertEqual(self.client.get("/static/js/main.js").status_code, 200)

    def test_02_database_initializes(self):
        tables = {r["name"] for r in self.rows(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn("evidence", tables)
        self.assertIn("verification_logs", tables)
        fks = self.rows("PRAGMA foreign_key_list(verification_logs)")
        self.assertEqual(fks[0]["table"], "evidence")

    def test_03_upload_works(self):
        resp = self.upload(follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Evidence collected", resp.data)
        self.assertEqual(len(self.rows("SELECT * FROM evidence")), 1)

    def test_04_unique_evidence_codes(self):
        self.upload()
        self.upload()
        codes = [r["evidence_code"] for r in self.rows("SELECT evidence_code FROM evidence")]
        self.assertEqual(len(codes), 2)
        self.assertEqual(len(set(codes)), 2)
        self.assertRegex(codes[0], r"^EV-\d{8}-[0-9A-F]{6}$")

    def test_05_sha256_correct(self):
        row = self.collect_one()
        self.assertEqual(row["sha256_hash"], hashlib.sha256(SAMPLE).hexdigest())
        self.assertEqual(len(row["sha256_hash"]), 64)
        with open(self.stored_path(row), "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), row["sha256_hash"])

    def test_06_metadata_stored(self):
        row = self.collect_one(filename="My Report.txt", name="Report", category="Log File",
                               by="Dana", description="desc")
        self.assertEqual(row["evidence_name"], "Report")
        self.assertEqual(row["original_filename"], "My_Report.txt")
        self.assertEqual(row["evidence_category"], "Log File")
        self.assertEqual(row["collected_by"], "Dana")
        self.assertEqual(row["description"], "desc")
        self.assertEqual(row["file_size"], len(SAMPLE))
        self.assertTrue(row["collected_at_utc"])
        # Stored name is server generated, not the user's filename
        self.assertNotIn("Report", row["stored_filename"])
        self.assertTrue(row["stored_filename"].endswith(".txt"))

    def test_07_dashboard_shows_records(self):
        self.assertIn(b"No evidence has been collected yet", self.client.get("/").data)
        row = self.collect_one()
        page = self.client.get("/").data
        self.assertIn(row["evidence_code"].encode(), page)
        self.assertIn(b"Evidence records", page)

    def test_08_search(self):
        a = self.collect_one(name="Alpha laptop image", filename="alpha.txt")
        b = self.collect_one(name="Beta router log", filename="beta_router.log")
        by_name = self.client.get("/evidence?q=Alpha").data
        self.assertIn(a["evidence_code"].encode(), by_name)
        self.assertNotIn(b["evidence_code"].encode(), by_name)
        by_file = self.client.get("/evidence?q=beta_router").data
        self.assertIn(b["evidence_code"].encode(), by_file)
        self.assertNotIn(a["evidence_code"].encode(), by_file)
        by_code = self.client.get("/evidence?q=" + a["evidence_code"]).data
        self.assertIn(a["evidence_code"].encode(), by_code)
        self.assertIn(b"No evidence matches", self.client.get("/evidence?q=zzzz").data)
        # SQL wildcard characters are treated literally
        self.assertIn(b"No evidence matches", self.client.get("/evidence?q=%25").data)

    def test_09_details_page(self):
        row = self.collect_one()
        page = self.client.get("/evidence/" + row["evidence_code"]).data
        self.assertIn(row["sha256_hash"].encode(), page)
        self.assertIn(b"Verify Integrity", page)
        self.assertIn(b"Copy SHA-256 Hash", page)
        self.assertIn(b"Print Evidence Documentation", page)
        self.assertNotIn(self.app.config["EVIDENCE_DIR"].encode(), page)
        self.assertNotIn(row["stored_filename"].encode(), page)

    def test_10_download(self):
        row = self.collect_one(filename="proof.txt")
        resp = self.client.get("/evidence/%s/download" % row["evidence_code"])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, SAMPLE)
        self.assertIn("attachment", resp.headers["Content-Disposition"])
        self.assertIn("proof.txt", resp.headers["Content-Disposition"])
        resp.close()

    def test_11_verify_match(self):
        row = self.collect_one()
        resp = self.post_verify(row["evidence_code"])
        self.assertIn(b"status-match", resp.data)
        log = self.rows("SELECT * FROM verification_logs")[0]
        self.assertEqual(log["verification_status"], "MATCH")
        self.assertEqual(log["expected_hash"], log["actual_hash"])

    def test_12_verify_mismatch(self):
        row = self.collect_one()
        with open(self.stored_path(row), "ab") as fh:
            fh.write(b"tampered")
        resp = self.post_verify(row["evidence_code"])
        self.assertIn(b"status-mismatch", resp.data)
        log = self.rows("SELECT * FROM verification_logs")[0]
        self.assertEqual(log["verification_status"], "MISMATCH")
        self.assertNotEqual(log["expected_hash"], log["actual_hash"])
        # Original hash must not be replaced
        after = self.rows("SELECT sha256_hash FROM evidence")[0]["sha256_hash"]
        self.assertEqual(after, row["sha256_hash"])

    def test_13_verify_missing(self):
        row = self.collect_one()
        os.remove(self.stored_path(row))
        resp = self.post_verify(row["evidence_code"])
        self.assertIn(b"status-missing", resp.data)
        log = self.rows("SELECT * FROM verification_logs")[0]
        self.assertEqual(log["verification_status"], "MISSING")
        self.assertIsNone(log["actual_hash"])
        self.assertEqual(self.client.get(
            "/evidence/%s/download" % row["evidence_code"]).status_code, 404)

    def test_14_verification_history(self):
        row = self.collect_one()
        self.post_verify(row["evidence_code"])
        with open(self.stored_path(row), "ab") as fh:
            fh.write(b"x")
        self.post_verify(row["evidence_code"])
        logs = self.rows("SELECT * FROM verification_logs ORDER BY id")
        self.assertEqual([l["verification_status"] for l in logs], ["MATCH", "MISMATCH"])
        self.assertTrue(all(l["verified_at_utc"] for l in logs))
        page = self.client.get("/evidence/" + row["evidence_code"]).data
        self.assertIn(b"MATCH", page)
        self.assertIn(b"MISMATCH", page)
        self.assertIn(b"2", self.client.get("/").data)

    def test_15_unsupported_rejected(self):
        resp = self.upload(filename="malware.exe")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"File type not supported", resp.data)
        resp = self.upload(filename="script.php.txt.exe")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(len(self.rows("SELECT * FROM evidence")), 0)
        self.assertEqual(os.listdir(self.app.config["EVIDENCE_DIR"]), [])

    def test_16_empty_rejected(self):
        resp = self.upload(content=b"")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"empty", resp.data)
        self.assertEqual(len(self.rows("SELECT * FROM evidence")), 0)
        self.assertEqual(os.listdir(self.app.config["EVIDENCE_DIR"]), [])

    def test_17_oversized_rejected(self):
        resp = self.upload(content=b"a" * (20 * 1024 * 1024 + 1024))
        self.assertEqual(resp.status_code, 413)
        self.assertIn(b"File too large", resp.data)
        self.assertEqual(len(self.rows("SELECT * FROM evidence")), 0)

    def test_18_invalid_evidence_id(self):
        for url in ("/evidence/EV-00000000-XXXXXX", "/evidence/EV-00000000-XXXXXX/download",
                    "/evidence/../../etc/passwd", "/nonexistent"):
            self.assertEqual(self.client.get(url).status_code, 404, url)
        resp = self.client.post("/evidence/EV-00000000-XXXXXX/verify",
                                data={"csrf_token": TOKEN})
        self.assertEqual(resp.status_code, 404)

    # ---- additional checks ----
    def test_19_missing_fields_rejected(self):
        resp = self.upload(name="", by="")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"Enter an evidence name", resp.data)
        self.assertIn(b"investigator", resp.data)
        self.assertEqual(self.upload(category="Bogus").status_code, 400)
        self.assertEqual(len(self.rows("SELECT * FROM evidence")), 0)

    def test_20_csrf_required(self):
        self.assertEqual(self.upload(token="wrong").status_code, 400)
        row = self.collect_one()
        resp = self.client.post("/evidence/%s/verify" % row["evidence_code"], data={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(len(self.rows("SELECT * FROM verification_logs")), 0)

    def test_21_path_traversal_filename_is_neutralised(self):
        row = self.collect_one(filename="../../evil.txt")
        self.assertEqual(row["original_filename"], "evil.txt")
        self.assertEqual(os.listdir(self.app.config["EVIDENCE_DIR"]), [row["stored_filename"]])

    def test_22_html_in_input_is_escaped(self):
        row = self.collect_one(name="<script>alert(1)</script>")
        page = self.client.get("/evidence/" + row["evidence_code"]).data
        self.assertNotIn(b"<script>alert(1)</script>", page)
        self.assertIn(b"&lt;script&gt;", page)

    def test_23_data_persists_after_restart(self):
        row = self.collect_one()
        restarted = self.make_app().test_client()
        resp = restarted.get("/evidence/" + row["evidence_code"])
        self.assertEqual(resp.status_code, 200)
        self.assertIn(row["sha256_hash"].encode(), resp.data)

    def test_24_file_removed_if_database_insert_fails(self):
        from unittest import mock
        with mock.patch("evidence_app.routes.db.insert_evidence",
                        side_effect=sqlite3.OperationalError("disk I/O error")):
            resp = self.upload()
        self.assertEqual(resp.status_code, 500)
        self.assertIn(b"could not be recorded", resp.data)
        self.assertEqual(os.listdir(self.app.config["EVIDENCE_DIR"]), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
