# Visual QA Report - Stage 1
**Date**: 2026-06-10
**Slide Deck**: `/Users/bunnypro/teamwork_projects/logage_slides/output.pptx`

---

## 1. Structure Verification
Using `markitdown`, the slide deck structure was verified:
- **Total Slides**: Exactly 11 slides.
- **Slide 1**: Title Slide – *Omni-Channel Logistics & Supply Chain Strategy*
- **Slide 2**: *Executive Summary: Key Operational Insights*
- **Slide 3**: *SKU Demand Pattern Classification (ABC-XYZ Analysis)*
- **Slide 4**: *Warehouse Throughput Analysis & Data Quality*
- **Slide 5**: *Geographic Demand Mapping & Regional Concentration*
- **Slide 6**: *Customer Segment Profiling: MT vs. TT*
- **Slide 7**: *Network Model Assessment & Channel Flow Profile*
- **Slide 8**: *HCMC SLA Feasibility & Dark Store Nodes*
- **Slide 9**: *Lead Time and Class A Safety Stock Optimization*
- **Slide 10**: *Inventory Pooling & Operational Control*
- **Slide 11**: *Strategic Recommendations & Execution Roadmap*

---

## 2. Text and Navigation QA
A review of the extracted text content was performed:
- **Navigation Bar**: All slides successfully contain the navigation bar elements: `Part 1`, `Part 2`, and `Part 3` at the top.
- **Placeholders**: Grep searches for common placeholder patterns (e.g., `xxxx`, `lorem`, `ipsum`, `todo`, `tbd`, `placeholder`, and brackets `[`/`]`) returned no matches. The text content is fully populated with actual analysis details and metrics from the Round 2 database (e.g., the 19 A-X SKUs driving 57.87% of quantity, 93.02% vs. 6.98% operational splits, 1.94 days average lead time, and 77.5% expected travel-time reduction under Model 2 slotting).

---

## 3. Contest Logo Position Analysis
We unpacked the `.pptx` file and inspected the XML structure under `ppt/slides/` and `ppt/slides/_rels/`:
- **Logo Media Reference**: The contest logo is identified as `image1.png` in `ppt/media/`.
- **Relationship Mapping**: Every slide relationship file (`slideX.xml.rels`) correctly binds the relationship ID `rId2` to `../media/image1.png`.
- **Layout Position Preservation**: Every slide XML file (`slideX.xml`) positions this image shape with identical coordinates and size parameters:
  - **Offset**: `x="17029142"` and `y="442632"`
  - **Extent/Size**: `cx="1258858"` and `cy="1067032"`
- **Conclusion**: The contest logo is perfectly preserved in its original position and dimensions across all 11 slides.

---

## 4. Slide Image Index
The converted slide images are rendered and located at `/Users/bunnypro/teamwork_projects/logage_slides/images/`:

| Slide | Title | Image Path |
|---|---|---|
| 1 | Omni-Channel Logistics & Supply Chain Strategy | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-01.jpg` |
| 2 | Executive Summary: Key Operational Insights | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-02.jpg` |
| 3 | SKU Demand Pattern Classification (ABC-XYZ Analysis) | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-03.jpg` |
| 4 | Warehouse Throughput Analysis & Data Quality | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-04.jpg` |
| 5 | Geographic Demand Mapping & Regional Concentration | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-05.jpg` |
| 6 | Customer Segment Profiling: MT vs. TT | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-06.jpg` |
| 7 | Network Model Assessment & Channel Flow Profile | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-07.jpg` |
| 8 | HCMC SLA Feasibility & Dark Store Nodes | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-08.jpg` |
| 9 | Lead Time and Class A Safety Stock Optimization | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-09.jpg` |
| 10 | Inventory Pooling & Operational Control | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-10.jpg` |
| 11 | Strategic Recommendations & Execution Roadmap | `/Users/bunnypro/teamwork_projects/logage_slides/images/slide-11.jpg` |

---

## 5. Extracted Text Content
Below is the verbatim text extracted from the presentation:

