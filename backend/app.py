from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, select, func, desc
from sqlalchemy.orm import declarative_base, sessionmaker
import hashlib
import secrets

from blockchain import blockchain


BASE_DIR = __import__("pathlib").Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "healthcare_audit.db"


app = Flask(
    __name__,
    static_folder="static",
    static_url_path=""
)
app.secret_key = "dev-only-change-this-secret"
app.config["JSON_SORT_KEYS"] = False

engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
Base = declarative_base()


# ============================================================
# DATABASE MODELS
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)


class Consent(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True)
    consent_id = Column(String(32), unique=True, nullable=False)
    subject_id = Column(String(120), nullable=False)
    patient_username = Column(String(80), nullable=False)
    provider_username = Column(String(80), nullable=False)
    model_id = Column(String(80), nullable=False)
    purpose = Column(String(200), nullable=False)
    expiry = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    blockchain_tx_hash = Column(String(100), nullable=True)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True)
    model_id = Column(String(80), unique=True, nullable=False)
    version = Column(String(40), nullable=False)
    model_digest = Column(String(64), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    description = Column(String(500), nullable=True)


class InferenceAudit(Base):
    __tablename__ = "inference_audit"

    id = Column(Integer, primary_key=True)
    receipt_id = Column(String(32), nullable=False)
    consent_id = Column(String(32), nullable=False)
    subject_id = Column(String(120), nullable=False)
    provider_username = Column(String(80), nullable=False)
    model_id = Column(String(80), nullable=False)
    model_digest = Column(String(64), nullable=False)
    output_digest = Column(String(64), nullable=False)
    output_label = Column(String(80), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    blockchain_recorded = Column(Boolean, nullable=False, default=False)


Base.metadata.create_all(engine)


# ============================================================
# FIXED PROVIDERS / ADMIN
# ============================================================

# Patients are NOT hardcoded. Any number of patients can register
# through the registration flow below. Exactly two providers are
# created by the application: provider and provider2.

FIXED_PROVIDERS = {
    "provider": "provider123",
    "provider2": "provider2123",
}

FIXED_ADMIN = {
    "admin": "admin123",
}


def seed_system_users():
    """Create the two fixed providers and one fixed admin if missing."""

    with SessionLocal() as db:
        for username, password in FIXED_PROVIDERS.items():
            user = db.scalar(
                select(User).where(User.username == username)
            )
            if user is None:
                db.add(
                    User(
                        username=username,
                        password_hash=generate_password_hash(password),
                        role="PROVIDER",
                    )
                )
            elif user.role != "PROVIDER":
                user.role = "PROVIDER"

        for username, password in FIXED_ADMIN.items():
            user = db.scalar(
                select(User).where(User.username == username)
            )
            if user is None:
                db.add(
                    User(
                        username=username,
                        password_hash=generate_password_hash(password),
                        role="ADMIN",
                    )
                )
            elif user.role != "ADMIN":
                user.role = "ADMIN"

        db.commit()


seed_system_users()


# ============================================================
# BLOCKCHAIN DEMO IDENTITY
# ============================================================

# For this educational local prototype, the provider application
# user is mapped to Hardhat Account #0.
#
# This is necessary because the Solidity contract checks:
#
#     provider == msg.sender
#
# during recordInference().
#
# A production system would use real wallet-based identities
# instead of this local Hardhat account.

PROVIDER_BLOCKCHAIN_ADDRESS = blockchain.account


def get_provider_blockchain_address(username):
    """
    Return the configured local blockchain address for either fixed provider.

    The current educational Hardhat setup uses one demo account.
    Production should map each provider to a distinct wallet.
    """

    if username in FIXED_PROVIDERS:
        return PROVIDER_BLOCKCHAIN_ADDRESS

    raise ValueError(
        f"No blockchain wallet is configured for provider '{username}'."
    )


# ============================================================
# HELPERS
# ============================================================

def now_utc():
    return datetime.now(timezone.utc)


def is_expired(dt):
    # SQLite may return timezone-naive datetimes even when
    # timezone=True is declared.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt < now_utc()


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(4).upper()}"


def current_user():
    username = session.get("username")
    if not username:
        return None

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.username == username)
        )

        if not user:
            return None

        return {
            "username": user.username,
            "role": user.role,
            "password_hash": user.password_hash,
        }


