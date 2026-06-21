## 2024-05-27 - [Desktop Companion App CORS & CSP Vulnerability]
**Vulnerability:** The .NET orchestrator had `AllowAnyOrigin()` CORS policy and the Tauri frontend had `csp: null`. This allowed any public website to make unauthorized requests to the local desktop orchestrator on `127.0.0.1` and left the frontend vulnerable to XSS and injection.
**Learning:** In local desktop companion apps, especially those binding to loopback for sidecar communication, wildcard CORS and missing CSPs are critical risks that can expose the local machine's services or file system to malicious sites visited in the browser.
**Prevention:** Always restrict CORS to the specific `localhost` or `tauri://localhost` origins used by the frontend, and ensure the Tauri frontend defines a strict Content Security Policy limiting connections and sources.

## 2024-05-28 - [Local API Hijacking via Sidecar Port]
**Vulnerability:** The .NET orchestrator binds to a local port and exposes REST APIs. Even with CORS restrictions to Tauri domains, a malicious process or DNS rebinding attack could potentially send requests directly to the bound localhost port.
**Learning:** Pure CORS and loopback binding are not sufficient to prevent unauthorized local processes from hijacking sidecar APIs, especially those handling file system access or licenses.
**Prevention:** Implement a strict IPC Secret Token mechanism where the frontend generates a secure random string on launch, passes it to the sidecar via CLI arguments, and includes it as a header (`X-IPC-Secret`) on all HTTP requests to validate authorization.

## 2024-05-29 - [Timing Attack in IPC Secret Validation]
**Vulnerability:** The .NET orchestrator used a standard string comparison (`providedSecret != ipcSecret`) to validate the `X-IPC-Secret` header, which is vulnerable to timing attacks. An attacker could theoretically guess the secret byte-by-byte by measuring the response time.
**Learning:** Security-sensitive string comparisons, such as secret tokens, should be done using constant-time comparisons to prevent timing side-channel attacks.
**Prevention:** Use `CryptographicOperations.FixedTimeEquals()` on the byte representation of strings when comparing secrets, ensuring to check the lengths first (as `FixedTimeEquals` requires arrays of the same length).
## 2025-02-27: Supabase PostgREST API Injection

*   **Vulnerability:** A `userId` passed from the request body was directly interpolated into a query string sent to the Supabase PostgREST API without validation or encoding. This allowed for potential query parameter injection, letting an attacker modify the query logic (e.g., adding `&status=eq.canceled`).
*   **Learning:** Never trust client-provided data, especially when constructing dynamic queries or API calls. Even internal API requests (like fetching from Supabase via `fetch`) need strict input sanitization.
*   **Prevention:** Always validate the format of parameters (e.g., using a strict Regex for UUIDs) and safely encode them using `encodeURIComponent()` before appending them to URLs.
## 2024-05-27: Missing Authentication on Local API Endpoints
* **Vulnerability**: Local FastAPI endpoints in the ML Service lacked authentication, meaning any user or malicious application running on the same machine could bypass the .NET orchestrator and interact with the AI pipeline directly, potentially executing resource exhaustion attacks (DOS) or extracting unauthorized data.
* **Learning**: Internal microservices running on `localhost` should still validate the authenticity of incoming requests, especially if they perform heavy computations or have access to sensitive capabilities.
* **Prevention**: Enforce authentication for all incoming traffic to local services using Inter-Process Communication (IPC) secrets. The main host application should generate or possess a secure secret, pass it to the sidecar during startup (via CLI or environment variables), and include it as an HTTP header on every request. The sidecar must validate this header using constant-time string comparison (`hmac.compare_digest`) before processing the request.
## 2025-02-27 - [Configuration Secret Leak via Placeholder Default]
**Vulnerability:** The .NET orchestrator `LicenseService` initialized `VITE_SUPABASE_URL` with a hardcoded fallback string (`https://placeholder-url.supabase.co`) if the environment variable was missing. This created a critical security risk where sensitive authentication credentials (JWTs) would be transmitted to an attacker-controllable domain if the environment was misconfigured.
**Learning:** Do not use hardcoded fallback strings for sensitive configuration parameters like API URLs or keys during environment variable initialization. Misconfigurations must fail securely rather than degrade to an insecure state.
**Prevention:** Explicitly throw an `InvalidOperationException` if required sensitive variables are missing to enforce fail-fast security, ensuring the application cannot start in an insecure or leaking state.