### Slide 1
* **Part 1**, **Part 2**, **Part 3**
* **Title**: Omni-Channel Logistics & Supply Chain Strategy
* **Subtitle**: Data-Driven Optimization for Multi-Channel Operations, Inventory Control, and Warehouse Slotting

### Slide 2
* **Part 1**, **Part 2**, **Part 3**
* **Title**: Executive Summary: Key Operational Insights
* **Bullet 1**: Extreme SKU Concentration: A tiny core of 19 "Fast-Moving" A-X SKUs (4.04% of assortment) drives 57.87% of outbound quantity and 25.88% of pick transactions.
* **Bullet 2**: Centralized Invoicing Distortion: Resolved data initially showed a 92.59% My Phuoc bias. Statistical scaling restored the true operational split: 93.02% My Phuoc vs. 6.98% Vinh Loc.
* **Bullet 3**: Distinct Segment Profiles: Modern Trade orders are large, consolidated, and pallet-centric (75.25% pallet share). Traditional Trade orders are small, fragmented (48.54% carton, 9.77% loose), and spread across 60 provinces.
* **Bullet 4**: Virtual Inventory Pooling: Merging channel safety stocks under a mile-weighted lead time of 1.94 days yields a **61.8% inventory reduction** (12,168 units vs. 31,852 units).
* **Bullet 5**: Ergonomic Slotting: Model 2 (ABC + Ergonomics) achieves a **77.5% expected travel time reduction**, exceeding the 30% peak improvement target.

### Slide 3
* **Part 1**, **Part 2**, **Part 3**
* **Title**: SKU Demand Pattern Classification (ABC-XYZ Analysis)
* **Bullet 1**: Assortment Classification: 470 unique SKUs evaluated across volume (ABC) and transaction frequency (XYZ) over 7 months.
* **Bullet 2**: ABC Volume Concentration: Class A (Top 70% quantity) includes 28 SKUs; Class B (Next 20%) includes 39 SKUs; Class C (Bottom 10%) includes 403 SKUs.
* **Bullet 3**: XYZ Frequency Concentration: Class X (Top 70% orders) includes 53 SKUs; Class Y (Next 20%) includes 88 SKUs; Class Z (Bottom 10%) includes 329 SKUs.
* **Bullet 4**: The Fast-Moving Group (A-X): 19 SKUs (4.04%) drive **57.87% of outbound quantity** (163,014 units) and **25.88% of pick transactions** (5,381 orders).
* **Bullet 5**: Operational Recommendations: Dedicated replenishment and lower pick-face positioning (levels 1 and 2) must be reserved for the 19 A-X SKUs to minimize travel time.
* **Bullet 6**: Rationalize or store in deep reserve the 329 C-Z slow-moving SKUs (70.0% of assortment).
* **Charts**: `Chart0.jpg`, `Chart1.jpg`

### Slide 4
* **Part 1**, **Part 2**, **Part 3**
* **Title**: Warehouse Throughput Analysis & Data Quality
* **Bullet 1**: High Geocoding Resolution: The data cleansing pipeline successfully resolved 97.12% of transaction rows and 94.15% of outbound quantities to specific coordinates.
* **Bullet 2**: Database Gaps: 617 rows were left unresolved due to 'unknown' Ship-to Customers in the source logs.
* **Bullet 3**: Centralized Invoicing Distortion: ERP invoicing initially attributes 92.59% of resolved volume to My Phuoc. Utilizing Statistical Scaling (Approach A), we restore the true 93.02% vs. 6.98% operational split.
* **Bullet 4**: Throughput Realities: My Phuoc processes 262,053 units (93.02% of quantity and 93.22% of CBM) over 16,142 rows. Vinh Loc processes 19,652 units (6.98% of quantity and 6.78% of CBM) over 5,258 rows.
* **Bullet 5**: Operational Focus: Planning and resource allocation must remain focused on My Phuoc as the high-volume core.
* **Charts**: `Chart0.jpg`, `Chart1.jpg`