# ============================================================
# SERIALIZATION HELPERS
# ============================================================

def consent_dict(c):
    return {
        "id": c.id,
        "consentId": c.consent_id,
        "subjectId": c.subject_id,
        "patientUsername": c.patient_username,
        "providerUsername": c.provider_username,
        "modelId": c.model_id,
        "purpose": c.purpose,
        "expiry": c.expiry.isoformat(),
        "revoked": c.revoked,
        "blockchainTxHash": c.blockchain_tx_hash,
    }


def model_dict(m):
    return {
        "id": m.id,
        "modelId": m.model_id,
        "version": m.version,
        "modelDigest": m.model_digest,
        "active": m.active,
        "description": m.description,
    }


def audit_dict(a):
    return {
        "id": a.id,
        "receiptId": a.receipt_id,
        "consentId": a.consent_id,
        "subjectId": a.subject_id,
        "providerUsername": a.provider_username,
        "modelId": a.model_id,
        "modelDigest": a.model_digest,
        "outputDigest": a.output_digest,
        "outputLabel": a.output_label,
        "timestamp": a.timestamp.isoformat(),
        "blockchainRecorded": a.blockchain_recorded,
    }


# ============================================================
# DATABASE SEEDING
# ============================================================

def register_model_db(db, model_id, version, description):
    m = db.scalar(
        select(ModelRegistry).where(
            ModelRegistry.model_id == model_id
        )
    )

    digest = sha256(
        f"{model_id}:{version}:{description}"
    )

    if m is None:
        m = ModelRegistry(
            model_id=model_id,
            version=version,
            model_digest=digest,
            active=True,
            description=description
        )

        db.add(m)

    else:
        m.version = version
        m.model_digest = digest
        m.active = True
        m.description = description

    return m


def seed_models():
    with SessionLocal() as db:

        if db.scalar(
            select(func.count(ModelRegistry.id))
        ) == 0:

            register_model_db(
                db,
                "MODEL_V1",
                "1.0",
                "Synthetic non-clinical scoring model"
            )

            register_model_db(
                db,
                "MODEL_V2",
                "2.0",
                "Updated educational scoring model"
            )

            db.commit()


seed_models()


# ============================================================
# AUTHENTICATION
# ============================================================

def require_login(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("username"):

            if request.path.startswith("/api/"):
                return jsonify({
                    "error": "Authentication required."
                }), 401

            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped


def require_role(role):

    def decorator(view):

        @wraps(view)
        def wrapped(*args, **kwargs):

            if not session.get("username"):

                if request.path.startswith("/api/"):
                    return jsonify({
                        "error": "Authentication required."
                    }), 401

                return redirect(url_for("login"))

            if session.get("role") != role:

                if request.path.startswith("/api/"):
                    return jsonify({
                        "error": f"Role required: {role}"
                    }), 403

                return "Access denied", 403

            return view(*args, **kwargs)

        return wrapped

    return decorator


# ============================================================
# WEB PAGES
# ============================================================

@app.get("/login")
def login():

    if session.get("username"):
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.post("/login")
def login_post():

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.username == username)
        )

        if not user or not check_password_hash(
            user.password_hash,
            password
        ):
            return redirect(
                url_for(
                    "login",
                    error="Invalid username or password"
                )
            )

        role = user.role

    session.clear()
    session["username"] = username
    session["role"] = role

    return redirect(url_for("dashboard"))


