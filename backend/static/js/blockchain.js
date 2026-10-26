/*
 * ============================================================
 * MEDCHAIN - BLOCKCHAIN PAGE
 * ============================================================
 *
 * Responsibilities:
 *
 * 1. Connect MetaMask
 * 2. Verify Hardhat network
 * 3. Display connected wallet
 * 4. Display deployed smart contract address
 * 5. Detect MetaMask account/network changes
 * 6. Load role-based quick-action buttons
 *
 * Blockchain:
 * Hardhat Local Network
 * Chain ID: 31337
 *
 * Smart Contract:
 * HealthcareConsentAudit
 * ============================================================
 */


/* ============================================================
   CONFIGURATION
   ============================================================ */

const HARDHAT_CHAIN_ID = 31337;

const CONTRACT_ADDRESS =
    "0x5FbDB2315678afecb367f032d93F642f64180aa3";


/* ============================================================
   SMART CONTRACT ABI
   ============================================================ */

const ABI = [

    "function registeredModels(bytes32) view returns (bool)",

    "function consents(bytes32) view returns (bytes32,address,bytes32,bytes32,uint256,bool,bool)"

];


/* ============================================================
   CONNECT META MASK
   ============================================================ */

async function connectChain() {

    const statusElement =
        document.getElementById("chainStatus");

    const walletElement =
        document.getElementById("walletAddress");

    const contractElement =
        document.getElementById("contractAddress");


    try {

        /*
         * Check whether MetaMask exists.
         */

        if (!window.ethereum) {

            throw new Error(
                "MetaMask is not installed. Please install MetaMask."
            );

        }


        /*
         * Create Ethers BrowserProvider.
         *
         * This connects the browser to MetaMask.
         */

        const provider =
            new ethers.BrowserProvider(
                window.ethereum
            );


        /*
         * Ask MetaMask for account permission.
         */

        const accounts =
            await provider.send(
                "eth_requestAccounts",
                []
            );


        /*
         * Make sure an account exists.
         */

        if (
            !accounts ||
            accounts.length === 0
        ) {

            throw new Error(
                "No MetaMask account connected."
            );

        }


        /*
         * Get the current blockchain network.
         */

        const network =
            await provider.getNetwork();


        const chainId =
            Number(network.chainId);


        /*
         * Display wallet address.
         */

        walletElement.textContent =
            accounts[0];


        /*
         * Always show the deployed contract.
         */

        contractElement.textContent =
            CONTRACT_ADDRESS;


        /*
         * Check whether the connected
         * network is Hardhat.
         */

        if (
            chainId !== HARDHAT_CHAIN_ID
        ) {

            statusElement.innerHTML = `
                <span class="error">
                    Wrong network
                </span>
                · Chain ID ${chainId}
            `;

            return;

        }


        /*
         * Correct Hardhat network.
         */

        statusElement.innerHTML = `
            <span class="ok">
                Connected
            </span>
            · Chain ID ${chainId}
        `;


        console.log(
            "MetaMask connected successfully."
        );

        console.log(
            "Wallet:",
            accounts[0]
        );

        console.log(
            "Chain ID:",
            chainId
        );

        console.log(
            "Contract:",
            CONTRACT_ADDRESS
        );

    }


    catch (error) {

        console.error(
            "MetaMask connection failed:",
            error
        );


        statusElement.innerHTML = `
            <span class="error">
                ${escapeHtml(error.message)}
            </span>
        `;


        walletElement.textContent =
            "Not connected";

    }

}


/* ============================================================
   ESCAPE HTML
   ============================================================ */

function escapeHtml(value) {

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


/* ============================================================
   ROLE-BASED QUICK ACTIONS
   ============================================================ */

async function setupRoleButtons() {

    const container =
        document.getElementById("roleButtons");


    /*
     * Stop if the element does not exist.
     */

    if (!container) {

        return;

    }


    try {

        /*
         * Get currently logged-in user.
         */

        const response =
            await fetch("/api/me");


        if (!response.ok) {

            throw new Error(
                "Unable to load user role."
            );

        }


        const data =
            await response.json();


        /*
         * Backend returns roles such as:
         *
         * ROLE_PATIENT
         * ROLE_PROVIDER
         * ROLE_ADMIN
         */

        const roles =
            data.roles || [];


        /*
         * Clear loading message.
         */

        container.innerHTML = "";


        /* ----------------------------------------------------
           PATIENT
           ---------------------------------------------------- */

        if (
            roles.includes("ROLE_PATIENT")
        ) {

            container.innerHTML += `

                <a
                    href="/consent"
                    class="primary"
                >
                    Manage Consent
                </a>

            `;

        }


        /* ----------------------------------------------------
           PROVIDER
           ---------------------------------------------------- */

        if (
            roles.includes("ROLE_PROVIDER")
        ) {

            container.innerHTML += `

                <a
                    href="/inference"
                    class="primary"
                >
                    Run AI Inference
                </a>

            `;

        }


        /* ----------------------------------------------------
           ADMIN
           ---------------------------------------------------- */

        if (
            roles.includes("ROLE_ADMIN")
        ) {

            container.innerHTML += `

                <a
                    href="/admin/models"
                    class="primary"
                >
                    Manage Models
                </a>

            `;

        }


        /*
         * If no recognized role exists.
         */

        if (
            container.innerHTML.trim() === ""
        ) {

            container.innerHTML = `

                <span class="muted">
                    No role-specific actions available.
                </span>

            `;

        }

    }


    catch (error) {

        console.error(
            "Role buttons failed:",
            error
        );


        container.innerHTML = `

            <span class="error">
                Unable to load role actions.
            </span>

        `;

    }

}


/* ============================================================
   METAMASK ACCOUNT CHANGE
   ============================================================ */

if (window.ethereum) {

    window.ethereum.on(
        "accountsChanged",
        function (accounts) {

            const walletElement =
                document.getElementById(
                    "walletAddress"
                );


            const statusElement =
                document.getElementById(
                    "chainStatus"
                );


            /*
             * User disconnected wallet.
             */

            if (
                !accounts ||
                accounts.length === 0
            ) {

                walletElement.textContent =
                    "Not connected";

                statusElement.textContent =
                    "Not connected";

                return;

            }


            /*
             * Update wallet.
             */

            walletElement.textContent =
                accounts[0];


            /*
             * Re-check network.
             */

            connectChain();

        }
    );


    /* ========================================================
       METAMASK NETWORK CHANGE
       ======================================================== */

    window.ethereum.on(
        "chainChanged",
        function () {

            /*
             * Re-check the connection
             * after network changes.
             */

            connectChain();

        }
    );

}


/* ============================================================
   PAGE INITIALIZATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    async function () {

        console.log(
            "MedChain Blockchain page initialized."
        );


        // Load role-based buttons
        setupRoleButtons();


        /*
         * Check whether MetaMask is installed.
         */
        if (!window.ethereum) {

            console.log(
                "MetaMask not detected."
            );

            return;
        }


        /*
         * Check whether MetaMask is ALREADY connected.
         *
         * eth_accounts does NOT open a popup.
         */
        try {

            const accounts =
                await window.ethereum.request({
                    method: "eth_accounts"
                });


            /*
             * If an account is already connected,
             * automatically verify the network.
             */
            if (
                accounts &&
                accounts.length > 0
            ) {

                console.log(
                    "Existing MetaMask connection detected."
                );

                await connectChain();

            }

        }

        catch (error) {

            console.error(
                "Unable to detect MetaMask connection:",
                error
            );

        }

    }
);