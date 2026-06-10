# plan.md — PPTX Presentation Generation Plan

## Phase 1: Content Extraction & Template Analysis
- **Goal**: Extract methodology, findings, and recommendations from `part1_question_summary.tex`, `part2_question_summary.tex`, and `part3_question_summary.tex`. Analyze the template `Red Modern Logistic Presentation.pptx` for available slide layouts and placeholders.
- **Tasks**:
  - Spawn an Explorer agent to read and summarize the tex files.
  - Run the `thumbnail.py` script on the template and convert it to text using `markitdown` to inspect its layout index.
- **Verification**: Ensure we have a clear map of source data and available template slide layouts.

## Phase 2: Slide Mapping & Structural PPTX Setup
- **Goal**: Formulate the slide-by-slide structure (exactly 11 slides) and prepare the unpacked directory.
- **Slide Allocation (11 slides)**:
  - Slide 1: Introduction (Title slide from template layout)
  - Slide 2: Executive Summary (Highlights of Round 2 insights)
  - Slide 3: Part 1 - Methodology & Data (ABC analysis, xyz analysis, data cleaning)
  - Slide 4: Part 1 - Product Segmentation Findings (ABC-XYZ matrix and demand profiles)
  - Slide 5: Part 1 - Warehouse Allocation & Dominance Map (Warehouse dominance, imbalances)
  - Slide 6: Part 1 - SKU Profile comparison & Packaging Mix
  - Slide 7: Part 2 - Logistics Network Design (Channel flow profile and networks)
  - Slide 8: Part 2 - Urban logistics & HCM District Volume analysis
  - Slide 9: Part 2 - Inventory pooling & Lead-time sensitivity analysis
  - Slide 10: Part 3 - Summary (Slotting analysis & Pick-Pack flows)
  - Slide 11: Conclusion (Key recommendations and strategic roadmap)
- **Tasks**:
  - Copy template to `/Users/bunnypro/teamwork_projects/logage_slides/output.pptx`.
  - Unpack the presentation.
  - Duplicate/reorder/delete slides via `add_slide.py` to match the 11-slide plan.
  - Re-verify slide order and run `clean.py`.
- **Verification**: `python -m markitdown output.pptx` shows exactly 11 slides.

## Phase 3: Content Editing & Chart Integration
- **Goal**: Populate content, insert charts, and polish navigation bar.
- **Tasks**:
  - Rename the navigation bar items on every slide to "Part 1", "Part 2", and "Part 3".
  - Replace text placeholders with detailed findings.
  - Keep the contest logo exactly in its original position.
  - Integrate appropriate charts into the slide relationships.
- **Verification**: XML structure compiles and repacks successfully.

## Phase 4: Visual QA & Final Review
- **Goal**: Ensure premium layout design, no overlaps, high contrast, and logo placement.
- **Tasks**:
  - Render PPTX to PDF via LibreOffice, then PDF to JPG.
  - Spawn a Reviewer/Challenger/Auditor agent to review every slide image against visual guidelines.
  - Implement fixes for any alignment or overlap issues.
- **Verification**: Final PDF visual inspection shows perfect alignment.
