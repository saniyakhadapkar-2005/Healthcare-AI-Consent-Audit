async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `HTTP ${response.status}`);
    }

    return response.json();
}


function esc(value) {
    return String(value ?? "").replace(
        /[&<>"']/g,
        function (char) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }[char];
        }
    );
}


/* =========================================================
   ROLE-BASED NAVIGATION
   ========================================================= */

async function setupRoleNavigation() {
    try {
        const user = await api("/api/me");
        const roles = user.roles || [];

        const consentNav = document.getElementById("consentNav");
        const inferenceNav = document.getElementById("inferenceNav");
        const modelsNav = document.getElementById("modelsNav");

        // Patient only
        if (consentNav && !roles.includes("ROLE_PATIENT")) {
            consentNav.style.display = "none";
        }

        // Provider only
        if (inferenceNav && !roles.includes("ROLE_PROVIDER")) {
            inferenceNav.style.display = "none";
        }

        // Admin only
        if (modelsNav && !roles.includes("ROLE_ADMIN")) {
            modelsNav.style.display = "none";
        }

    } catch (error) {
        console.error("Role navigation failed:", error);
    }
}


/* =========================================================
   DASHBOARD STATS
   ========================================================= */

async function loadStats() {
    try {
        const stats = await api("/api/stats");

        const s1 = document.getElementById("s1");
        const s2 = document.getElementById("s2");
        const s3 = document.getElementById("s3");

        if (s1) {
            s1.textContent = stats.consents;
        }

        if (s2) {
            s2.textContent = stats.models;
        }

        if (s3) {
            s3.textContent = stats.audits;
        }

    } catch (error) {
        console.error("loadStats failed:", error);
    }
}


/* =========================================================
   LOAD ACTIVE MODELS
   ========================================================= */

async function loadModels(selectId = "modelId") {
    const select = document.getElementById(selectId);

    if (!select) {
        console.warn(`Element #${selectId} not found.`);
        return;
    }

    try {
        select.innerHTML = `
            <option value="">Loading models...</option>
        `;

        console.log("Loading models from /api/models...");

        const models = await api("/api/models");

        console.log("Models received:", models);

        if (!Array.isArray(models) || models.length === 0) {
            select.innerHTML = `
                <option value="">No active models available</option>
            `;
            return;
        }

        select.innerHTML = "";

        models.forEach(function (model) {
            const option = document.createElement("option");

            option.value = model.modelId;

            option.textContent =
                `${model.modelId} · v${model.version}`;

            select.appendChild(option);
        });

        console.log(
            `Successfully loaded ${models.length} model(s).`
        );

    } catch (error) {
        console.error("loadModels failed:", error);

        select.innerHTML = `
            <option value="">Unable to load models</option>
        `;
    }
}


/* =========================================================
   LOAD CONSENTS
   ========================================================= */

async function loadConsents() {
    const element = document.getElementById("consentList");

    if (!element) {
        return;
    }

    try {
        const consents = await api("/api/consents");

        if (!Array.isArray(consents) || consents.length === 0) {

            element.innerHTML = `
                <div class="empty">
                    No consent records yet.
                    <br>
                    <span class="muted">
                        Create a scoped authorization to get started.
                    </span>
                </div>
            `;

            return;
        }

        element.innerHTML = consents.map(function (consent) {

            return `
                <div class="item">

                    <div class="item-title">

                        ${esc(consent.consentId)}

                        <span class="pill">
                            ${consent.revoked ? "REVOKED" : "ACTIVE"}
                        </span>

                    </div>

                    <div>
                        ${esc(consent.subjectId)}
                        →
                        ${esc(consent.providerUsername)}
                    </div>

                    <div class="muted">
                        ${esc(consent.modelId)}
                        ·
                        ${esc(consent.purpose)}
                    </div>

                    ${
                        consent.revoked
                            ? ""
                            : `
                                <button
                                    class="primary"
                                    style="margin-top:9px"
                                    onclick="revokeConsent('${esc(consent.consentId)}')"
                                >
                                    Revoke
                                </button>
                              `
                    }

                </div>
            `;

        }).join("");

    } catch (error) {

        console.error("loadConsents failed:", error);

        element.innerHTML = `
            <p class="error">
                Unable to load consents.
            </p>
        `;
    }
}


/* =========================================================
   GRANT CONSENT
   ========================================================= */

async function grantConsent(event) {

    event.preventDefault();

    const providerInput =
        document.getElementById("providerUsername");

    const subjectInput =
        document.getElementById("subjectId");

    const modelInput =
        document.getElementById("modelId");

    const purposeInput =
        document.getElementById("purpose");

    const hoursInput =
        document.getElementById("hours");

    const message =
        document.getElementById("grantMsg");

    try {

        const result = await api("/api/consents", {

            method: "POST",

            body: JSON.stringify({

                providerUsername:
                    providerInput.value,

                subjectId:
                    subjectInput.value,

                modelId:
                    modelInput.value,

                purpose:
                    purposeInput.value,

                expirySeconds:
                    Number(hoursInput.value) * 3600
            })
        });


        message.innerHTML = `
            <p class="ok">
                Consent created:
                <code>${esc(result.consentId)}</code>
            </p>
        `;


        await loadConsents();


    } catch (error) {

        console.error(
            "grantConsent failed:",
            error
        );

        message.innerHTML = `
            <p class="error">
                ${esc(error.message)}
            </p>
        `;
    }
}


