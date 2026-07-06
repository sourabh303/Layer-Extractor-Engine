## 2024-05-24 - [Fix PostgREST API Injection in LicenseService]
**Vulnerability:** PostgREST API Injection via unsanitized `userId` in C# `LicenseService.cs`.
**Learning:** Dynamic variables interpolated directly into URLs for Supabase REST API requests can be exploited to alter query parameters if not properly escaped.
**Prevention:** Always wrap dynamically inserted variables (such as user claims) with `Uri.EscapeDataString()` before interpolating them into query strings in C# (.NET).
