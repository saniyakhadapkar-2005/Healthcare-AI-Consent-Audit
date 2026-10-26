# Java → Python conversion map

| Original Java/Spring component | Python replacement |
|---|---|
| Spring Boot application | `app.py` Flask application |
| Spring MVC controllers | Flask route functions |
| Spring Security | Flask session + role decorators |
| Spring Data JPA repositories | SQLAlchemy queries |
| H2 database | SQLite |
| JPA entities | SQLAlchemy ORM models |
| `HealthcareService` | Service logic implemented in `app.py` |
| BCrypt password encoder | Werkzeug password hashing |
| SHA-256 `MessageDigest` | Python `hashlib.sha256` |
| Thymeleaf/static web UI | Existing HTML/CSS/JS served by Flask |
| Solidity contract | Kept unchanged |
| Hardhat deployment | Kept unchanged |
| MetaMask/ethers.js dashboard | Kept unchanged |

## Important design decision

Only the **application backend** is converted to Python. Solidity cannot be "converted to Python" because the deployed smart contract is written in Solidity and executes on the EVM. Hardhat and the existing contract are therefore retained.

The Python backend currently mirrors the original Java backend's behavior rather than changing the project's business logic.
