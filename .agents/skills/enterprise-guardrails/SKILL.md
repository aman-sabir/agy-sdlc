---
name: enterprise-guardrails
description: Enforces secure coding practices, dependency vetting, structured logging, safe error handling, and regulatory compliance standards for all generated code.
---

# Enterprise Guardrails Skill

This skill enforces critical enterprise guardrails to ensure that all generated code is secure, reliable, maintainable, and compliant with standard enterprise policies.

## Security Guardrails

### 1. No Hardcoded Secrets
*   **Rule**: Never hardcode API keys, passwords, tokens, database credentials, encryption keys, or certificates.
*   **Action**: Use environment variables, secure configurations, or enterprise secret management services (such as Google Cloud Secret Manager).
*   **Example (Violating)**:
    ```java
    String dbPassword = "superSecretPassword123"; // VIOLATION
    ```
*   **Example (Compliant)**:
    ```java
    String dbPassword = System.getenv("DB_PASSWORD"); // COMPLIANT
    ```

### 2. PII & Sensitive Data Protection
*   **Rule**: Never log, expose, or store unencrypted Personally Identifiable Information (PII) or sensitive personal/financial data (such as SSNs, credit card numbers, or full tax IDs).
*   **Action**: Mask, tokenize, or encrypt sensitive data before storing or printing to logs.

---

## Dependency & Third-Party Code Guardrails

### 1. Approved Dependencies Only
*   **Rule**: Do not pull in arbitrary third-party libraries or unverified packages. Use only established, enterprise-approved, and vulnerability-scanned dependencies.
*   **Action**: Check existing dependency configuration files (`pom.xml`, `requirements.txt`, `package.json`) and strictly follow existing project dependency definitions.

### 2. Version Locking
*   **Rule**: Always lock dependency versions to avoid downstream supply chain vulnerabilities or unexpected breaking changes.

---

## Logging & Observability Guardrails

### 1. Structured Logging
*   **Rule**: Use structured logging (JSON or standard log framework layouts like Slf4j/Logback or Python standard logging) to support centralized log analysis.
*   **Action**: Avoid `System.out.println` or raw stdout prints in production code. Always use standard logger instances at appropriate levels (`INFO`, `WARN`, `ERROR`, `DEBUG`).

### 2. Safe Logging
*   **Rule**: Ensure logs never contain credentials, session tokens, or PII.

---

## Error Handling & Resiliency

### 1. Graceful Error Handling
*   **Rule**: All public interfaces and API endpoints must handle exceptions gracefully.
*   **Action**: Return clean, user-friendly error messages with proper HTTP status codes. Never leak raw stack traces or internal backend implementation details to the client.

### 2. Retry and Circuit Breaking
*   **Rule**: Integrate timeouts, retries, and circuit breakers for external service integrations to avoid cascading failures.
