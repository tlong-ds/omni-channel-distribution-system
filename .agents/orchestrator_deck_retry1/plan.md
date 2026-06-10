# plan.md — PPTX Slide Deck Verification & Visual QA Plan (Retry 1)

This plan outlines the verification, visual QA, and remediation strategy for the LOGage 2026 Round 2 slide deck.

## Phase 1-3: Content Extraction, Layout Mapping, Setup & Integration (Completed)
- Previous work completed content extraction from LaTeX files, mapped layout, unpacked the template, renamed navigation bars, modified XML content/relationships, and compiled the output to `/Users/bunnypro/teamwork_projects/logage_slides/output.pptx`.

## Phase 4: Visual QA & Verification (Current)
- **Goal**: Rigorously verify content correctness, layout structure, and visual quality. Correct any issues found.
- **Tasks**:
  1. **Content & Structural Verification**:
     - Run `markitdown` on `/Users/bunnypro/teamwork_projects/logage_slides/output.pptx` to verify that it has exactly 11 slides.
     - Inspect slide text content to ensure navigation bars say "Part 1", "Part 2", and "Part 3", and check for placeholder text.
  2. **Visual Inspection**:
     - Convert `output.pptx` to PDF using headless LibreOffice.
     - Render PDF pages to JPEG images using `pdftoppm`.
     - Spawn a Reviewer/Critic subagent to inspect the slide images against high-end design guidelines, paying attention to:
       - Text overlap and box overflow.
       - Contrast of text and icons against backgrounds.
       - Preservation and positioning of the contest logo.
       - Correct integration, sizing, and styling of charts from `outputs/round2/charts/`.
  3. **Remediation & Re-compilation (if needed)**:
     - If issues are identified (e.g., text overlap, broken charts, navigation bar typos), modify the XMLs in the unpacked directory `/Users/bunnypro/teamwork_projects/logage_slides/unpacked/`.
     - Repack the presentation into `/Users/bunnypro/teamwork_projects/logage_slides/output.pptx`.
     - Re-render and re-verify until all issues are solved.

## Phase 5: Final Review & Sign-off
- **Goal**: Final acceptance by the orchestrator and report to user.