@app.get("/register")
def register_page():
    if session.get("username"):
        return redirect(url_for("dashboard"))

    error = request.args.get("error", "")
    error_html = (
        f'<p style="color:#b91c1c;font-weight:600;">{error}</p>'
        if error else ""
    )

    return f"""
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Patient Registration</title>
    <style>
        body {{ font-family: Arial, sans-serif; background:#f5f7fb; margin:0; }}
        .card {{ max-width:420px; margin:70px auto; background:white; padding:30px;
                 border-radius:14px; box-shadow:0 8px 30px rgba(0,0,0,.08); }}
        h1 {{ margin-top:0; }}
        label {{ display:block; margin-top:16px; font-weight:600; }}
        input {{ width:100%; box-sizing:border-box; padding:11px; margin-top:6px;
                 border:1px solid #cbd5e1; border-radius:8px; }}
        button {{ width:100%; margin-top:22px; padding:12px; border:0; border-radius:8px;
                  background:#2563eb; color:white; font-weight:700; cursor:pointer; }}
        a {{ display:block; margin-top:16px; text-align:center; }}
        .note {{ font-size:13px; color:#475569; margin-top:14px; }}
    </style>
</head>
<body>
<div class="card">
    <h1>Patient Registration</h1>
    <p>Create a new patient account.</p>
    {error_html}
    <form method="post" action="/register">
        <label>Username</label>
        <input name="username" minlength="3" maxlength="80" required>

        <label>Password</label>
        <input type="password" name="password" minlength="8" required>

        <label>Confirm Password</label>
        <input type="password" name="confirm_password" minlength="8" required>

        <button type="submit">Create Patient Account</button>
    </form>
    <a href="/login">Back to Login</a>
    <div class="note">Providers are fixed to exactly two accounts: provider and provider2.</div>
</div>
</body>
</html>
"""


@app.post("/register")
def register_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not username or not password or not confirm_password:
        return redirect(
            url_for("register_page", error="All fields are required.")
        )

    if len(username) < 3 or len(username) > 80:
        return redirect(
            url_for("register_page", error="Username must be 3-80 characters.")
        )

    if len(password) < 8:
        return redirect(
            url_for("register_page", error="Password must be at least 8 characters.")
        )

    if password != confirm_password:
        return redirect(
            url_for("register_page", error="Passwords do not match.")
        )

    # Patient registration only. Providers are fixed to exactly two accounts.
    if username in FIXED_PROVIDERS or username in FIXED_ADMIN:
        return redirect(
            url_for("register_page", error="This username is reserved.")
        )

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(User.username == username)
        )

        if existing:
            return redirect(
                url_for("register_page", error="Username already exists.")
            )

        patient = User(
            username=username,
            password_hash=generate_password_hash(password),
            role="PATIENT",
        )
        db.add(patient)
        db.commit()

    return redirect(
        url_for("login", registered="1")
    )


@app.post("/api/register")
def register_api():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    if len(username) < 3 or len(username) > 80:
        return jsonify({"error": "Username must be 3-80 characters."}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    if username in FIXED_PROVIDERS or username in FIXED_ADMIN:
        return jsonify({"error": "This username is reserved."}), 400

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(User.username == username)
        )

        if existing:
            return jsonify({"error": "Username already exists."}), 409

        patient = User(
            username=username,
            password_hash=generate_password_hash(password),
            role="PATIENT",
        )
        db.add(patient)
        db.commit()

        return jsonify({
            "message": "Patient registered successfully.",
            "username": patient.username,
            "role": patient.role,
        }), 201


@app.post("/logout")
def logout():

    session.clear()

    return redirect(
        url_for(
            "login",
            logout="1"
        )
    )


@app.get("/")
@app.get("/dashboard")
@require_login
def dashboard():
    return render_template("dashboard.html")


@app.get("/consent")
@require_role("PATIENT")
def consent_page():
    return render_template("consent.html")


@app.get("/inference")
@require_role("PROVIDER")
def inference_page():
    return render_template("inference.html")


@app.get("/blockchain")
@require_login
def blockchain_page():
    return render_template("blockchain.html")


@app.get("/admin/models")
@require_role("ADMIN")
def models_page():
    return render_template("models.html")


# ============================================================
# USER API
# ============================================================

@app.get("/api/me")
@require_login
def me():

    return jsonify({
        "username": session["username"],
        "roles": [
            f"ROLE_{session['role']}"
        ]
    })


# ============================================================
# PROVIDER API
# ============================================================

