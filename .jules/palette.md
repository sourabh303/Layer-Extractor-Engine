## 2025-02-20 - Explicit Form Labels

**Learning:** Both the desktop app and web portal frontends used implicit label wrapping or lacked explicit `id`/`htmlFor` bindings entirely on form inputs, causing screen reader accessibility issues.
**Action:** Always ensure form inputs use explicit `<label htmlFor="id">` elements with corresponding `id` attributes on the input fields, rather than implicit wrapping or relying purely on placeholder text, to ensure proper screen reader support and accessibility across both React codebases.
## 2026-06-29 - [Loading Spinner for Async Actions]
**Learning:** Explicit visual feedback like a loading spinner helps reassure users that their action was acknowledged and is being processed, especially important for authentication forms which often have network latency. Without it, users may think the application froze or attempt multiple submissions.
**Action:** When adding async logic, always pair it with a visual state (like disabling buttons and adding a spinner) that clearly communicates loading state to prevent confusion.
