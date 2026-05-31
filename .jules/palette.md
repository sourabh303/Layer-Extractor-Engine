## 2026-05-29 - [Added ARIA Attributes to Action Buttons]
**Learning:** [Identified missing screen reader support and loading state representation in toast notification and export action buttons.]
**Action:** [Added 'aria-label' and 'aria-busy' attributes to respectively clarify visually-implied actions and convey transient states to assistive technologies without altering visual design.]

## 2026-05-30 - [Added ARIA Attributes and Improved Loading States in Login Form]
**Learning:** [Identified missing screen reader support for form inputs and lack of visual feedback during authentication. Existing code used inline styles making standard class-based disabled states difficult.]
**Action:** [Added 'aria-label' to inputs without associated labels, disabled inputs and adjusted opacity when loading to provide visual feedback and prevent multiple submissions, and added 'role="alert"' to the error message container to immediately notify screen readers of authentication issues.]

## 2026-06-01 - [Improved Empty State and Keyboard Accessibility]
**Learning:** [Identified that the default plain-text empty state lacked visual hierarchy, and interactive elements lacked a global :focus-visible state, hurting keyboard accessibility.]
**Action:** [Replaced the plain text empty state with a structured layout containing an SVG icon and descriptive text. Added a global :focus-visible rule to index.css to ensure keyboard navigation outlines are consistently visible.]
