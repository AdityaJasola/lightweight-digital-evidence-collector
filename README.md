# Digital Evidence Collector

Evidence Collection & Integrity Documentation

> **Important:** This is an academic demonstration. It is **not** a certified forensic acquisition platform. It does not independently establish that evidence is authentic, and it does not replace professional forensic procedures, chain-of-custody rules or legal requirements. It runs on localhost for a single user.

## 1. Introduction

Digital Evidence Collector is a small web application for a college cybersecurity project. An investigator uploads a file, describes it, and the system saves it, calculates a SHA-256 hash and records everything in a database. Later, the investigator can check whether the stored file has changed.

## 2. Objectives

- Show how digital evidence is collected and documented.
- Generate a SHA-256 cryptographic hash from the real file contents.
- Store evidence details in SQLite.
- Detect modified or missing evidence by recalculating the hash.
- Keep a record of every integrity check.

## 3. Technologies

Python 3, Flask, SQLite, hashlib (SHA-256), HTML5, CSS3, a little vanilla JavaScript, and unittest. No internet connection is needed to run it.

## 4. Main features

- Evidence upload with server-side validation (type, size, empty files).
- Automatic SHA-256 hash (read in chunks) and UTC collection time.
- Evidence records table with search by ID, name or original filename.
- Details page with download, copy-hash and print-friendly documentation.
- Integrity verification with three results: MATCH, MISMATCH, MISSING.
- Verification history per evidence item (cannot be edited or deleted in the app).
- Overview page whose numbers come only from the database.

## 5. Folder structure

```
digital-evidence-collector/
  app.py                 starts the server
  requirements.txt
  evidence_app/
    __init__.py          app setup, CSRF check, error pages
    routes.py            pages and actions
    database.py          SQLite tables and queries
    hashing.py           SHA-256 function
  templates/             HTML pages
  static/css, static/js  styles and scripts
  instance/              created automatically
    evidence.db          database
    evidence_files/      uploaded evidence (not web-accessible)
  tests/test_app.py      automated tests
```

## 6. Requirements

- Windows 10 or 11
- Python 3.9 or newer (from python.org; tick "Add Python to PATH" when installing)

## 7. Installation (Windows)

Open **Command Prompt** or **PowerShell** in the project folder.

```
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

In PowerShell, if activation is blocked, run `Set-ExecutionPolicy -Scope Process RemoteSigned` first, then activate again.

## 8. Launch

```
python app.py
```

Open **http://127.0.0.1:5000** in your browser. Stop the server with `Ctrl+C`. The database and evidence folder are created on first start.

## 9. How to collect evidence

1. Click **Collect Evidence**.
2. Choose the file, enter the evidence name, pick a category and enter the investigator name. Description is optional.
3. Click **Collect evidence**. The server saves the file under a random (UUID) name, calculates the SHA-256 hash, and records the details.
4. You are taken to the details page for the new record (for example `EV-20261103-A1B2C3`).

Allowed types: png, jpg, jpeg, pdf, txt, csv, log, docx, pcap, pcapng. Maximum size: 20 MB.

## 10. How SHA-256 verification works

A SHA-256 hash is a 64-character fingerprint of a file's exact bytes. Changing even one byte produces a completely different hash. When the file is collected, the hash is saved. When you click **Verify Integrity**, the app recalculates the hash of the stored file and compares it with the saved one:

- **MATCH** – the hashes are equal. The file is consistent with its recorded hash.
- **MISMATCH** – the hashes differ. The file has changed since collection.
- **MISSING** – the stored file cannot be found.

Every check is saved in the verification history. The original hash is never overwritten, and verification never changes the evidence file.

## 11. How to test evidence integrity (demonstration)

1. Collect a small `.txt` file.
2. Click **Verify Integrity**. Result: MATCH.
3. Stop the server. Open `instance\evidence_files`, and open the file with the long random name in Notepad. Add a character and save.
4. Start the server, open the record and click **Verify Integrity**. Result: MISMATCH. The history shows both checks.
5. Delete that file and verify again. Result: MISSING.

To run the automated tests (they use temporary folders and never touch real evidence):

```
python -m unittest discover -s tests -v
```

## 12. Common errors

| Problem | Solution |
|---|---|
| `python` or `py` is not recognized | Reinstall Python and tick "Add Python to PATH", or use `py` instead of `python`. |
| `No module named flask` | Activate the virtual environment (`venv\Scripts\activate`) and run `pip install -r requirements.txt`. |
| Port 5000 already in use | Close the other program, or change `port=5000` in `app.py`. |
| "File type not supported" | Use one of the allowed extensions listed above. |
| "File too large" | The limit is 20 MB. Choose a smaller file. |
| "The form has expired" | Reload the page and submit again (the session token changes when the server restarts). |
| Verification shows MISMATCH | The stored file was changed after collection. This is the expected result of the demonstration in section 11. |

## 13. Academic limitations

- Single user, localhost only. There is no login, user roles or access control.
- The hash proves only that the stored file has not changed since it was collected. It does not prove the file was authentic or unaltered *before* upload.
- Someone with access to the computer could edit both the database and the file. The database is not tamper-proof.
- Hashes are not digitally signed or time-stamped by a trusted third party.
- Evidence files are stored unencrypted on disk.
- Collection time comes from the computer's clock.
- It is not a forensic imaging tool and has not been validated for court use.
