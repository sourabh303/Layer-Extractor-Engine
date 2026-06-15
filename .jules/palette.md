## 2025-02-20 - Explicit Form Labels

**Learning:** Both the desktop app and web portal frontends used implicit label wrapping or lacked explicit `id`/`htmlFor` bindings entirely on form inputs, causing screen reader accessibility issues.
**Action:** Always ensure form inputs use explicit `<label htmlFor="id">` elements with corresponding `id` attributes on the input fields, rather than implicit wrapping or relying purely on placeholder text, to ensure proper screen reader support and accessibility across both React codebases.
