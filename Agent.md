Product Requirements Document (PRD)
AI Textile Layer Extraction & Cleanup Engine  |  Version 2.1
1. Product Overview
The AI Textile Layer Extraction & Cleanup Engine is a professional-grade, offline-first desktop utility designed to automate and accelerate the preparation of textile artwork for production. The core goal is to convert messy, complex textile designs into clean, organized, production-ready layered assets without requiring manual separation by the designer.
The product targets Windows-first deployment, operates entirely on local hardware with no cloud dependency for core processing, and is built on a three-tier architecture: a Tauri-based frontend, a .NET 8 orchestration layer, and a Python-based ML inference service.

2. Core Problem Statement
Professional textile and print designers currently spend a disproportionate portion of their working hours on manual preparation tasks that should be automated. These tasks include separating individual motifs from a complex design, cleaning photographic folds and shadows out of scanned or photographed artwork, isolating texture layers, identifying and grouping repeating design elements, and packaging all assets into the layered file formats required by production pipelines such as PSD, SVG, or TIFF.
These workflows are highly repetitive, error-prone, and time-intensive. A single complex design can require several hours of manual cleanup before it is ready for production. The software compresses this preparation time down to minutes through AI-assisted extraction, geometry cleanup, and automated export packaging.

3. Target Users
Primary Users
•	Textile designers working with motif-heavy print artwork
•	DTF (Direct-to-Film) print designers requiring flat vector outputs
•	Surface pattern designers preparing repeat tiles
•	Textile studios managing multi-designer teams with shared workflows
•	Fashion artwork teams preparing seasonal collections for production

Secondary Users
•	Print production teams receiving artwork from external studios
•	Design freelancers preparing client deliverables
•	Creative agencies handling brand textile assets

4. Product Scope — MVP Inclusions
Extraction Features
•	Automatic motif detection and extraction using RT-DETR and SAM2
•	Background separation with transparent PNG mask output
•	Texture and pattern layer isolation
•	Automatic layer grouping by visual similarity
•	Basic typography detection and separation from design elements

Geometry Cleanup — Critical Requirement
The cleanup pipeline is the primary differentiator of this product. The AI must aggressively enforce strictly flat, production-ready designs. The following quantitative rules govern the cleanup pipeline:
•	Color Flattening: OpenCV K-Means quantization must reduce all local gradient variance to zero within each segmented motif. All gradients are posterized into solid, hex-code-specific color blocks with no tonal stepping permitted.
•	Curve Elimination: OpenCV approxPolyDP must be applied to all contour masks using a strict epsilon threshold of 0.02 multiplied by the arc length of each contour. This explicitly removes all fabric curves, wavy folds, and organic texture lines from mask edges.
•	Vector Output Rules: VTracer SVG generation must have curve-fitting explicitly disabled. All SVG outputs must consist of hard-vertex, linear polygons only. Bezier curve generation is strictly prohibited throughout the pipeline.

Export Features
•	PSD export with preserved layer hierarchy for Photoshop and CorelDRAW
•	SVG export producing flat, editable vectors with no curves or fabric textures
•	TIFF export for lossless production print compatibility in CMYK and RGB
•	PNG export for lightweight web preview and internal review

5. MVP Exclusions
The following capabilities are explicitly out of scope for the MVP release and are documented here to prevent scope creep during development:
•	Full design editing suite with brush tools or vector drawing
•	Cloud collaboration or multi-user project sharing
•	Embroidery-specific automation or DST format export
•	Batch processing pipelines for bulk folder operations
•	Plugin marketplace or third-party integration framework
•	Advanced OCR or typography editing workflows
•	AI image generation capabilities
•	Internal project cataloging or asset management database

6. User Stories
Role	Goal	Outcome
Textile Designer	Separate motifs automatically	Faster editing in Photoshop with organized layers
Print Designer	Receive flattened clean artwork without fabric wrinkles	Print preparation becomes significantly faster
Studio Operator	Receive organized layered PSD exports	Team can continue editing without sorting temporary files
DTF Designer	Export flat vector SVGs ready for cutting plotter	Zero manual cleanup required before production