@app.get("/api/providers")
@require_role("PATIENT")
def list_providers():
    with SessionLocal() as db:
        rows = db.scalars(
            select(User).where(
                User.role == "PROVIDER"
            ).order_by(User.id)
        ).all()

        return jsonify([
            {
                "username": user.username,
                "role": user.role,
            }
            for user in rows
        ])


# ============================================================
# CONSENT API
# ============================================================

@app.get("/api/consents")
@require_login
def list_consents():

    username = session["username"]

    with SessionLocal() as db:

        if session["role"] == "PATIENT":

            rows = db.scalars(
                select(Consent).where(
                    Consent.patient_username == username
                )
            ).all()

        else:

            rows = db.scalars(
                select(Consent).where(
                    Consent.provider_username == username
                )
            ).all()

        return jsonify(
            [
                consent_dict(c)
                for c in rows
            ]
        )


@app.post("/api/consents")
@require_role("PATIENT")
def grant_consent():

    data = request.get_json(silent=True) or {}

    required = [
        "providerUsername",
        "subjectId",
        "modelId",
        "purpose",
        "expirySeconds"
    ]

    if any(
        k not in data or data[k] in ("", None)
        for k in required
    ):
        return jsonify({
            "error": "All consent fields are required."
        }), 400

    try:

        expiry_seconds = int(
            data["expirySeconds"]
        )

    except (TypeError, ValueError):

        return jsonify({
            "error": "expirySeconds must be an integer."
        }), 400

    if expiry_seconds < 60:

        return jsonify({
            "error": "Expiry must be at least 60 seconds."
        }), 400

    provider_username = str(
        data["providerUsername"]
    ).strip()

    if provider_username not in FIXED_PROVIDERS:
        return jsonify({
            "error": "Invalid provider. Only provider and provider2 are available."
        }), 400

    with SessionLocal() as provider_db:
        provider_user = provider_db.scalar(
            select(User).where(User.username == provider_username)
        )
        if not provider_user or provider_user.role != "PROVIDER":
            return jsonify({
                "error": "Selected provider is not available."
            }), 400

    try:

        provider_address = get_provider_blockchain_address(
            provider_username
        )

    except ValueError as exc:

        return jsonify({
            "error": str(exc)
        }), 400

    with SessionLocal() as db:

        # ----------------------------------------------------
        # 1. Validate model in SQLite
        # ----------------------------------------------------

        model = db.scalar(
            select(ModelRegistry).where(
                ModelRegistry.model_id == data["modelId"]
            )
        )

        if not model:

            return jsonify({
                "error": "Model is not registered."
            }), 400

        if not model.active:

            return jsonify({
                "error": "Model is not active."
            }), 400

        # ----------------------------------------------------
        # 2. Generate consent
        # ----------------------------------------------------

        consent_id = new_id("C")

        expiry = (
            now_utc()
            + timedelta(seconds=expiry_seconds)
        )

        c = Consent(
            consent_id=consent_id,
            patient_username=session["username"],
            provider_username=provider_username,
            subject_id=str(data["subjectId"]),
            model_id=str(data["modelId"]),
            purpose=str(data["purpose"]),
            expiry=expiry,
            revoked=False,
            blockchain_tx_hash=None,
        )

        # ----------------------------------------------------
        # 3. Make sure model exists on blockchain
        # ----------------------------------------------------

        blockchain.ensure_model_registered(
            model.model_id
        )

        # ----------------------------------------------------
        # 4. Grant consent on blockchain
        # ----------------------------------------------------

        blockchain_result = blockchain.grant_consent(
            consent_id=consent_id,
            subject_id=c.subject_id,
            provider_address=provider_address,
            model_id=c.model_id,
            purpose=c.purpose,
            expiry_timestamp=int(
                expiry.timestamp()
            ),
        )

        # ----------------------------------------------------
        # 5. Store blockchain transaction hash
        # ----------------------------------------------------

        c.blockchain_tx_hash = (
            blockchain_result["tx_hash"]
        )

        db.add(c)
        db.commit()
        db.refresh(c)

        return jsonify({
            **consent_dict(c),
            "blockchain": {
                "transactionHash":
                    blockchain_result["tx_hash"],
                "blockNumber":
                    blockchain_result["block_number"],
                "providerAddress":
                    provider_address,
            }
        }), 201


