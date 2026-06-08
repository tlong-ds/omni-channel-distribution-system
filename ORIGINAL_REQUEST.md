# Original User Request

## Initial Request — 2026-06-08T15:20:36+07:00

Implement the two remaining unbuilt deliverables for the **LOGage2026 Round 2** logistics competition — Part 3: Warehouse Operations Solutions — inside the existing Python analytics pipeline, and produce a compiled LaTeX report. Parts 1 and 2 are fully complete; this extends the pipeline from scratch for Part 3. Do NOT use or modify `notebook.ipynb`.

Working directory: `/Users/bunnypro/Projects/LOGage2026`
Integrity mode: development

---

## Context

The pipeline lives in `src/logage2026/` with modules:
- `analysis.py` — builds DataFrames and CSV tables
- `visuals.py` — renders charts (PNG)
- `notes.py` — writes LaTeX (`.tex`) reports
- `excel_reports.py` — writes Excel workbooks
- `run_analysis.py` — main entry point that calls all of the above

Outputs live under `outputs/round2/`: `cleaned/`, `tables/`, `charts/`, `notes/`.

**Important**: `run_analysis.py` contains a `STALE_OUTPUTS` list (lines ~64–95) that *deletes* `slotting_plan.csv` and `pick_pack_flowchart.md` at the start of every run (they were added as placeholders but never generated). Before implementing Part 3, remove those two entries from `STALE_OUTPUTS` so the pipeline does not delete its own newly generated outputs.

### Key inputs for Part 3

| File | Contents |
|---|---|
| `outputs/round2/tables/q11_sku_abc_xyz.csv` | 470 SKUs with ABC class, XYZ class, velocity metrics |
| `outputs/round2/cleaned/sku_master_cleaned.csv` | SKU dimensions (L/W/H cm), weight (kg), PCS/CTN/Pallet, CBM |
| `outputs/round2/cleaned/shipments_cleaned.csv` | 6-month outbound transaction history (Jun–Dec 2025) |
| `outputs/round2/tables/q13_order_profile_segments.csv` | B2B/B2C segment profiles |
| `outputs/round2/tables/safety_stock_class_a.csv` | Class A safety stock values |
| `VILAS - Inhouse Training - SNP.pptx` | Warehouse storage design reference — extract text with `python-pptx` and use the zone-design principles, terminology, and slotting framework it contains |
| `outputs/round2/notes/part1_question_summary.tex` | LaTeX style reference (match preamble, section structure, formatting) |
| `outputs/round2/notes/part2_question_summary.tex` | LaTeX style reference |

There is already a helper `_slotting_zone(abc_class)` in `excel_reports.py` that maps A→Pick-Face Zone, B→Forward Reserve Zone, C→Reserve/Bulk Zone. Use it as a starting point for Q3.1.

---

## Requirements

### R1. Slotting Optimization (Q3.1)

Using the ABC-XYZ classification and SKU physical dimensions/weight from the master data, produce a complete slotting plan that assigns every SKU to one of three warehouse zones:
- **Class A / Fast-Moving** → Pick-face zone (lower racks, ergonomic height, close to packing area)
- **Class B** → Intermediate zone with replenishment logic
- **Class C / Slow-Moving** → Reserve zone (upper racks, bulk storage)

The plan must include a **quantitative comparison against a random storage baseline** demonstrating at least a **30% reduction in estimated picker travel time**. Use SKU velocity (order frequency), weight, and physical size as inputs. Document the travel time formula and assumptions clearly.

New Python code should follow the existing module structure — add functions to `analysis.py` (computation) and `visuals.py` (charts) and call them from `run_analysis.py`.

**Required outputs:**
- `outputs/round2/tables/slotting_plan.csv` — one row per SKU with: SKU code, ABC class, XYZ class, zone assignment, a numeric velocity/travel contribution metric, and rank within zone
- `outputs/round2/charts/q31_slotting_analysis.png` — at least one visualization (e.g., zone distribution, travel time comparison bar chart)

### R2. Omni-Channel Pick-and-Pack Flowchart (Q3.2)

Design a unified pick-and-pack process for two order types:
- **B2B orders** (large volume, few SKUs): Pallet / Total Picking — pickers fulfill entire pallets or large CTN quantities per order in a single pass
- **B2C / E-commerce orders** (small quantity, many SKUs, many concurrent orders): Batch Picking + Zone Routing — multiple small orders grouped into a single pick wave, sorted at packing

The flowchart **must explicitly cover the conflict scenario**: the same SKU is ordered simultaneously by a B2B client and a B2C customer with limited available stock. Include stock allocation rules and escalation logic for when stock is insufficient for both channels.

**Required outputs:**
- `outputs/round2/notes/pick_pack_flowchart.md` — valid Mermaid `flowchart` diagram + written description of each step and decision point
- `outputs/round2/charts/q32_pick_pack_flowchart.png` — the flowchart rendered as a PNG image (use `mmdc` from `@mermaid-js/mermaid-cli` if available, or an equivalent renderer)

### R3. Part 3 LaTeX Report

Write and compile a LaTeX report for Part 3 that follows the exact same conventions as the existing `part1_question_summary.tex` and `part2_question_summary.tex` (read both to match preamble, packages, section structure, table style, figure embedding, and overall formatting).

The report must include:
- **Q3.1 section**: slotting zone framework (referencing VILAS SNP design principles), the quantitative travel-time analysis with formula and a results table, the slotting plan summary, and the embedded chart
- **Q3.2 section**: complete pick-and-pack process description, embedded flowchart, and explanation of each decision point including the conflict resolution rules

Add the Part 3 LaTeX generation to `notes.py` (as a `write_part3_notes()` or equivalent function) and call it from `run_analysis.py` after the Part 3 analysis steps, consistent with how `write_notes()` handles Parts 1 and 2.

**Required outputs:**
- `outputs/round2/notes/part3_question_summary.tex`
- `outputs/round2/notes/part3_question_summary.pdf` (compiled from the `.tex` source)

---

## Acceptance Criteria

### Slotting Plan (Q3.1)
- [ ] `outputs/round2/tables/slotting_plan.csv` exists with all 470 SKUs, each assigned to a zone
- [ ] The CSV contains at minimum: SKU code, ABC class, XYZ class, zone, and a numeric travel-distance or velocity metric
- [ ] `outputs/round2/charts/q31_slotting_analysis.png` exists and is non-empty
- [ ] The Part 3 report documents a ≥30% picker travel time reduction vs. random baseline, with the formula and assumptions stated

### Pick-and-Pack Flowchart (Q3.2)
- [ ] `outputs/round2/notes/pick_pack_flowchart.md` exists and contains a syntactically valid Mermaid flowchart
- [ ] The flowchart covers all three paths: B2B pallet picking, B2C batch picking, and the dual-channel stock conflict scenario with allocation + escalation rules
- [ ] `outputs/round2/charts/q32_pick_pack_flowchart.png` exists as a rendered image

### Part 3 Report (R3)
- [ ] `outputs/round2/notes/part3_question_summary.pdf` exists and opens correctly
- [ ] The PDF contains answers to both Q3.1 and Q3.2 with supporting tables and at least one embedded chart or figure
- [ ] LaTeX style (preamble, sections, formatting) visually matches the existing Part 1 and Part 2 PDFs
- [ ] The two STALE_OUTPUTS entries for `slotting_plan.csv` and `pick_pack_flowchart.md` have been removed from `run_analysis.py`
- [ ] `python run_analysis.py` completes without errors after all changes are integrated
