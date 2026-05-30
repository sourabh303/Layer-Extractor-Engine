## 2026-05-29 - [Added ARIA Attributes to Action Buttons]
**Learning:** [Identified missing screen reader support and loading state representation in toast notification and export action buttons.]
**Action:** [Added 'aria-label' and 'aria-busy' attributes to respectively clarify visually-implied actions and convey transient states to assistive technologies without altering visual design.]

## 2026-05-30 - [Added ARIA Attributes and Improved Loading States in Login Form]
**Learning:** [Identified missing screen reader support for form inputs and lack of visual feedback during authentication. Existing code used inline styles making standard class-based disabled states difficult.]
**Action:** [Added 'aria-label' to inputs without associated labels, disabled inputs and adjusted opacity when loading to provide visual feedback and prevent multiple submissions, and added 'role="alert"' to the error message container to immediately notify screen readers of authentication issues.]
