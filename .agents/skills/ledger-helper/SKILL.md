---
name: ledger-helper
description: Assists the developer and the Antigravity local CLI agent in managing, building, testing, and debugging the Bank of Anthos Java LedgerWriter microservice.
---

# Ledger Helper Skill

This local developer skill equips the Antigravity agent (`agy`) with instructions and tasks to manage the Bank of Anthos `ledger-writer` Java service.

## 🛠️ Tasks & Commands

### 1. Run the Smoke Test
To verify codebase structural integrity, files, and standard directory setup, execute the built-in smoke test:
```bash
./.agents/skills/ledger-helper/scripts/smoke_test.sh
```

### 2. Build & Compile LedgerWriter
To compile and build the Java application, the agent or developer should run Maven compile from the `ledger-writer` directory:
```bash
mvn clean compile
```

### 3. Run Compliance Verification Tests
To run the full Spring Boot integration tests verifying compliance rules, run:
```bash
mvn test
```

### 4. Build Executable JAR
To package the project into a deployable Spring Boot JAR file, run:
```bash
mvn clean package -DskipTests
```

## 📋 Compliance Rule Guidelines

When executing a regulatory task (e.g., AML thresholds):
1. Locate the `LedgerValidationRule.java` utility or controller logic under the official package path `anthos.samples.bankofanthos.ledgerwriter`.
2. Ensure any transaction amount exceeding **$10,000** triggers `transaction.setFlaggedForAml(true)`.
3. Require `transaction.getRegulatoryPurposeCode()` to be present and non-blank; if missing, throw an `IllegalArgumentException` or validation error returning a `400 Bad Request`.
4. Log a structured regulatory warning using standard Spring Boot logging formats.
