# 10-minute live demo checklist

1. Start Hardhat:
   `cd blockchain && npm install && npm run node`
2. Deploy:
   `npm run deploy`
3. Start Spring Boot:
   `cd backend && mvn spring-boot:run`
4. Open:
   `http://localhost:8080/login`
5. Patient login: `patient / patient123`
6. Grant consent:
   Provider = provider
   Subject = SYNTHETIC_PATIENT_001
   Model = MODEL_V1
   Purpose = NON_CLINICAL_SCORING
7. Logout → Provider login: `provider / provider123`
8. Copy the consent ID into AI Inference and run the matching synthetic values.
9. Show `HIGH_SCORE`/`LOW_SCORE`, receipt ID, model digest and output digest.
10. Demonstrate rejection by using a different model or subject.
11. Patient logs in and revokes consent.
12. Provider retries → rejected.
13. Admin login: `admin / admin123`
14. Show model registry and audit information.
15. Open Blockchain page and connect MetaMask to Hardhat Localhost.

For a stronger blockchain demonstration, also execute the Solidity tests:
`cd blockchain && npm test`
