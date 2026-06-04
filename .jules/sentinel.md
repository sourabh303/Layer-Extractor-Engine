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
## 2024-05-XX Arbitrary File Write via Path Traversal
* **Vulnerability:** Path traversal (`../`) in the `ml-service` vectorize endpoint allowed arbitrary file write by passing unsanitized absolute or relative paths to file writing functions.
* **Learning:** Validating paths with `os.path.commonpath` can be brittle and break API contracts if clients don't know the exact server path. Using `os.path.basename()` to extract only the filename completely mitigates directory traversal attacks while remaining robust.
* **Prevention:** Always use `os.path.basename()` on user-supplied paths intended for saving files, rather than trusting absolute paths or doing directory containment checks when not strictly needed.
