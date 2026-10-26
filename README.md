# Healthcare AI Consent and Inference Audit System

A privacy-aware healthcare prototype that combines Artificial Intelligence (AI), Python, and Blockchain to manage patient consent, control access to AI inference, and maintain verifiable audit records.

## Overview

Healthcare AI applications may process sensitive patient information. It is important to ensure that healthcare providers access information only with appropriate permission and that AI inference activities can be audited.

The **Healthcare AI Consent and Inference Audit System** demonstrates how blockchain technology can support consent management, provider authorization, and AI auditability.

The application combines a Python backend, an SQLite database, an off-chain AI scoring component, and a local Ethereum-compatible blockchain powered by Hardhat.

The system is designed as an academic prototype using synthetic or pseudonymous data. Raw healthcare information is kept off-chain rather than stored directly on the blockchain.

## Key Features

- **Patient Consent Management:** Supports granting and managing consent for authorized healthcare AI activities.
- **Provider Authorization:** Restricts access according to the configured provider and consent permissions.
- **Consent Revocation:** Supports withdrawing consent and checking whether consent remains valid.
- **Consent Expiry Validation:** Helps prevent inference using expired consent.
- **AI Inference:** Demonstrates an off-chain scoring component using synthetic inputs.
- **Model Registry:** Supports checking whether an AI model is registered and active.
- **Blockchain Audit Trail:** Records consent and inference-related audit evidence on a local blockchain.
- **Inference Receipts:** Supports auditable records associated with inference activities.
- **Privacy-Aware Design:** Keeps detailed application records and raw healthcare inputs off-chain.
- **Role-Based Interface:** Provides role-specific workflows for patients, providers, and administrators.

> Note: These features describe the intended project functionality. Verify each workflow against the running application before presenting it as fully tested.

## Problem Statement

Traditional healthcare applications often rely on centralized databases to store consent information and access logs. These records may be modified by authorized database operators, making independent verification difficult.

This project explores how blockchain-backed audit records can improve the traceability of healthcare AI activities while keeping sensitive information outside the blockchain.

The system focuses on three questions:

1. Has the patient provided valid consent?
2. Is the requesting provider authorized to perform the intended AI inference?
3. Can the consent and inference activity be audited afterward?

## Project Objectives

- Develop a healthcare AI consent management prototype.
- Demonstrate provider-specific authorization.
- Validate consent status, expiry, and revocation.
- Integrate an off-chain AI scoring component.
- Use a Solidity smart contract to maintain blockchain audit evidence.
- Connect the Python backend to a local blockchain through Web3.py.
- Keep raw healthcare information off-chain.
- Demonstrate how blockchain can improve auditability and traceability.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Blockchain | Hardhat local Ethereum-compatible network |
| Smart Contracts | Solidity |
| Blockchain Integration | Web3.py |
| Database | SQLite |
| AI Component | Off-chain AI/rule-based scoring |
| Frontend | Browser-based application interface |
| Version Control | Git and GitHub |

## System Architecture

```text
              PATIENT / HEALTHCARE PROVIDER
                           |
                           v
                Browser-Based Interface
                           |
                           v
                   Python Flask API
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
       Consent and      SQLite       AI Inference
       Authorization    Database     Component
             |             |             |
             +-------------+-------------+
                           |
                           v
                    Web3.py Client
                           |
                           v
                 Hardhat Local Network
                           |
                           v
                   Solidity Contract
                           |
                           v
                Blockchain Audit Evidence
```

### Architecture Explanation

**1. Frontend**

Provides the interface through which patients manage consent and authorized providers access permitted AI functionality.

**2. Python Backend**

Handles application requests, consent validation, authorization checks, AI inference requests, and blockchain integration.

**3. SQLite Database**

Stores application records off-chain, such as user information and detailed application data.

**4. AI Inference Component**

Processes permitted synthetic inputs and produces a demonstration score or result outside the blockchain.

**5. Web3.py**

Connects the Python backend to the local Ethereum-compatible network and communicates with the deployed smart contract.

**6. Solidity Smart Contract**

Provides blockchain-based functionality for consent and audit-related operations according to the implemented contract logic.

**7. Hardhat**

Runs the local blockchain network used for development and demonstration.

## How the System Works

The intended workflow is:

1. A patient registers or logs in.
2. The patient grants consent for a specified provider and permitted AI activity.
3. The application records the consent information.
4. The provider logs in and requests an authorized AI inference.
5. The backend validates the relevant consent and authorization conditions.
6. If the checks pass, the off-chain AI component processes the permitted synthetic input.
7. The application creates an inference-related audit record.
8. Blockchain evidence can be inspected through the audit interface.
9. The patient can revoke consent.
10. Subsequent inference requests should be rejected when the applicable consent is no longer valid.

Actual behavior depends on the deployed smart contract and backend implementation.

## Privacy and Security Considerations

Privacy is a central design consideration in this project.

- **Off-chain data storage:** Raw healthcare inputs and detailed application records are kept outside the blockchain.
- **Consent validation:** Access decisions should consider the patient's consent and its current status.
- **Provider restrictions:** Provider access should be limited to the permissions configured for that provider.
- **Auditability:** Blockchain transactions can provide evidence that particular audit-related operations occurred.
- **Synthetic data:** The prototype is intended for development and academic demonstration, not real patient data.
- **Credential protection:** Passwords, private keys, tokens, and environment secrets must not be committed to a public repository.