@app.post("/api/consents/<consent_id>/revoke")
@require_role("PATIENT")
def revoke_consent(consent_id):

    with SessionLocal() as db:

        c = db.scalar(
            select(Consent).where(
                Consent.consent_id == consent_id
            )
        )

        if not c:

            return jsonify({
                "error": "Consent not found."
            }), 404

        if c.patient_username != session["username"]:

            return jsonify({
                "error": "Only the consent owner can revoke it."
            }), 403

        if c.revoked:

            return jsonify({
                "error": "Consent is already revoked."
            }), 400

        # ----------------------------------------------------
        # Revoke on blockchain first
        # ----------------------------------------------------

        blockchain_result = blockchain.revoke_consent(
            consent_id
        )

        # ----------------------------------------------------
        # Update SQLite after blockchain success
        # ----------------------------------------------------

        c.revoked = True

        db.commit()

        return jsonify({
            "status": "revoked",
            "consentId": consent_id,
            "blockchain": {
                "transactionHash":
                    blockchain_result["tx_hash"],
                "blockNumber":
                    blockchain_result["block_number"],
            }
        })


# ============================================================
# MODEL API
# ============================================================

@app.get("/api/models")
@require_login
def active_models():

    with SessionLocal() as db:

        rows = db.scalars(
            select(ModelRegistry).where(
                ModelRegistry.active.is_(True)
            )
        ).all()

        return jsonify(
            [
                model_dict(m)
                for m in rows
            ]
        )


@app.get("/api/models/all")
@require_role("ADMIN")
def all_models():

    with SessionLocal() as db:

        rows = db.scalars(
            select(ModelRegistry).order_by(
                ModelRegistry.id
            )
        ).all()

        return jsonify(
            [
                model_dict(m)
                for m in rows
            ]
        )