/* =========================================================
   REVOKE CONSENT
   ========================================================= */

async function revokeConsent(consentId) {

    try {

        await api(
            "/api/consents/" +
            encodeURIComponent(consentId) +
            "/revoke",
            {
                method: "POST"
            }
        );

        await loadConsents();

    } catch (error) {

        console.error(
            "revokeConsent failed:",
            error
        );

        alert(error.message);
    }
}


/* =========================================================
   AI INFERENCE
   ========================================================= */

async function runInference(event) {

    event.preventDefault();

    const consent =
        document.getElementById("inferConsent");

    const subject =
        document.getElementById("inferSubject");

    const model =
        document.getElementById("inferModel");

    const ageInput =
        document.getElementById("age");

    const bpInput =
        document.getElementById("bp");

    const cholesterolInput =
        document.getElementById("chol");

    const resultBox =
        document.getElementById("inferResult");


    try {

        const result = await api(
            "/api/inference",
            {
                method: "POST",

                body: JSON.stringify({

                    consentId:
                        consent.value,

                    subjectId:
                        subject.value,

                    modelId:
                        model.value,

                    age:
                        Number(ageInput.value),

                    bloodPressure:
                        Number(bpInput.value),

                    cholesterol:
                        Number(cholesterolInput.value)
                })
            }
        );


        resultBox.innerHTML = `

            <div class="result-box">

                <div class="item-title ok">
                    ✓ INFERENCE ALLOWED
                </div>

                <p>
                    Output:
                    <b>${esc(result.outputLabel)}</b>
                </p>

                <p>
                    Receipt:
                    <code>${esc(result.receiptId)}</code>
                </p>

                <p>
                    Model digest:
                    <code>${esc(result.modelDigest)}</code>
                </p>

                <p>
                    Output digest:
                    <code>${esc(result.outputDigest)}</code>
                </p>

            </div>
        `;


    } catch (error) {

        console.error(
            "runInference failed:",
            error
        );

        resultBox.innerHTML = `

            <div class="item">

                <p class="error">
                    ✕ INFERENCE REJECTED
                </p>

                <p>
                    ${esc(error.message)}
                </p>

            </div>
        `;
    }
}


/* =========================================================
   LOAD ALL MODELS - ADMIN
   ========================================================= */

async function loadAllModels() {

    const element =
        document.getElementById("modelList");

    if (!element) {
        return;
    }

    try {

        const models =
            await api("/api/models/all");


        element.innerHTML = `

            <div class="table-wrap">

                <table>

                    <tr>
                        <th>ID</th>
                        <th>Version</th>
                        <th>Digest</th>
                        <th>Status</th>
                    </tr>

                    ${
                        models.map(function (model) {

                            return `

                                <tr>

                                    <td>
                                        ${esc(model.modelId)}
                                    </td>

                                    <td>
                                        ${esc(model.version)}
                                    </td>

                                    <td class="mono">
                                        ${esc(model.modelDigest)}
                                    </td>

                                    <td>
                                        ${
                                            model.active
                                                ? "ACTIVE"
                                                : "INACTIVE"
                                        }
                                    </td>

                                </tr>
                            `;

                        }).join("")
                    }

                </table>

            </div>
        `;


    } catch (error) {

        console.error(
            "loadAllModels failed:",
            error
        );

        element.innerHTML = `
            <p class="error">
                Admin access required.
            </p>
        `;
    }
}


/* =========================================================
   REGISTER MODEL - ADMIN
   ========================================================= */

async function registerModel(event) {

    event.preventDefault();

    const modelId =
        document.getElementById("newModelId");

    const version =
        document.getElementById("newVersion");

    const description =
        document.getElementById("newDescription");

    const message =
        document.getElementById("modelMsg");


    try {

        await api(
            "/api/models",
            {
                method: "POST",

                body: JSON.stringify({

                    modelId:
                        modelId.value,

                    version:
                        version.value,

                    description:
                        description.value
                })
            }
        );


        message.innerHTML = `
            <p class="ok">
                Model registered successfully.
            </p>
        `;


        await loadAllModels();


    } catch (error) {

        console.error(
            "registerModel failed:",
            error
        );

        message.innerHTML = `
            <p class="error">
                ${esc(error.message)}
            </p>
        `;
    }
}


/* =========================================================
   PAGE INITIALIZATION
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "MedChain frontend initialized."
        );


        // Role-based navigation
        setupRoleNavigation();


        // Consent page
        if (
            document.getElementById("grantForm")
        ) {

            loadModels();

            loadConsents();
        }


        // Admin models page
        if (
            document.getElementById("modelList")
        ) {

            loadAllModels();
        }


        // Dashboard statistics
        if (
            document.getElementById("s1") ||
            document.getElementById("s2") ||
            document.getElementById("s3")
        ) {

            loadStats();
        }

    }
);