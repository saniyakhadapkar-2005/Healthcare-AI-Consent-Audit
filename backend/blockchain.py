from pathlib import Path
import json
from web3 import Web3


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

CONTRACT_FILE = (
    PROJECT_DIR
    / "blockchain"
    / "artifacts"
    / "contracts"
    / "HealthcareConsentAudit.sol"
    / "HealthcareConsentAudit.json"
)

RPC_URL = "http://127.0.0.1:8545"

CONTRACT_ADDRESS = Web3.to_checksum_address(
    "0x5FbDB2315678afecb367f032d93F642f64180aa3"
)


class BlockchainService:

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))

        if not self.w3.is_connected():
            raise RuntimeError(
                "Cannot connect to Hardhat at http://127.0.0.1:8545. "
                "Make sure 'npm run node' is running."
            )

        if not CONTRACT_FILE.exists():
            raise FileNotFoundError(
                f"Contract ABI not found: {CONTRACT_FILE}"
            )

        with open(CONTRACT_FILE, "r", encoding="utf-8") as f:
            artifact = json.load(f)

        self.contract = self.w3.eth.contract(
            address=CONTRACT_ADDRESS,
            abi=artifact["abi"]
        )

        # Local Hardhat Account #0.
        # Educational prototype only.
        self.account = self.w3.eth.accounts[0]

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def to_bytes32(value: str) -> bytes:
        """
        Convert a normal string into deterministic bytes32.

        Used for:
        consent ID, subject ID, model ID and purpose.
        """
        return Web3.keccak(text=str(value))

    @staticmethod
    def digest_to_bytes32(value: str) -> bytes:
        """
        Convert a SHA-256 hexadecimal digest into exactly 32 bytes.

        If the value is not a valid 64-character hex digest,
        fall back to keccak(text=value).
        """
        if not value:
            return Web3.keccak(text="")

        cleaned = str(value).lower().removeprefix("0x")

        if len(cleaned) == 64:
            try:
                return bytes.fromhex(cleaned)
            except ValueError:
                pass

        return Web3.keccak(text=str(value))

    # ---------------------------------------------------------
    # Model registration
    # ---------------------------------------------------------

    def is_model_registered(self, model_id: str) -> bool:
        """
        Check whether a model is registered on the blockchain.
        """
        model_hash = self.to_bytes32(model_id)

        return self.contract.functions.registeredModels(
            model_hash
        ).call()

    def ensure_model_registered(self, model_id: str):
        """
        Register the model on-chain if it is not already registered.
        """
        if self.is_model_registered(model_id):
            return None

        return self.register_model(model_id)

    def register_model(self, model_id: str):
        model_hash = self.to_bytes32(model_id)

        tx = self.contract.functions.registerModel(
            model_hash
        ).transact({
            "from": self.account
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)

        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "block_number": receipt["blockNumber"],
        }

    # ---------------------------------------------------------
    # Consent
    # ---------------------------------------------------------

    def grant_consent(
        self,
        consent_id: str,
        subject_id: str,
        provider_address: str,
        model_id: str,
        purpose: str,
        expiry_timestamp: int,
    ):
        """
        Store consent on the Solidity contract.
        """

        tx = self.contract.functions.grantConsent(
            self.to_bytes32(consent_id),
            self.to_bytes32(subject_id),
            Web3.to_checksum_address(provider_address),
            self.to_bytes32(model_id),
            self.to_bytes32(purpose),
            int(expiry_timestamp),
        ).transact({
            "from": self.account
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)

        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "block_number": receipt["blockNumber"],
        }

    def revoke_consent(self, consent_id: str):
        """
        Revoke consent on the Solidity contract.
        """

        tx = self.contract.functions.revokeConsent(
            self.to_bytes32(consent_id)
        ).transact({
            "from": self.account
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)

        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "block_number": receipt["blockNumber"],
        }

    # ---------------------------------------------------------
    # Authorization
    # ---------------------------------------------------------

    def can_infer(
        self,
        consent_id: str,
        provider_address: str,
        model_id: str,
        purpose: str,
    ) -> bool:
        """
        Ask Solidity whether this inference is currently authorized.
        """

        return self.contract.functions.canInfer(
            self.to_bytes32(consent_id),
            Web3.to_checksum_address(provider_address),
            self.to_bytes32(model_id),
            self.to_bytes32(purpose),
        ).call()

    # ---------------------------------------------------------
    # AI inference audit
    # ---------------------------------------------------------

    def record_inference(
        self,
        receipt_id: str,
        consent_id: str,
        model_digest: str,
        output_digest: str,
    ):
        """
        Record the inference audit receipt on-chain.
        """

        tx = self.contract.functions.recordInference(
            self.to_bytes32(receipt_id),
            self.to_bytes32(consent_id),
            self.digest_to_bytes32(model_digest),
            self.digest_to_bytes32(output_digest),
        ).transact({
            "from": self.account
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)

        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "block_number": receipt["blockNumber"],
        }


# Single blockchain service used by Flask.
blockchain = BlockchainService()