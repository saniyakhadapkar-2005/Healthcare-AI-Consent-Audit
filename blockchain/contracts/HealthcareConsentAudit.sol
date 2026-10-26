// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * Educational prototype only.
 * Never store real patient records, diagnoses or other health data here.
 */
contract HealthcareConsentAudit {
    struct Consent {
        bytes32 subjectId;
        address provider;
        bytes32 modelId;
        bytes32 purpose;
        uint256 expiry;
        bool revoked;
        bool exists;
    }
    struct InferenceReceipt {
        bytes32 consentId;
        bytes32 subjectId;
        address provider;
        bytes32 modelId;
        bytes32 modelDigest;
        bytes32 outputDigest;
        uint256 timestamp;
        bool exists;
    }

    mapping(bytes32 => Consent) public consents;
    mapping(bytes32 => InferenceReceipt) public receipts;
    mapping(bytes32 => bool) public registeredModels;

    event ModelRegistered(bytes32 indexed modelId);
    event ConsentGranted(bytes32 indexed consentId, bytes32 indexed subjectId, address indexed provider,
        bytes32 modelId, bytes32 purpose, uint256 expiry);
    event ConsentRevoked(bytes32 indexed consentId);
    event InferenceRecorded(bytes32 indexed receiptId, bytes32 indexed consentId, bytes32 indexed subjectId,
        address provider, bytes32 modelId, bytes32 modelDigest, bytes32 outputDigest);

    function registerModel(bytes32 modelId) external {
        require(modelId != bytes32(0), "Invalid model");
        registeredModels[modelId] = true;
        emit ModelRegistered(modelId);
    }

    function grantConsent(bytes32 consentId, bytes32 subjectId, address provider,
        bytes32 modelId, bytes32 purpose, uint256 expiry) external {
        require(!consents[consentId].exists, "Consent already exists");
        require(subjectId != bytes32(0), "Invalid subject");
        require(provider != address(0), "Invalid provider");
        require(registeredModels[modelId], "Model not registered");
        require(expiry > block.timestamp, "Expiry must be future");
        consents[consentId] = Consent(subjectId, provider, modelId, purpose, expiry, false, true);
        emit ConsentGranted(consentId, subjectId, provider, modelId, purpose, expiry);
    }

    function revokeConsent(bytes32 consentId) external {
        require(consents[consentId].exists, "Consent not found");
        consents[consentId].revoked = true;
        emit ConsentRevoked(consentId);
    }

    function canInfer(bytes32 consentId, address provider, bytes32 modelId, bytes32 purpose)
        public view returns(bool) {
        Consent memory c=consents[consentId];
        return c.exists && !c.revoked && c.provider==provider && c.modelId==modelId &&
               c.purpose==purpose && c.expiry>=block.timestamp && registeredModels[modelId];
    }

    function recordInference(bytes32 receiptId, bytes32 consentId, bytes32 modelDigest, bytes32 outputDigest)
        external {
        require(!receipts[receiptId].exists, "Receipt already exists");
        Consent memory c=consents[consentId];
        require(canInfer(consentId,msg.sender,c.modelId,c.purpose),"Inference not authorized");
        receipts[receiptId]=InferenceReceipt(consentId,c.subjectId,msg.sender,c.modelId,
            modelDigest,outputDigest,block.timestamp,true);
        emit InferenceRecorded(receiptId,consentId,c.subjectId,msg.sender,c.modelId,modelDigest,outputDigest);
    }
}