### Slide 5
* **Part 1**, **Part 2**, **Part 3**
* **Title**: Geographic Demand Mapping & Regional Concentration
* **Bullet 1**: Southeast Focus: Đông Nam Bộ is the dominant demand region, accounting for **47.36% of resolved quantity** (125,617 units) and 49% of orders.
* **Bullet 2**: Central & Mekong Hubs: Bắc Trung Bộ & Duyên hải miền Trung represents **25.49% of volume** (67,606 units), and Đồng bằng sông Cửu Long drives **15.16%** (40,204 units).
* **Bullet 3**: Top Provinces: Hồ Chí Minh City leads with 32.95% of orders and 27.47% of quantity (65,527 units). Bình Dương follows with 15.53% of orders and 18.03% of quantity (43,012 units).
* **Bullet 4**: Distance vs. Volume Correlation: Delivery distance is negatively correlated with order size. Close-by urban centers (HCMC and surrounding areas) order in high density and frequency.
* **Bullet 5**: Regional Logistics: Transportation routes must be optimized for HCMC-Binh Duong milk runs to handle the dense local demand.
* **Charts**: `Chart0.jpg`, `Chart1.jpg`

### Slide 6
* **Part 1**, **Part 2**, **Part 3**
* **Title**: Customer Segment Profiling: MT vs. TT
* **Modern Trade (MT) Profile**:
  * 132 active customers, 1,564 orders.
  * Orders are highly consolidated, averaging **80.19 pcs** and **5.16 m³**.
  * Narrow SKU breadth (2.84 SKUs/order) and concentrated in 34 provinces.
  * Highly pallet-centric (**75.25% of quantity** is shipped as full pallets). Carton picking is 22.52%, and loose picking is only 2.23%.
* **Traditional Trade (TT) Profile**:
  * 270 active customers, 3,782 orders.
  * Orders are small and fragmented, averaging **41.33 pcs** and **2.13 m³**.
  * Broad SKU breadth (4.33 SKUs/order) and dispersed across 60 provinces.
  * Highly carton-centric (**48.54%**) and loose-picking reliant (**9.77%**).
* **Synthesis**: MT requires high-volume pallet-loading bays; TT demands intensive piece-picking and carton-sorting zones.
* **Charts**: `Chart0.jpg`, `Chart1.jpg`

### Slide 7
* **Part 1**, **Part 2**, **Part 3**
* **Title**: Network Model Assessment & Channel Flow Profile
* **Bullet 1**: Two-RDC Footprint: My Phuoc (Binh Duong) and Vinh Loc (HCMC). Both warehouses handle mixed B2B and B2C flows.
* **Bullet 2**: Timeline Discrepancy: My Phuoc operates over the full 6 months (Jun–Nov). Vinh Loc is a new facility, operational in December only (1 month).
* **Bullet 3**: B2B Flow Dominance: B2B represents **99.2% of CBM** at My Phuoc and **99.7% of CBM** at Vinh Loc.
* **Bullet 4**: Year-End Surge: On a normalized daily basis, Vinh Loc processed B2B orders at a daily rate of 48.7 orders/active day, exceeding My Phuoc's 25.5 orders/active day, indicating strong December peak demands.
* **Bullet 5**: SLA Failure Modes: Standard RDC locations are too far (>10 km) from central districts to support HCMC B2C e-commerce same-day 2–4 hour delivery SLAs.
* **Charts**: `Chart0.jpg`

### Slide 8
* **Part 1**, **Part 2**, **Part 3**
* **Title**: HCMC SLA Feasibility & Dark Store Nodes
* **Bullet 1**: SLA Threshold: Set at a 25 km radius from existing RDCs to secure a 2–4 hour delivery SLA across HCMC (assuming 25 km/h urban transit).
* **Bullet 2**: Current Coverage: All 21 districts of HCMC lie within 25 km of Vinh Loc or My Phuoc. However, heavy traffic makes inner-city SLA fulfillment from RDCs highly volatile.
* **Bullet 3**: Node 1 (Bình Tân/Tân Phú Corridor): High-volume cluster (>50,000 units). Vinh Loc is situated 5–7 km away. Recommended to upgrade Vinh Loc's satellite capabilities.
* **Bullet 4**: Node 2 (District 1/3/Phú Nhuận CBD): Distance to RDCs is 14+ km. Establish a small urban dark store (200–300 m²) stocked with top A-X SKUs.
* **Bullet 5**: Order Split Logic: If HCMC address is < 25 km from Vinh Loc, route to Vinh Loc. If < 35 km from My Phuoc, route to My Phuoc. Otherwise, route via urban dark store.
* **Charts**: `Chart0.jpg`, `Chart1.jpg`

