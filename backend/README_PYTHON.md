# Python Backend — Healthcare AI Consent & Inference Audit

This version replaces the original **Java 21 + Spring Boot + JPA/H2 backend** with:

- Python 3.11+
- Flask
- SQLAlchemy
- SQLite
- Werkzeug password hashing
- The existing HTML/CSS/JavaScript UI
- The existing Solidity + Hardhat blockchain demo

## 1. Install

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
```

## 2. Run Python backend

```bash
python app.py
```

Open:

`http://127.0.0.1:8080`

The SQLite database `healthcare_audit.db` is created automatically.

## 3. Demo accounts

| Role | Username | Password |
|---|---|---|
| Patient | `patient` | `patient123` |
| Provider | `provider` | `provider123` |
| Admin | `admin` | `admin123` |

## 4. Demo flow

1. Login as `patient`.
2. Grant `provider` consent for `MODEL_V1`.
3. Login as `provider`.
4. Run an inference using the same consent, subject and model.
5. The API validates provider + subject + model + expiry + revocation.
6. The system creates an auditable inference receipt and SHA-256 digests.
7. Revoke the consent as patient.
8. Repeat inference; it is rejected.
9. Login as admin to inspect models and audit records.
10. Use the Blockchain page for the existing MetaMask/Hardhat demonstration.

## 5. Blockchain

The blockchain folder is intentionally kept in JavaScript/Solidity because the smart contract itself is Solidity and Hardhat is the existing deployment tool.

Start it separately:

```bash
cd blockchain
npm install
npm run node
```

In another terminal:

```bash
cd blockchain
npm run deploy
```

Then configure the deployed address in:

`backend/static/js/blockchain.js`

## Important

This remains an educational prototype. It uses synthetic identifiers and a deliberately non-clinical scoring rule. It is **not** a medical device or clinical decision-support system.

For production use, move users/secrets to a real database/secret manager, add CSRF protection, use HTTPS, add proper authorization policies, and never put real patient records on a public blockchain.