7. Success Metrics
Business Metrics
•	Daily active designers using the extraction workflow
•	Export completion rate per session (target: above 85%)
•	Paid subscription conversion rate from free tier
•	30-day and 90-day user retention rates

Workflow Metrics
•	Average time saved per design compared to manual baseline (target: 70% reduction)
•	Export success rate without user-reported errors (target: above 95%)
•	Accepted layer percentage without manual correction (target: above 80%)
•	Crash frequency per 100 sessions (target: below 1)

8. Product Constraints
•	Offline-first: All core processing must function without internet access
•	Windows-first launch; macOS and Linux support are post-MVP
•	No cloud dependency for extraction, cleanup, or export workflows
•	Optimized for standard 8GB RAM workstations with or without dedicated GPU
•	Market constraint: The MVP billing engine is hard-coupled to Razorpay for Indian market UPI support; international expansion will require abstracting the billing layer to support Stripe or Paddle

9. Pricing Philosophy
The pricing strategy prioritizes rapid adoption over maximum revenue extraction. Plans are designed to be accessible to individual freelancers, small studios, and design teams. An annual Pro Tier with a meaningful discount over monthly pricing is the primary conversion target. A free tier with limited exports is included to drive initial adoption and allow word-of-mouth growth within the Indian textile design community.

Technical Requirements Document (TRD)
AI Textile Layer Extraction & Cleanup Engine  |  Version 2.1
1. System Architecture Overview
The application is built on a strict three-tier architecture. Each tier has a clearly defined and non-overlapping responsibility. The three tiers are: the React/Tauri Frontend (UI Layer), the .NET 8 Orchestrator (Middleware Layer), and the Python ML Service (Inference Layer). All inter-process communication follows strict protocols designed to minimize memory overhead and ensure stability on 8GB RAM target hardware.