Blockchain auditability does not automatically guarantee complete application security or regulatory compliance.

## Project Structure

```text
healthcare-ai-consent-audit-full/
|
|-- backend/
|   `-- Python backend and application files
|
|-- blockchain/
|   `-- Hardhat and smart contract project files
|
|-- data/
|   `-- Project data files
|
|-- DEMO_CHECKLIST.md
|-- Healthcare_AI_Consent_Audit_Project_Presentation.pptx
|-- Healthcare_AI_Consent_Audit_Project_Report.docx
|-- README.md
`-- .gitignore
```

This is a high-level overview. Refer to the actual files in each folder for the exact implementation.

## Prerequisites

Install the following before running the project:

- Python 3
- Node.js and npm
- Git
- A supported Python environment
- Dependencies listed in the project's Python requirements file, if provided
- Dependencies listed in `blockchain/package.json`

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/saniyakhadapkar-2005/Healthcare-AI-Consent-Audit.git
```

Navigate into the project directory:

```bash
cd Healthcare-AI-Consent-Audit
```

### 2. Set Up the Python Backend

Open a terminal in the project root and navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

Install the required dependencies using the project's requirements file, if available:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not present, install the dependencies specified by the project documentation instead.

### 3. Set Up the Blockchain

Open a **second terminal** and navigate to the blockchain directory:

```bash
cd path\to\Healthcare-AI-Consent-Audit\blockchain
```

Install the Node.js dependencies:

```bash
npm install
```

Inspect the available scripts in `package.json` before starting the local network or deploying the smart contract.

Start the Hardhat node using the script configured by the project. For example, if the package defines a `node` script:

```bash
npm run node
```

Keep the terminal running.

**Important:** Starting a Hardhat node does not automatically deploy the smart contract. Deploy the contract using the project's deployment script and ensure that the backend uses the correct contract address and ABI for the active local network.

### 4. Start the Backend

Open another terminal and navigate to the backend directory.

Activate the virtual environment if needed, then start the application:

```bash
python app.py
```

If the backend reports that it cannot connect to Hardhat, check that the local blockchain is running and that the RPC URL matches the backend configuration.

If a contract-call error occurs, verify that the contract has been deployed to the current network and that the backend is configured with the correct address and ABI.

### 5. Open the Application

Open the local application URL configured by the project.

For a local development setup, the interface may be available at:

```text
http://127.0.0.1:8080
```

Use this address only if the frontend server is running on port 8080. Otherwise, use the URL configured by your application.

## Suggested Testing Workflow

Use synthetic test data and verify the following scenarios:

| Test | Expected Behavior |
|---|---|
| Valid consent | An authorized request can proceed when all checks pass |
| Missing consent | The request is rejected |
| Revoked consent | Further protected inference is rejected |
| Expired consent | Further protected inference is rejected |
| Unauthorized provider | Access is rejected |
| Inactive or unregistered model | Inference is rejected where the implemented checks require it |
| Audit inspection | Available transaction and audit evidence can be reviewed |

Run these tests against the actual application before reporting the results as passed.

## Limitations

- This is an academic prototype, not a production healthcare platform.
- The project uses synthetic or pseudonymous data.
- The AI component is intended for demonstration and is not clinically validated.
- The local Hardhat network is for development and testing.
- Blockchain records do not replace secure application authentication, access controls, or database protection.
- Production deployment would require additional security testing, privacy review, key management, monitoring, and compliance assessment.

## Future Enhancements

- Integrate a clinically validated model for an appropriately reviewed research setting.
- Add comprehensive automated tests for consent and authorization.
- Improve authentication and session management.
- Add more detailed audit reporting and transaction verification.
- Improve error handling and deployment automation.
- Add monitoring for failed authorization attempts.
- Evaluate scalability and performance under controlled test conditions.

## Academic Use and Disclaimer

This project demonstrates concepts in Artificial Intelligence, Blockchain, smart contracts, consent management, and privacy-aware software design.

It is intended for educational and research purposes only. It must not be used to make real clinical decisions or to store real patient information without appropriate security, privacy, and regulatory safeguards.

## Author

**Saniya Khadapkar**

M.Sc. Artificial Intelligence  
Project: Healthcare AI Consent and Inference Audit

## Repository

GitHub: https://github.com/saniyakhadapkar-2005/Healthcare-AI-Consent-Audit


## Screenshorts

1. login page
   
<img width="1023" height="907" alt="LOGIN_PAGE" src="https://github.com/user-attachments/assets/e26352db-d275-4a74-9c03-aea178c385a8" />

2.Patient Dashboard

<img width="1600" height="928" alt="dashboard" src="https://github.com/user-attachments/assets/75f7c16e-c702-4267-8692-efee6ad824c9" />


3.AI Inference 

<img width="1433" height="923" alt="PATIENT_AI_INFERENCE" src="https://github.com/user-attachments/assets/ffbe6337-b57b-47d8-8148-d4aa221c9d4e" />

4.Consent Management 

<img width="1497" height="922" alt="Consent Management" src="https://github.com/user-attachments/assets/38c6a5da-8136-433d-8513-6fad443bcbb4" />

5.Blockchain Audit Page 

<img width="1385" height="885" alt="BLOCKCHAIN_DASHBOARD" src="https://github.com/user-attachments/assets/4fa04c36-5ef1-47cc-8320-e883c4691732" />