@app.post("/api/models")
@require_role("ADMIN")
def register_model():

    data = request.get_json(silent=True) or {}

    model_id = str(
        data.get("modelId", "")
    ).strip()

    version = str(
        data.get("version", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    if not model_id or not version:

        return jsonify({
            "error": "modelId and version are required."
        }), 400

    with SessionLocal() as db:

        m = register_model_db(
            db,
            model_id,
            version,
            description
        )

        # ----------------------------------------------------
        # Register model on blockchain
        # ----------------------------------------------------

        blockchain_result = (
            blockchain.ensure_model_registered(
                model_id
            )
        )

        db.commit()

        response = model_dict(m)

        if blockchain_result:

            response["blockchain"] = {
                "transactionHash":
                    blockchain_result["tx_hash"],
                "blockNumber":
                    blockchain_result["block_number"],
            }

        else:

            response["blockchain"] = {
                "alreadyRegistered": True
            }

        return jsonify(response), 201


# ============================================================
# AI INFERENCE + BLOCKCHAIN AUDIT
# ============================================================

@app.post("/api/inference")
@require_role("PROVIDER")
def run_inference():

    data = request.get_json(silent=True) or {}

    required = [
        "consentId",
        "subjectId",
        "modelId",
        "age",
        "bloodPressure",
        "cholesterol"
    ]

    if any(
        k not in data
        for k in required
    ):
        return jsonify({
            "error": "All inference fields are required."
        }), 400

    try:

        age = int(data["age"])
        bp = int(data["bloodPressure"])
        cholesterol = int(data["cholesterol"])

    except (TypeError, ValueError):

        return jsonify({
            "error": (
                "Age, blood pressure and cholesterol "
                "must be numbers."
            )
        }), 400

    if min(age, bp, cholesterol) < 0:

        return jsonify({
            "error": "Input values cannot be negative."
        }), 400

    with SessionLocal() as db:

        # ----------------------------------------------------
        # 1. Find consent
        # ----------------------------------------------------

        c = db.scalar(
            select(Consent).where(
                Consent.consent_id == data["consentId"]
            )
        )

        if not c:

            return jsonify({
                "error": "Consent not found."
            }), 404

        # ----------------------------------------------------
        # 2. Verify application-level authorization
        # ----------------------------------------------------

        if c.provider_username != session["username"]:

            return jsonify({
                "error": "Provider is not authorized."
            }), 403

        if c.subject_id != data["subjectId"]:

            return jsonify({
                "error": "Subject does not match consent."
            }), 403

        if c.model_id != data["modelId"]:

            return jsonify({
                "error": "Model does not match consent."
            }), 403

        if c.revoked or is_expired(c.expiry):

            return jsonify({
                "error": "Consent is revoked or expired."
            }), 403

        # ----------------------------------------------------
        # 3. Validate model
        # ----------------------------------------------------

        m = db.scalar(
            select(ModelRegistry).where(
                ModelRegistry.model_id == data["modelId"]
            )
        )

        if not m or not m.active:

            return jsonify({
                "error": "Model is not active."
            }), 400

        # ----------------------------------------------------
        # 4. Blockchain authorization check
        # ----------------------------------------------------

        provider_address = (
            get_provider_blockchain_address(
                session["username"]
            )
        )

        blockchain_authorized = (
            blockchain.can_infer(
                consent_id=c.consent_id,
                provider_address=provider_address,
                model_id=m.model_id,
                purpose=c.purpose,
            )
        )

        if not blockchain_authorized:

            return jsonify({
                "error": (
                    "Blockchain authorization failed. "
                    "Consent is not valid for this inference."
                )
            }), 403

        # ----------------------------------------------------
        # 5. Existing educational AI scoring model
        # ----------------------------------------------------

        score = (
            int(age > 50)
            + int(bp > 140)
            + int(cholesterol > 200)
        )

        label = (
            "HIGH_SCORE"
            if score >= 2
            else "LOW_SCORE"
        )

        receipt_id = new_id("R")

        output_digest = sha256(
            f"{c.consent_id}|"
            f"{m.model_id}|"
            f"{label}|"
            f"{secrets.token_hex(8)}"
        )

        # ----------------------------------------------------
        # 6. Record inference on blockchain
        # ----------------------------------------------------

        blockchain_result = (
            blockchain.record_inference(
                receipt_id=receipt_id,
                consent_id=c.consent_id,
                model_digest=m.model_digest,
                output_digest=output_digest,
            )
        )

        # ----------------------------------------------------
        # 7. Save audit in SQLite
        # ----------------------------------------------------

        audit = InferenceAudit(
            receipt_id=receipt_id,
            consent_id=c.consent_id,
            subject_id=c.subject_id,
            provider_username=session["username"],
            model_id=m.model_id,
            model_digest=m.model_digest,
            output_digest=output_digest,
            output_label=label,
            timestamp=now_utc(),
            blockchain_recorded=True,
        )

        db.add(audit)
        db.commit()
        db.refresh(audit)

        return jsonify({
            **audit_dict(audit),
            "score": score,
            "blockchain": {
                "transactionHash":
                    blockchain_result["tx_hash"],
                "blockNumber":
                    blockchain_result["block_number"],
            }
        }), 201


# ============================================================
# AUDIT API
# ============================================================

@app.get("/api/audits")
@require_role("ADMIN")
def audits():

    with SessionLocal() as db:

        rows = db.scalars(
            select(InferenceAudit).order_by(
                desc(InferenceAudit.timestamp)
            ).limit(25)
        ).all()

        return jsonify(
            [
                audit_dict(a)
                for a in rows
            ]
        )


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

@app.get("/api/stats")
@require_login
def stats():

    with SessionLocal() as db:

        return jsonify({
            "consents":
                db.scalar(
                    select(func.count(Consent.id))
                ),

            "models":
                db.scalar(
                    select(func.count(ModelRegistry.id))
                ),

            "audits":
                db.scalar(
                    select(func.count(InferenceAudit.id))
                ),
        })


# ============================================================
# ERROR HANDLER
# ============================================================

@app.errorhandler(Exception)
def handle_exception(exc):

    app.logger.exception(exc)

    if request.path.startswith("/api/"):

        return jsonify({
            "error": str(exc)
            or "Internal server error"
        }), 500

    return "Internal server error", 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=8080,
        debug=True
    )