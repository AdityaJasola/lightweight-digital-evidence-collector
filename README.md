# Digital Evidence Collector
### Evidence Collection & Integrity Documentation System

**Digital Evidence Collector** is a lightweight web-based application developed as an academic cybersecurity project. It helps investigators collect digital files, document evidence details, generate SHA-256 hashes and verify the integrity of stored evidence.

> **Important:** This is an academic demonstration, not a certified forensic acquisition platform. It does not independently establish evidence authenticity or replace professional forensic procedures, chain-of-custody rules or legal requirements.

## 1. Introduction
The Digital Evidence Collector is a Python-based web application designed to demonstrate digital evidence collection and integrity documentation. It allows users to upload digital files, record relevant information and monitor whether collected evidence has been modified.

## 2. Project Objectives
- Demonstrate digital evidence collection and documentation.
- Generate SHA-256 cryptographic hashes.
- Maintain structured evidence records.
- Detect modified or missing evidence files.
- Maintain a history of integrity verification.

## 3. Technologies Used
The project uses the following technologies:

- **Python 3:** Core programming language.
- **Flask:** Web application framework.
- **SQLite:** Database management.
- **Hashlib:** SHA-256 hash generation.
- **HTML5:** Webpage structure.
- **CSS3:** User interface styling.
- **JavaScript:** Client-side functionality.
- **Unittest:** Automated testing.

## 4. Main Features
- Digital evidence file uploading.
- Server-side file validation.
- Automatic SHA-256 hash generation.
- Evidence information documentation.
- Evidence records with search functionality.
- Evidence details and download functionality.
- Integrity verification.
- Verification history.
- Overview dashboard.

## 5. System Workflow
The application follows a simple workflow:

1. Investigator selects a digital file.
2. Evidence information is entered.
3. The application validates the uploaded file.
4. The file is stored securely within the local evidence folder.
5. A SHA-256 hash is generated.
6. Evidence details are saved in the SQLite database.
7. The investigator can verify the evidence integrity whenever required.

## 6. SHA-256 Hashing
SHA-256 is a cryptographic hashing algorithm that generates a 256-bit hash value, represented as a 64-character hexadecimal string.

The application calculates the hash using the actual file contents. It reads files in chunks to calculate the hash and stores the resulting value with the evidence record.

Even a small modification to a file produces a different hash.

## 7. Evidence Documentation
For every collected evidence item, the application records relevant information, including:

- Evidence ID.
- Evidence name.
- Original filename.
- Category.
- Investigator name.
- Description.
- Collection timestamp.
- SHA-256 hash.

This information helps maintain organized evidence documentation.

## 8. Evidence Integrity Verification
The application provides an integrity verification feature that recalculates the SHA-256 hash of the stored evidence file and compares it with the original recorded hash.

Three possible verification results are provided:

- **MATCH:** The calculated hash matches the original hash.
- **MISMATCH:** The calculated hash differs from the original hash.
- **MISSING:** The stored evidence file cannot be found.

## 9. Verification History
The application maintains a verification history for each evidence item.

Every integrity check is recorded so that investigators can review previous verification results. The original recorded hash is not overwritten during verification.

Verification history cannot be edited or deleted through the application.

## 10. File Validation
The application performs server-side validation before accepting uploaded files.

Validation includes:

- File extension checking.
- Empty file detection.
- Maximum file size checking.
- Supported file type verification.

**Supported formats:** PNG, JPG, JPEG, PDF, TXT, CSV, LOG, DOCX, PCAP and PCAPNG.

**Maximum file size:** 20 MB.

## 11. Database Management
SQLite is used to maintain evidence records and verification history.

The database stores evidence-related information, including file details, hashes, collection timestamps and integrity verification results.

The database and uploaded evidence files are created locally when the application starts.

## 12. Project Folder Structure
```text
digital-evidence-collector/
│
├── evidence_app/
│   ├── __init__.py
│   ├── routes.py
│   ├── database.py
│   └── hashing.py
│
├── static/
│   ├── css/
│   └── js/
│
├── templates/
│
├── tests/
│   └── test_app.py
│
├── instance/
│   ├── evidence.db
│   └── evidence_files/
│
├── app.py
├── requirements.txt
└── README.md
```

## 13. System Requirements
The following requirements are needed to run the project:

- Windows 10 or Windows 11.
- Python 3.9 or newer.
- Visual Studio Code or another Python editor.
- Internet connection for downloading dependencies during initial setup.

The application itself runs locally and does not require an internet connection during normal operation.

## 14. Installation and Setup
Follow these steps to install the project.

**Step 1:** Clone the repository.

```bash
git clone https://github.com/AdityaJasola/lightweight-digital-evidence-collector.git
```

**Step 2:** Open the project directory.

```bash
cd lightweight-digital-evidence-collector
```

**Step 3:** Create a virtual environment.

```bash
py -m venv venv
```

**Step 4:** Activate the virtual environment.

```powershell
venv\Scripts\activate
```

**Step 5:** Install the required dependencies.

```bash
pip install -r requirements.txt
```

## 15. Running the Application
After completing the installation, execute:

```bash
python app.py
```

Open the following address in your browser:

```text
http://127.0.0.1:5000
```

The application will run locally. Press `Ctrl + C` in the terminal to stop the server.

## 16. Testing and Demonstration
The project includes an automated testing module.

Run the tests using:

```bash
python -m unittest discover -s tests -v
```

A manual integrity demonstration can also be performed:

1. Upload a small text file.
2. Verify its integrity and observe the MATCH result.
3. Modify the stored file manually.
4. Verify it again and observe the MISMATCH result.
5. Delete the stored file and verify again to observe the MISSING result.

This demonstrates how SHA-256 hashing helps identify changes in stored evidence.

## 17. Limitations and Future Improvements
**Current limitations:**
- Designed for a single user running the application locally.
- No login system or role-based access control.
- The database is not tamper-proof.
- Evidence files are stored without encryption.
- Hashes are not digitally signed or independently timestamped.
- The collection timestamp depends on the computer's clock.
- The application does not perform forensic disk imaging.

**Possible future improvements:**
- User authentication and access control.
- Encrypted evidence storage.
- Digital signatures for evidence records.
- Secure audit logging.
- Improved evidence export and reporting.
- Multi-user support.

## 18. Conclusion and Disclaimer
The Digital Evidence Collector demonstrates the basic principles of digital evidence collection, documentation and integrity verification.

By combining Flask, SQLite and SHA-256 hashing, the application provides a simple environment for understanding how digital evidence can be recorded and checked for modifications.

This project was developed for educational purposes as part of a cybersecurity academic project. It is not a certified forensic tool and should not be used as a replacement for professional forensic acquisition, preservation or legal procedures.

---

**Project:** Digital Evidence Collector  
**Category:** Cybersecurity  
**Repository:** https://github.com/AdityaJasola/lightweight-digital-evidence-collector  
**Development Environment:** Python, Flask and SQLite