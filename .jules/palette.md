## 2025-02-20 - Explicit Form Labels

**Learning:** Both the desktop app and web portal frontends used implicit label wrapping or lacked explicit `id`/`htmlFor` bindings entirely on form inputs, causing screen reader accessibility issues.
**Action:** Always ensure form inputs use explicit `<label htmlFor="id">` elements with corresponding `id` attributes on the input fields, rather than implicit wrapping or relying purely on placeholder text, to ensure proper screen reader support and accessibility across both React codebases.

## 2024-05-18 - Explicit labels for accessibility
**Learning:** Implicitly wrapped labels (`<label><input /> Text</label>`) can be less accessible to certain screen readers and are restricted in this app's design system. Explicit associations using `id` on the input and `htmlFor` on the label provide better accessibility and structure.
**Action:** Always prefer explicit `<input id="...">` and `<label htmlFor="...">` associations instead of implicit wrapping for all forms, checkboxes, and radio buttons across React frontends in this repository.