### Slide 9
* **Part 1**, **Part 2**, **Part 3**
* **Title**: Lead Time and Class A Safety Stock Optimization
* **Bullet 1**: Mile-Weighted Lead Time: RDC serves 6 regions. Weighting regional standard lead times by order shares results in a **weighted average lead time of 1.94 days**.
* **Bullet 2**: Regional Standards: Southeast is 1 day (49% of orders); Central is 3 days (19.2% of orders); Mekong Delta is 2 days (15.0% of orders); North is 4 days (9.4% of orders).
* **Bullet 3**: Safety Stock Model: Demand-uncertainty formula over 7 months (Jun–Dec 2025) at a 95% service level (Z = 1.645):
  `SS = Z * std_dev * sqrt(LT)`
* **Bullet 4**: Class A Results: Total safety stock across all 28 Class A SKUs is **12,168 units** under a pooled model.
* **Bullet 5**: Lead Time Sensitivity: Safety stock grows sub-linearly (sqrt(LT)). Lowering average lead time from 1.94 days to 1.0 day yields a 28.2% safety stock reduction (to 8,736 units).
* **Charts**: `Chart0.jpg`

### Slide 10
* **Part 1**, **Part 2**, **Part 3**
* **Title**: Inventory Pooling & Operational Control
* **Bullet 1**: Virtual Pooling Model: Merging B2B and B2C inventories into a single physical pool in WMS/OMS, rather than physically dedicating stock.
* **Bullet 2**: Financial Impact: Reduces total required safety stock by **61.8%** (12,168 units vs. 31,852 units), saving **19,684 units** of inventory.
* **Bullet 3**: Operational Rules: Enforce 6 controls: (R1) Common Pool; (R2) Per-channel ROP floors; (R3) Amber alert thresholds; (R4) Red conflict priority routing (MT first, TT last); (R5) SKU spike freezes; (R6) EOD rebalancing.
* **Bullet 4**: Model 2 Ergonomic Slotting: Sub-tiers Class A into A1 Pallet (pallet share > 40%), A2 Big-Face (carton share > 80% at waist-height), and A3 Mixed.
* **Bullet 5**: Expected Travel Distance Reduction: Model 2 yields a **77.5% expected travel-time reduction** (vs 51.6% for Model 1), driven by forklift aisle separation and waist-height picking for fast-movers.
* **Bullet 6**: Pick-and-Pack Processes: B2B utilizes total pallet picking and direct dock staging. B2C utilizes batch wave picking, trolley carts, and sort-consolidate QC.
* **Charts**: `Chart0.jpg`, `Chart1.jpg`

### Slide 11
* **Part 1**, **Part 2**, **Part 3**
* **Title**: Strategic Recommendations & Execution Roadmap
* **Bullet 1**: Deploy Virtual Inventory Pooling: Transition to a single physical WMS pool and implement the 6 conflict control rules (R1-R6) to capture the 61.8% safety stock savings.
* **Bullet 2**: Implement Model 2 Ergonomic Slotting: Reconfigure My Phuoc's layout to separate forklift pallet lanes (A1) from manual carton pick-faces (A2) to secure the 77.5% travel time reduction.
* **Bullet 3**: Establish HCMC Urban Fulfillment Network: Upgrade Vinh Loc's satellite capabilities to launch a pilot dark store in the Bình Tân/Tân Phú corridor, securing same-day B2C SLAs.
* **Bullet 4**: Resolve ERP Invoicing Bias: Correct invoicing-location logic in the ERP to ensure physical dispatches from Vinh Loc are not mistakenly attributed to My Phuoc.
* **Charts**: `Chart0.jpg`
