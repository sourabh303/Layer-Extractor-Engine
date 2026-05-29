## 2024-05-27 - [Desktop Companion App CORS & CSP Vulnerability]
**Vulnerability:** The .NET orchestrator had `AllowAnyOrigin()` CORS policy and the Tauri frontend had `csp: null`. This allowed any public website to make unauthorized requests to the local desktop orchestrator on `127.0.0.1` and left the frontend vulnerable to XSS and injection.
**Learning:** In local desktop companion apps, especially those binding to loopback for sidecar communication, wildcard CORS and missing CSPs are critical risks that can expose the local machine's services or file system to malicious sites visited in the browser.
**Prevention:** Always restrict CORS to the specific `localhost` or `tauri://localhost` origins used by the frontend, and ensure the Tauri frontend defines a strict Content Security Policy limiting connections and sources.

## 2024-05-29 - [IPC Sidecar Hijacking Vulnerability]
**Vulnerability:** The .NET Orchestrator spawned by Tauri did not implement IPC secrets. Even with localhost binding and CORS, it was vulnerable to DNS rebinding or other local processes calling the sidecar's `/api/*` endpoints directly without authorization.
**Learning:** For a Sidecar architecture relying on local HTTP servers, local host binding and CORS are insufficient. A shared secret (IPC token) generated dynamically by the parent process and required on all requests is mandatory to ensure requests actually originated from the authenticated frontend.
**Prevention:** Implement an `X-IPC-Secret` token generated cryptographically in Rust during launch, passed via CLI argument to the Sidecar, and enforced via an ASP.NET Core middleware for all `/api` traffic.
