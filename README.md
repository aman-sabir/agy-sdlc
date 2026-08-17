# 🏦 Ledger Writer Service (`ledger-writer`)

[![Java](https://img.shields.io/badge/Java-17-orange.svg)](https://www.oracle.com/java/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.5.15-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![Build Status](https://img.shields.io/badge/build-passing-success.svg)]()

The **Ledger Writer** is a mission-critical Spring Boot microservice within the **Bank of Anthos** platform. It serves as the authoritative transactional ingestion gateway responsible for validating incoming funds movements, verifying sender balances, enforcing compliance checks (AML & regulatory codes), deduplicating requests, and committing records to the core ledger database.

---

## 📑 Table of Contents
- [Architecture & Transaction Flow](#architecture--transaction-flow)
- [API Reference](#api-reference)
- [Data Model](#data-model)
- [Environment Configuration](#environment-configuration)
- [Prerequisites & Development Setup](#prerequisites--development-setup)
- [Building and Testing](#building-and-testing)
- [Compliance & Security](#compliance--security)

---

## 🏛️ Architecture & Transaction Flow

```
   [ Client / Frontend / Transaction Generator ]
                        │
                        ▼ (POST /transactions)
            ┌───────────────────────┐
            │   LedgerWriter API    │
            └───────────┬───────────┘
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
 [1. Deduplication Cache]     [2. Input Validation]
 (Guava UUID Cache 1hr)       (10-digit Acct / 9-digit Route)
        │
        ▼ (If local route)
 [3. Balance Check] ─────────▶ [Balances API Service]
        │
        ▼
 [4. AML & Regulatory Flagging]
        │
        ▼
 [5. Ledger Persistence] ────▶ [PostgreSQL / H2 DB (TRANSACTIONS)]
```

### Core Responsibilities
1. **Idempotency & Replay Protection**: Guava in-memory cache stores request UUIDs for 1 hour to drop duplicate payloads.
2. **Syntactic & Logical Validation**: Verifies 10-digit account numbers, 9-digit routing numbers, positive amounts, and disallows self-transfers.
3. **Balance Verification**: For local transfers, issues an authenticated HTTP call to the Balances service before committing the transaction.
4. **Regulatory Auditing**: Populates AML flags (`flaggedForAml`) and regulatory purpose codes.
5. **Persistence**: Commits immutable entries to the `TRANSACTIONS` table.

---

## 📡 API Reference

### 1. Readiness Probe
* **Endpoint**: `GET /ready`
* **Response**: `200 OK` (`"ok"`)

### 2. Version Information
* **Endpoint**: `GET /version`
* **Response**: `200 OK` (e.g., `"1.0.0"`)

### 3. Create Transaction
* **Endpoint**: `POST /transactions`
* **Headers**: `Content-Type: application/json`
* **Request Body**:
```json
{
  "fromAccountNum": "1234567890",
  "fromRoutingNum": "123456789",
  "toAccountNum": "0987654321",
  "toRoutingNum": "123456789",
  "amount": 25000,
  "uuid": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "regulatoryPurposeCode": "RETAIL_PAYMENT",
  "flaggedForAml": false
}
```
* **Success Response (`201 CREATED`)**:
```json
{
  "transactionId": 1042,
  "fromAccountNum": "1234567890",
  "fromRoutingNum": "123456789",
  "toAccountNum": "0987654321",
  "toRoutingNum": "123456789",
  "amount": 25000,
  "timestamp": "2026-08-18T09:30:00.000+00:00",
  "flaggedForAml": false,
  "regulatoryPurposeCode": "RETAIL_PAYMENT",
  "status": "PROCESSED"
}
```
* **Error Responses**:
  * `400 Bad Request`: Validation failure (invalid numbers, self-transfer, non-positive amount, duplicate UUID, insufficient funds).
  * `500 Internal Server Error`: Downstream Balances service failure or database connectivity issue.

---

## 🗄️ Data Model

### Entity: `Transaction` (Table: `TRANSACTIONS`)
| Field | Type | DB Column | Notes |
|---|---|---|---|
| `transactionId` | `long` | `TRANSACTION_ID` | Primary Key, Auto-increment Identity |
| `fromAccountNum` | `String` | `FROM_ACCT` | 10-digit numeric account ID |
| `fromRoutingNum` | `String` | `FROM_ROUTE` | 9-digit numeric routing code |
| `toAccountNum` | `String` | `TO_ACCT` | 10-digit numeric account ID |
| `toRoutingNum` | `String` | `TO_ROUTE` | 9-digit numeric routing code |
| `amount` | `Integer` | `AMOUNT` | Value in integer cents ($1.00 = 100) |
| `timestamp` | `Date` | `TIMESTAMP` | Auto-generated creation timestamp |
| `flaggedForAml` | `Boolean` | `flagged_for_aml` | Set to `true` if transaction triggers AML threshold |
| `regulatoryPurposeCode` | `String` | `regulatory_purpose_code` | Transaction purpose classification code |
| `status` | `String` | `status` | Processing state (default: `"PROCESSED"`) |
| `requestUuid` | `String` | *Transient* | Client request UUID for deduplication |

---

## ⚙️ Environment Configuration

The application checks for required environment variables during bootstrap. If any mandatory variable is missing, the application will terminate.

| Variable | Required | Default / Fallback | Description |
|---|---|---|---|
| `VERSION` | **Yes** | — | Service release version exposed on `/version` |
| `PORT` | **Yes** | `8080` | HTTP port for the web server |
| `LOCAL_ROUTING_NUM` | **Yes** | `123456789` | Local Bank of Anthos routing code |
| `BALANCES_API_ADDR` | **Yes** | `localhost:8080` | Host and port for the Balances API |
| `SPRING_DATASOURCE_URL` | No | In-memory H2 | JDBC connection URL for PostgreSQL |
| `SPRING_DATASOURCE_USERNAME` | No | `sa` | Database user |
| `SPRING_DATASOURCE_PASSWORD` | No | `""` | Database password |
| `ENABLE_METRICS` | No | `true` | Enable Stackdriver/Cloud Monitoring metrics |
| `ENABLE_TRACING` | No | `false` | Enable distributed tracing via Spring Cloud GCP |

---

## 🚀 Prerequisites & Development Setup

### Prerequisites
* **Java 17 SDK** (Eclipse Temurin or OpenJDK)
* **Apache Maven 3.9+**

### Local Quickstart
1. Set the mandatory environment variables:
   ```bash
   export VERSION="1.0.0"
   export PORT="8080"
   export LOCAL_ROUTING_NUM="123456789"
   export BALANCES_API_ADDR="localhost:8080"
   ```
2. Run the Spring Boot application (uses in-memory H2 database by default):
   ```bash
   mvn spring-boot:run
   ```

---

## 🛠️ Building and Testing

* **Compile codebase**:
  ```bash
  mvn clean compile
  ```
* **Run unit and integration tests**:
  ```bash
  mvn test
  ```
* **Build executable JAR**:
  ```bash
  mvn clean package
  ```
* **Build container image via Jib**:
  ```bash
  mvn compile jib:build
  ```

---

## 🛡️ Compliance & Security Guardrails

* **Anti-Money Laundering (AML)**: Transactions exceeding $10,000 should have `flaggedForAml` enabled and require a valid `regulatoryPurposeCode`.
* **Zero Secrets in Code**: Database credentials and keys must be injected via environment variables or secret managers.
* **Zero PII Exposure**: Sensitive account numbers and transaction payloads are masked in high-level audit logs.
* **Resilience**: Integrated with Cloud Monitoring metrics, readiness probes, and graceful shutdown lifecycle hooks.