2. Inter-Process Communication (IPC) Rules
Frontend to .NET Orchestrator
Tauri launches the .NET Orchestrator as a background Sidecar process on application startup. The React frontend communicates with the .NET layer exclusively via lightweight local HTTP REST requests targeting a dynamically assigned localhost port (e.g., http://localhost:PORT). Port numbers are never hardcoded; the .NET process dynamically assigns an available port and passes it back to the Tauri shell via command-line arguments at startup.

.NET Orchestrator to Python ML Service
The .NET layer communicates with the FastAPI Python service via local HTTP POST requests. The critical rule governing this boundary is that .NET must never transmit raw image byte arrays over HTTP. All image references must be passed as absolute file paths only, for example: { source_path: C:/Temp/image.jpg }. The Python service reads the file directly from disk. This rule is a strict memory constraint that prevents RAM exhaustion on 8GB machines when processing large textile artwork files.

Python ML Service Response
The Python service returns output file paths and JSON metadata back to .NET upon completion of each inference task. It does not return raw image bytes at any point in the pipeline.

3. Frontend Requirements
Requirement	Detail
Framework	React 18 with TypeScript — strict mode enabled
State Management	Zustand for global layer hierarchy, visibility, and UI state
Canvas Rendering	Konva.js for interactive layer preview and zoom/pan
Desktop Shell	Tauri 2.x for native OS integration and Sidecar process management
Responsibilities	Upload workflows, layer preview, export controls, progress visualization, hardware status banners

4. .NET Orchestrator Requirements
The .NET 8 Orchestrator is the central traffic controller of the application. It manages all stateful operations except AI inference, which is strictly delegated to Python.
Technology	Purpose
.NET 8 / ASP.NET Core	REST API host for frontend IPC
SkiaSharp	Image compositing, PSD layer packaging
ImageSharp	TIFF and PNG export generation
SQLite / Entity Framework	EXPLICITLY EXCLUDED — no local database permitted

Key responsibilities include: real-time state management of active project data in memory, native OS file dialog routing via Tauri IPC, export packaging for all four output formats, offline JWT license token reading and validation, crash recovery autosave writing to the system temp directory, and Python ML Service process lifecycle management.

5. Python ML Service Requirements
Technology	Role
FastAPI	HTTP API host for .NET IPC
ONNX Runtime	Optimized model inference with CPU/GPU provider switching
PyTorch 2.x	SAM2 and Real-ESRGAN inference
OpenCV	Contour smoothing, K-Means quantization, geometry cleanup pipeline
Pillow	Image I/O and format conversion
VTracer	Raster-to-SVG vectorization with curve-fitting disabled

6. Core AI Models
Model	Purpose	Notes
Real-ESRGAN	Enhancement and upscaling	Applied before segmentation on low-res inputs
RT-DETR	Lightweight motif detection	Primary detection pass; fallback if SAM2 fails
SAM2	High-quality segmentation	Primary segmentation model; graceful fallback to RT-DETR
OpenCV Pipeline	Geometry cleanup	approxPolyDP + K-Means; runs after every segmentation pass

7. Performance Requirements
Minimum Target Hardware
•	RAM: 8GB system memory
•	GPU: Integrated graphics (Intel Iris/UHD) or dedicated 4GB VRAM GPU
•	Storage: SSD required for temp file performance
•	CPU: Modern Intel i5 or AMD Ryzen 5 or equivalent

Optimization Constraints
•	Aggressive PyTorch VRAM swapping must be implemented to prevent out-of-memory crashes on 8GB machines
•	Dynamic INT8 quantization must be applied to all ONNX models at runtime to reduce VRAM footprint
•	If no dedicated GPU VRAM is detected (integrated graphics), the Python ML Service must automatically switch to the ONNX CPU Execution Provider
•	The React UI must detect the CPU-only state via IPC and display a persistent hardware warning banner: Hardware Acceleration Disabled: Segmentations may take 30 to 60 seconds per layer

8. Reliability Requirements
•	Temp-file-based crash recovery: .NET writes autosave.json to %TEMP%/AILayerEngine/ after every major extraction step
•	On startup, .NET checks for an existing autosave and prompts the user to recover if one is found
•	If the user declines recovery, the autosave.json and associated temp masks are deleted immediately to prevent stale state
•	Graceful inference fallback: if SAM2 inference fails or times out, the pipeline automatically retries the same region using RT-DETR
•	Non-destructive workflow: the original source image is never modified; all operations produce new output files

9. Authentication Architecture
The software uses a hybrid authentication model. The web portal manages all user identity, subscription state, and billing. The desktop application stores only a single encrypted JWT token (license.enc) in the OS AppData folder. On each application launch, the .NET layer reads and decrypts this token, validates the expiration date locally without requiring an internet connection, and hard-blocks new extractions and exports if the subscription has expired. Renewal warnings are surfaced 7 days before expiration.


UI/UX Design Specification
AI Textile Layer Extraction & Cleanup Engine  |  Version 2.1
1. UX Philosophy
The application is an extraction-first, workflow-focused utility. It is not a full design editor and must never be positioned or built as one. The single overriding design principle is speed: designers should be able to upload a complex textile image, initiate extraction, preview the result, and export their layers in the minimum possible number of interactions. Every feature decision, layout choice, and interaction pattern must be evaluated against this principle.
The secondary principle is transparency. Designers working in professional production environments cannot tolerate ambiguity about where their files are saved, what processing state the application is in, or whether an export was successful. Every async operation must have a visible progress indicator. Every completed operation must have a clear success confirmation. Every failure must surface a human-readable explanation.

2. Core UI Layout
The application uses a fixed three-panel layout that does not change between workflow states. This consistency reduces cognitive load and allows experienced users to operate by muscle memory.
Zone	Location	Contents
Top Toolbar	Full width, top of window	Application menu, session controls, hardware status badge, license status indicator
Left Sidebar	Fixed width ~260px, left panel	Upload button, layer list with visibility toggles, rename controls, export button, settings access
Main Preview Area	Remaining center/right space	Konva.js canvas, zoom and pan controls, layer overlay visualization, extraction result display
Bottom Status Bar	Full width, bottom of window	Current processing step label, progress percentage, active file path, GPU/CPU mode indicator

3. Key UX Principles
Fast Start
A user must be able to reach the extraction result from a cold application launch in three clicks or fewer: (1) click Upload, (2) select the image file, (3) click Extract. No configuration, no project setup, no onboarding wizard. The application defaults to the most aggressive extraction preset and allows the user to adjust after they have seen a result.

Non-Destructive Workflow
The original source image must never be modified, moved, or deleted by the application under any circumstances. All processing produces new output files in the system temp directory. The user retains full control over where final exports are saved via the native OS folder browser dialog. This principle must be clearly communicated in the UI with a persistent label showing the original file path.

Clear Progress Communication
Users working with large or complex textile files may experience processing times of 30 to 60 seconds per layer on CPU-only hardware. During all async operations, the application must display a named progress indicator that describes the current pipeline step by name (e.g., Running SAM2 Segmentation, Applying Geometry Cleanup, Packaging PSD Export). Generic spinner animations without descriptive labels are not acceptable.

Hardware Awareness
If the application detects that it is running in CPU-only mode (no dedicated GPU), a persistent warning banner must be displayed in the top toolbar or bottom status bar throughout the session. The banner must read: Hardware Acceleration Disabled: Segmentations may take 30 to 60 seconds per layer. This banner cannot be dismissed by the user and must remain visible for the entire session to prevent confusion about processing time expectations.

4. Allowed and Prohibited Editing Features
Feature	Permitted	Notes
Rename layer	Yes	Double-click layer name in sidebar to rename inline
Reorder layers	Yes	Drag and drop in left sidebar layer list
Toggle layer visibility	Yes	Eye icon per layer row in sidebar
Flattening intensity slider	Yes	Controls K-Means cluster count and approxPolyDP epsilon; range 1 to 10
Brush editing tools	No	Out of scope for MVP; would conflict with utility positioning
Vector pen or path drawing	No	Application is not a vector editor
Typography editing	No	Typography is extracted and exported as-is; no glyph editing
Full color adjustment tools	No	Color posterization is automated; manual adjustment is post-export

5. Screen States
Empty State
On first launch and after a session reset, the main preview area displays a centered upload prompt with a large drag-and-drop zone and an Upload Image button. The left sidebar shows a disabled layer list with a placeholder message. The bottom status bar shows Ready.

Processing State
Once extraction is initiated, the main preview area dims the source image and overlays a pipeline progress card showing each processing step with a checkmark as it completes. The left sidebar shows a spinning indicator. The Export button is disabled and grayed during processing. The top toolbar hardware badge changes color to active amber.

Result State
Upon completion, the main preview area shows the extracted layers rendered as a Konva.js canvas with individual layer visibility controls. The left sidebar populates with the full layer list. The Export button becomes active. A success toast notification appears for 3 seconds confirming the number of layers extracted.

6. Visual Design Direction
The visual language of the application must be clean, modern, and professional. It must communicate precision and reliability rather than creativity or playfulness. The recommended palette is dark neutral backgrounds (near-black or dark navy) with high-contrast white and light grey UI text, accented with a single brand color used only for interactive elements such as buttons, active states, and progress indicators. No gradients, no drop shadows, and no decorative illustrations are permitted in the core UI chrome.
Typography must be set in a single sans-serif typeface throughout the application. Font sizes should be conservative and consistent. Iconography must use a single unified icon library to ensure visual coherence. All interactive elements must have clearly distinct hover, active, and disabled states.

7. Export UX Flow
When the user clicks Export, the following sequence must occur: (1) Tauri triggers the native OS folder browser dialog allowing the user to select a destination folder. (2) The user confirms the folder. (3) The .NET Orchestrator writes the selected export format(s) directly to the chosen folder. (4) The bottom status bar shows export progress by format. (5) On completion, a toast notification confirms the export with a clickable Open Folder link that opens the destination in Windows Explorer. Under no circumstances should export files be written to internal AppData folders or temp directories as a final output location.



File System, Memory & State Strategy
AI Textile Layer Extraction & Cleanup Engine  |  Version 2.1
1. Architectural Philosophy — No Database
The application operates entirely in real-time memory. There is no local SQLite database, no embedded key-value store, and no persistent local data layer of any kind. This decision is intentional and aligns the product with the workflow model of professional utility applications such as Adobe Photoshop, where the session is king and the file system is the persistence layer.
This approach eliminates a full category of bugs related to database migrations, schema corruption, and state synchronization between in-memory and on-disk representations. It also reduces installation complexity, eliminates database file management from the user experience, and keeps the application footprint small. The tradeoff is that session recovery must be handled through a carefully designed temp file system rather than a queryable database.

2. Frontend State — Zustand
The React frontend uses Zustand as its sole state management layer. Zustand holds the complete current session state including: the active layer hierarchy as an ordered array of layer objects, visibility toggle states per layer, the current flattening intensity slider value, upload and export UI states, hardware mode (GPU or CPU), and all transient error and notification states.
Zustand state is intentionally ephemeral. It is not persisted to localStorage, sessionStorage, or any browser storage mechanism. When the application window closes, all Zustand state is discarded. Recovery of extraction results between sessions is handled entirely by the .NET crash recovery system described below.

3. .NET Backend State — In-Memory Only
The .NET Orchestrator holds the active project state in memory for the duration of the session. This includes: the absolute path of the source image currently being processed, a dictionary mapping each layer ID to its corresponding temp file mask path, the current export configuration, the active IPC port assignments for the Python ML Service, and the decoded license token payload.
None of this state is written to disk during normal operation except through the autosave mechanism described in Section 5. If the .NET process terminates unexpectedly, all in-memory state is lost, and recovery depends entirely on the autosave.json file in the temp directory.

4. Export Strategy — Native OS Save As
The export workflow is designed to give the user complete and transparent control over where their files are saved. The application does not use internal AppData folders, hidden output directories, or any form of managed export library. The workflow is as follows:
•	The user clicks Export and selects their desired output formats (PSD, SVG, TIFF, PNG)
•	Tauri triggers the native Windows folder browser dialog
•	The user navigates to and selects their destination folder (e.g., D:/Client_Work/Spring2025/)
•	The .NET Orchestrator writes the final export files directly to the selected folder
•	The status bar confirms the export and provides an Open Folder shortcut

This model mirrors the Save As behavior of all major creative tools and ensures designers always know exactly where their files are. There is no ambiguity about file location and no risk of exports being hidden in system folders.

5. Crash Recovery — The Temp File System
To prevent loss of extraction work during power interruptions, application crashes, or OS-level failures, the .NET Orchestrator implements a lightweight autosave system based on the Windows system temp directory.
Autosave Behavior
•	After every major extraction step (detection, segmentation, geometry cleanup, vectorization), .NET writes an autosave.json file to %TEMP%/AILayerEngine/
•	The autosave.json file maps each layer ID to its corresponding temporary PNG mask file path and records the current layer hierarchy, visibility states, and source image path
•	This write operation is silent and non-blocking; it must not introduce perceptible delay into the extraction workflow

Recovery Behavior on Startup
•	On every application launch, the .NET Orchestrator checks %TEMP%/AILayerEngine/ for the presence of an autosave.json file
•	If an autosave is found and the referenced temp mask files still exist on disk, the UI displays a recovery prompt: An unsaved extraction was found. Would you like to recover it?
•	If the user accepts, .NET loads the autosave state into memory and the Zustand frontend restores the layer list
•	If the user declines, the autosave.json file and all associated temp mask files are immediately deleted from the temp directory to prevent stale state accumulation

6. Custom Project Files — .layerAI Format
Users who want to save and resume work-in-progress sessions can use the custom .layerAI project format. This format allows a complete session to be saved to a single portable file and reopened at any point.
File Structure
A .layerAI file is a standard ZIP archive with a custom file extension. It contains exactly three components:
•	The original source image in its original format (JPEG, PNG, or TIFF)
•	One transparent PNG mask file per extracted layer, named by layer ID
•	A state.json file encoding the complete layer hierarchy, opacity values, visibility states, and flattening settings

Schema Versioning — Critical Rule
The state.json file must include a schema_version key at the root level with a value of 1.0 for all files produced under the current specification. This versioning requirement is non-negotiable and must be enforced by the .NET Orchestrator on both write and read operations.
On load, the .NET Orchestrator must validate the schema_version value before attempting to deserialize the state.json. If a file with schema_version 2.0 or higher is opened by an older version of the application, the Orchestrator must refuse to load it and surface a clear error message directing the user to update the application. When a future v2 schema is introduced, a migration script must be implemented and executed automatically before loading the file into memory. Silent schema mismatches that produce corrupted layer states are not acceptable.

7. Temp File Cleanup Policy
Temp files in %TEMP%/AILayerEngine/ accumulate during normal use and must be managed to prevent disk space exhaustion on the user's machine. The following cleanup rules apply:
•	On successful export completion, all temp mask files associated with the exported session are deleted automatically
•	On application close via the normal exit path, all temp files from the current session are deleted
•	On startup recovery decline, all temp files from the recovered session are deleted immediately
•	A maximum temp directory size cap of 2GB must be enforced; if this threshold is reached, the oldest session's temp files are deleted automatically with a non-blocking notification to the user


Implementation Plan
AI Textile Layer Extraction & Cleanup Engine  |  Version 2.1
1. Development Philosophy
The MVP build prioritizes extraction quality, workflow speed, export reliability, and usability in that order. Feature breadth is explicitly deprioritized. A single workflow that works flawlessly for 90% of real textile design inputs is more valuable at launch than ten workflows that each work for 50% of inputs. Every phase has a defined completion gate that must be passed before the next phase begins.

2. Phase 1 — Foundation (Week 1)
Goal: Establish the full three-tier architecture with functional IPC before writing any AI code.

Tauri + React Frontend
•	Initialize Tauri 2.x project shell with React 18 and TypeScript
•	Configure Zustand store with the complete state schema for layers, UI states, and hardware mode
•	Build the static UI shell: top toolbar, left sidebar, main preview canvas, status bar
•	Implement native OS file dialog trigger via Tauri IPC for image upload

.NET Orchestrator
•	Initialize ASP.NET Core (.NET 8) project with dynamic port assignment on startup
•	Implement JWT license.enc reader and local expiration enforcement logic
•	Implement temp file autosave writer and startup recovery checker
•	Establish REST API endpoints for all planned frontend-to-.NET IPC calls

Python ML Service
•	Initialize FastAPI service with ONNX Runtime configured for both GPU and CPU Execution Providers
•	Implement hardware detection logic: check for CUDA/VRAM availability and select Execution Provider accordingly
•	Return hardware mode flag to .NET on startup so the frontend can display the correct hardware banner
•	Implement INT8 quantization loading for all ONNX model files

Shared Types
•	Define all IPC payload schemas in shared-types/ as OpenAPI/JSON Schema files
•	Configure quicktype build step to auto-generate TypeScript interfaces, C# classes, and Python Pydantic models from these schemas
•	Add a CI check that fails the build if any generated file is out of sync with its source schema

Phase 1 Completion Gate: A test image file path can be passed from the React UI through .NET to Python and a mock response path returned and rendered in the Konva canvas without errors.

3. Phase 2 — Core Extraction & Geometry Cleanup (Week 2–3)
Goal: Produce a working end-to-end extraction with strictly flat geometry output.

Detection and Segmentation
•	Integrate RT-DETR ONNX model for initial motif bounding box detection
•	Integrate SAM2 PyTorch model for high-quality mask generation within detected bounding boxes
•	Implement graceful fallback: if SAM2 inference fails or exceeds a 45-second timeout, retry the region with RT-DETR mask generation

Geometry Cleanup Pipeline — Critical
•	Immediately after each segmentation mask is produced, run OpenCV K-Means quantization to reduce gradient variance to zero within each mask region
•	Apply OpenCV approxPolyDP to all mask contours using epsilon = 0.02 * arcLength to eliminate curves, folds, and organic textile textures
•	Verify that no Bezier curve data is present in any pipeline output at this stage

Acceptance Test for Phase 2
Phase 2 is not complete until the pipeline passes the following test: run the geometry cleanup pipeline against a reference set of 10 real textile design images. Verify: zero Bezier curves present in any output contour, K-Means cluster count does not exceed the configured maximum (default: 12 colors per motif), and contour edge smoothness visually matches the flat reference samples approved by the product owner.

Layer Grouping and Preview
•	Implement automatic layer grouping by visual similarity score
•	Build real-time Konva.js layer preview with individual visibility toggles
•	Connect layer list in left sidebar to Zustand state

4. Phase 3 — Vectorization & Export Pipeline (Week 4)
Goal: Produce production-ready file exports in all four formats.

•	Integrate VTracer vectorization with curve-fitting explicitly disabled; all SVG outputs must be hard-vertex linear polygons
•	Build TIFF export pipeline via ImageSharp supporting both CMYK and RGB color spaces
•	Build PSD layered export pipeline via SkiaSharp preserving the full layer hierarchy
•	Build PNG export pipeline for lightweight preview generation
•	Implement native OS Save As dialog integration for all export formats
•	Implement post-export temp file cleanup

Phase 3 Completion Gate: All four export formats open correctly in Adobe Photoshop, CorelDRAW, and Inkscape. PSD layers are preserved. SVG contains no Bezier curves. TIFF opens in both CMYK and RGB color modes.

5. Phase 4 — Authentication & Launch (Week 5–6)
Goal: Implement hybrid authentication, packaging, and public release.

•	Build web portal login flow using Next.js and Supabase Auth
•	Implement /api/license/issue endpoint that signs and encrypts the JWT offline token
•	Implement desktop .enc token caching and 7-day pre-expiry warning display
•	Integrate Razorpay subscription checkout on the web portal pricing page
•	Implement Razorpay webhook handler to update subscription status in real time
•	Build Windows installer package (NSIS or WiX) including all three service binaries
•	Complete end-to-end QA pass covering extraction quality, export integrity, license enforcement, and crash recovery

6. Repository & Folder Structure
Directory	Stack	Responsibility
web-portal/	Next.js + Supabase + Razorpay	Marketing site, user auth, billing, license issuance
desktop-app/src-ui/	React + Zustand + Tauri	Frontend UI, state management, canvas preview
desktop-app/src-tauri/	Rust + Tauri 2.x	Desktop shell, OS integration, Sidecar management
desktop-app/src-core/	.NET 8 + SkiaSharp	Orchestration, export packaging, license validation
ml-service/	Python + FastAPI + ONNX	AI inference, geometry cleanup, vectorization
shared-types/	JSON Schema + quicktype	Single source of truth for all IPC payload contracts

7. Environment & Configuration
No secrets, API keys, or port numbers are ever hardcoded in source files. All configuration follows this strategy:
•	Web portal uses .env.local for NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_KEY, and RAZORPAY_WEBHOOK_SECRET
•	The .NET Orchestrator dynamically assigns available localhost ports at startup and passes them to the Python ML Service and Tauri via command-line arguments
•	All environment variable names must be documented in a .env.example file committed to the repository
•	Production secrets are managed through Vercel environment variables for the web portal; no secrets are ever committed to the monorepo


Web Platform & Authentication Portal
AI Textile Layer Extraction & Cleanup Engine  |  Version 2.1
1. Platform Overview
The web platform serves three distinct functions within the product ecosystem: it is the public marketing storefront that converts visitors into paying subscribers, the billing engine that manages subscription lifecycle events in real time, and the central authentication authority that issues the offline license tokens used by the desktop application.
Critically, the web platform does not perform any image processing, extraction, or AI inference. It is a management portal only. All computational work happens on the user's local machine. This separation is architecturally important because it means the web platform can be a lightweight, standard Next.js deployment with no GPU infrastructure, no large file handling, and no specialized compute requirements.

2. Technology Stack
Layer	Technology	Hosting
Frontend + API Routes	Next.js (React / TypeScript)	Vercel — automatic CI/CD from main branch
Database	Supabase (PostgreSQL)	Supabase managed cloud — EU or AP region
Authentication	Supabase Auth	Delegated — no custom password hashing
Payments	Razorpay API + Webhooks	Razorpay-managed — Indian market, UPI support
License Signing	RS256 JWT via Next.js API Route	Vercel serverless function

3. Database Schema
The web platform uses Supabase's native auth.users table for all user identity and password management. Custom password hashing or a standalone users table with password_hash columns is explicitly prohibited. Delegating authentication to Supabase Auth eliminates a significant security surface area and provides out-of-the-box features including password reset flows, email verification, and session management.
The only custom table required is the subscriptions table, which records the subscription state for each user:
Column	Type	Notes
id	UUID PRIMARY KEY	Subscription record identifier
user_id	UUID REFERENCES auth.users(id)	Foreign key to Supabase managed auth table
razorpay_sub_id	TEXT UNIQUE	Razorpay subscription ID for webhook matching
plan_tier	TEXT	Values: free, pro, studio
status	TEXT	Values: active, past_due, canceled
current_period_end	TIMESTAMP	Used to generate the license JWT expiry claim

4. API Endpoints — The Desktop Bridge
The web platform exposes three API endpoints that serve as the bridge between the desktop application and the subscription management system.
POST /api/auth/login
Accepts an email and password from the desktop application login screen. Interfaces with Supabase Auth to validate credentials. On success, returns a short-lived session token that the desktop app uses to call the license issuance endpoint. On failure, returns a structured error with a human-readable message for display in the desktop UI. This endpoint must implement rate limiting to prevent brute-force attacks.

POST /api/license/issue
Called by the desktop application after successful authentication. This endpoint validates that the authenticated user has an active subscription in the subscriptions table. If the subscription status is active, the server uses an RS256 private key (stored as a Vercel environment variable, never committed to the repository) to sign a JWT containing the current_period_end timestamp as the expiry claim. The signed JWT is then encrypted and returned to the desktop application as the license.enc binary file, which the .NET Orchestrator stores in the OS AppData folder.

POST /api/billing/webhook
This endpoint receives real-time subscription lifecycle events directly from Razorpay. All incoming webhook requests must be validated against the RAZORPAY_WEBHOOK_SECRET before processing. The endpoint handles the following event types: subscription.activated (set status to active), subscription.charged (update current_period_end to the new billing period end date), subscription.cancelled (set status to canceled), and payment.failed (set status to past_due). Failed webhook processing must be logged with the full event payload for manual review.

5. Offline License Enforcement
The hybrid authentication model is designed to provide full functionality to paying subscribers even in environments with no internet connection, while still enforcing subscription expiry reliably.
How It Works
•	When a user successfully authenticates and has an active subscription, the server issues and the desktop app stores license.enc in the OS AppData directory
•	On every application launch, the .NET Orchestrator decrypts license.enc using the embedded public key and reads the current_period_end timestamp from the JWT claims
•	If the current date is before current_period_end, the application runs in fully unlocked mode with no internet check required
•	If the current date is within 7 days of current_period_end, the application displays a persistent renewal warning banner with a link to the web portal pricing page
•	If the current date is past current_period_end, the application hard-blocks all new extraction and export operations and redirects the user to the web portal to renew

Security Considerations
•	The RS256 private key used to sign JWTs must never be embedded in the desktop application; only the corresponding public key is embedded for validation
•	The license.enc file is encrypted at rest using AES-256 with a machine-specific entropy component to prevent license files from being shared between machines
•	License files that fail signature validation or decryption must be treated as invalid and must trigger the same hard-block as an expired license

6. Landing Page Strategy
Hero Section
The primary value proposition headline is: India's First Offline AI Layer Engine for Textile Designers. The hero section must include a high-resolution before-and-after interactive slider demonstrating a messy fabric photograph transforming into perfectly flat, vector-style production-ready artwork. This visual proof is the primary conversion driver and must load above the fold on both desktop and mobile viewports.

Feature Section
Three feature pillars should be highlighted with supporting visuals: (1) Automatic Extraction — separate motifs, textures, and backgrounds in seconds; (2) Strict Geometry Cleanup — eliminate fabric folds, shadows, and curves automatically; (3) Production-Ready Export — PSD, SVG, TIFF, and PNG with a single click.

Pricing Section
The pricing section must clearly present all plan tiers with a prominent annual/monthly toggle that demonstrates the savings of the annual Pro Tier. Each plan tier must have a direct Razorpay checkout button. The free tier CTA must link to the installer download. Pricing must be displayed in Indian Rupees as the primary currency for the MVP launch, with no currency switching in the MVP.

7. Installer Distribution
The desktop installer download links on the landing page must point to versioned release assets hosted on GitHub Releases or a Vercel-managed static asset store. Installer files must never be served from the Next.js application server directly. Each installer release must be code-signed with a valid Windows code-signing certificate to prevent Windows SmartScreen warnings on download and installation. The landing page must display the current version number and release date alongside the download button.
