# Slide-by-Slide Content and Layout Mapping Report

This report defines a slide-by-slide mapping of the logistics data analysis and omni-channel strategy for an 11-slide presentation based on the Round 2 analysis. It leverages the visual and structural design rules in the presentation template and the specific charts generated.

---

## Slide 1: Introduction (Title)
* **Title**: Omni-Channel Logistics & Supply Chain Strategy
* **Subtitle**: Data-Driven Optimization for Multi-Channel Operations, Inventory Control, and Warehouse Slotting
* **Template Layout**: Title Slide (Layout 1: `slideLayout1.xml`)
* **Content & Narrative**:
  - Introduction of the strategic logistics assessment based on June–December 2025 transaction logs.
  - Objective: Redesigning the distribution network, optimizing inventory safety stocks, and restructuring warehouse operations to support B2B and B2C channels.
  - Presenter: Omni-Channel Strategy Team
* **Visuals & Charts**:
  - Theme-matching red and white title screen from the template.
  - No data charts on the title slide.

---

## Slide 2: Executive Summary (Highlights of key insights across parts)
* **Title**: Executive Summary: Key Operational Insights
* **Template Layout**: Two Content (Layout 4: `slideLayout4.xml`)
* **Content & Narrative**:
  - **Left Column: Supply & Demand Insights**
    - *Extreme SKU Concentration*: A tiny core of 19 "Fast-Moving" A-X SKUs (4.04% of assortment) drives 57.87% of outbound quantity and 25.88% of pick transactions.
    - *Centralized Invoicing Distortion*: Resolved data initially showed a 92.59% My Phuoc bias. Statistical scaling restored the true operational split: 93% My Phuoc vs. 7% Vinh Loc.
  - **Right Column: Fulfillment & Operations Insights**
    - *Distinct Segment Profiles*: Modern Trade orders are large, consolidated, and pallet-centric (75.25% pallet share). Traditional Trade orders are small, fragmented (48.54% carton, 9.77% loose), and spread across 60 provinces.
    - *Virtual Inventory Pooling*: Merging channel safety stocks under a mile-weighted lead time of 1.94 days yields a **61.8% inventory reduction** (12,168 units vs. 31,852 units).
    - *Ergonomic Slotting*: Model 2 (ABC + Ergonomics) achieves a **77.5% expected travel time reduction**, exceeding the 30% peak improvement target.
* **Visuals & Charts**:
  - No charts are placed here to maintain a clean, text-driven summary slide.

---

## Slide 3: SKU Demand Classification (Part 1 Q1.1)
* **Title**: SKU Demand Pattern Classification (ABC-XYZ Analysis)
* **Template Layout**: Two Content (Layout 4: `slideLayout4.xml`)
* **Content & Narrative**:
  - **Left Column: Classification Methodology & Key Findings**
    - *Assortment Classification*: 470 unique SKUs evaluated across volume (ABC) and transaction frequency (XYZ) over 7 months.
    - *ABC Volume Concentration*: Class A (Top 70% quantity) includes 28 SKUs; Class B (Next 20%) includes 39 SKUs; Class C (Bottom 10%) includes 403 SKUs.
    - *XYZ Frequency Concentration*: Class X (Top 70% orders) includes 53 SKUs; Class Y (Next 20%) includes 88 SKUs; Class Z (Bottom 10%) includes 329 SKUs.
    - *The Fast-Moving Group (A-X)*: 19 SKUs (4.04%) drive **57.87% of outbound quantity** (163,014 units) and **25.88% of pick transactions** (5,381 orders).
  - **Right Column: Operational Recommendations**
    - Dedicated replenishment and lower pick-face positioning (levels 1 and 2) must be reserved for the 19 A-X SKUs to minimize travel time.
    - Rationalize or store in deep reserve the 329 C-Z slow-moving SKUs (70.0% of assortment).
* **Visuals & Charts**:
  - `outputs/round2/charts/q11_abc_xyz_matrix_frequency.png` (illustrates the SKU count distribution across the 9 cells of the ABC-XYZ frequency matrix)
  - `outputs/round2/charts/q11_abc_quantity_distribution.png` (shows the Pareto distribution of SKU quantity)

---

## Slide 4: Warehouse Throughput Imbalance & Geography Coverage (Part 1 Q1.2)
* **Title**: Warehouse Throughput Analysis & Data Quality
* **Template Layout**: Two Content (Layout 4: `slideLayout4.xml`)
* **Content & Narrative**:
  - **Left Column: Data Quality & Coverage**
    - *High Geocoding Resolution*: The data cleansing pipeline successfully resolved 97.12% of transaction rows and 94.15% of outbound quantities to specific coordinates.
    - *Database Gaps*: 617 rows were left unresolved due to 'unknown' Ship-to Customers in the source logs.
  - **Right Column: Throughput Imbalance & Invoicing Distortion**
    - *Centralized Invoicing Distortion*: ERP invoicing initially attributes 92.59% of resolved volume to My Phuoc. Utilizing Statistical Scaling (Approach A), we restore the true 93.02% vs. 6.98% operational split.
    - *Throughput Realities*: My Phuoc processes 262,053 units (93.02% of quantity and 93.22% of CBM) over 16,142 rows. Vinh Loc processes 19,652 units (6.98% of quantity and 6.78% of CBM) over 5,258 rows.
    - *Operational Focus*: Planning and resource allocation must remain focused on My Phuoc as the high-volume core.
* **Visuals & Charts**:
  - `outputs/round2/charts/q12_warehouse_imbalance.png` (bar chart comparing raw and resolved warehouse throughput shares)
  - `outputs/round2/charts/q12_geography_coverage_map.png` (Vietnam map indicating resolved vs. unresolved transaction locations)

---

## Slide 5: Regional & Provincial Demand Distribution (Part 1 Q1.2)
* **Title**: Geographic Demand Mapping & Regional Concentration
* **Template Layout**: Two Content (Layout 4: `slideLayout4.xml`)
* **Content & Narrative**:
  - **Left Column: Regional Concentration**
    - *Southeast Focus*: Đông Nam Bộ is the dominant demand region, accounting for **47.36% of resolved quantity** (125,617 units) and 49% of orders.
    - *Central & Mekong Hubs*: Bắc Trung Bộ & Duyên hải miền Trung represents **25.49% of volume** (67,606 units), and Đồng bằng sông Cửu Long drives **15.16%** (40,204 units).
    - *Top Provinces*: Hồ Chí Minh City leads with 32.95% of orders and 27.47% of quantity (65,527 units). Bình Dương follows with 15.53% of orders and 18.03% of quantity (43,012 units).
  - **Right Column: Spatial Distance Dynamics**
    - *Distance vs. Volume Correlation*: Delivery distance is negatively correlated with order size. Close-by urban centers (HCMC and surrounding areas) order in high density and frequency.
    - *Regional Logistics*: Transportation routes must be optimized for HCMC-Binh Duong milk runs to handle the dense local demand.
* **Visuals & Charts**:
  - `outputs/round2/charts/q12_region_quantity_orders.png` (donut chart showing regional volume and order distribution)
  - `outputs/round2/charts/q12_province_distance_correlation.png` (scatter plot illustrating order size relative to distance)

---

## Slide 6: Customer Segment Comparison: MT vs. TT (Part 1 Q1.3)
* **Title**: Customer Segment Profiling: Modern Trade vs. Traditional Trade
* **Template Layout**: Comparison (Layout 5: `slideLayout5.xml`)
* **Content & Narrative**:
  - **Left Column: Modern Trade (MT) Profile**
    - *Scale & Orders*: 132 active customers, 1,564 orders. Orders are highly consolidated, averaging **80.19 pcs** and **5.16 m³**.
    - *Assortment & Geography*: Narrow SKU breadth (2.84 SKUs/order) and concentrated in 34 provinces.
    - *Packaging Unit Mix*: Highly pallet-centric (**75.25% of quantity** is shipped as full pallets). Carton picking is 22.52%, and loose picking is only 2.23%.
  - **Right Column: Traditional Trade (TT) Profile**
    - *Scale & Orders*: 270 active customers, 3,782 orders. Orders are small and fragmented, averaging **41.33 pcs** and **2.13 m³**.
    - *Assortment & Geography*: Broad SKU breadth (4.33 SKUs/order) and dispersed across 60 provinces.
    - *Packaging Unit Mix*: Highly carton-centric (**48.54%**) and loose-picking reliant (**9.77%**).
  - **Operational Synthesis**: MT requires high-volume pallet-loading bays; TT demands intensive piece-picking and carton-sorting zones.
* **Visuals & Charts**:
  - `outputs/round2/charts/q13_order_profile_comparison.png` (bar chart comparing average qty, volume, breadth, and distance)
  - `outputs/round2/charts/q13_packaging_mix.png` (stacked bar comparing packaging unit shares)

---

## Slide 7: Omni-Channel Network Model & Channel Flow Analysis (Part 2 Q2.1)
* **Title**: Network Model Assessment & Channel Flow Profile
* **Template Layout**: Two Content (Layout 4: `slideLayout4.xml`)
* **Content & Narrative**:
  - **Left Column: RDC Network and Timelines**
    - *Two-RDC Footprint*: My Phuoc (Binh Duong) and Vinh Loc (HCMC). Both warehouses handle mixed B2B and B2C flows.
    - *Timeline Discrepancy*: My Phuoc operates over the full 6 months (Jun–Nov). Vinh Loc is a new facility, operational in December only (1 month).
    - *B2B Flow Dominance*: B2B represents **99.2% of CBM** at My Phuoc and **99.7% of CBM** at Vinh Loc.
  - **Right Column: Operating Rates & Channel Tension**
    - *Year-End Surge*: On a normalized daily basis, Vinh Loc processed B2B orders at a daily rate of 48.7 orders/active day, exceeding My Phuoc's 25.5 orders/active day, indicating strong December peak demands.
    - *SLA Failure Modes*: Standard RDC locations are too far (>10 km) from central districts to support HCMC B2C e-commerce same-day 2–4 hour delivery SLAs.
* **Visuals & Charts**:
  - `outputs/round2/charts/q21_channel_flow_profile.png` (bar chart showing B2B vs. B2C order and volume rates per day for both RDCs)

---

## Slide 8: Urban SLA Assessment & Dark Store Strategy (Part 2 Q2.1)
* **Title**: HCMC SLA Feasibility & Dark Store Nodes
* **Template Layout**: Two Content (Layout 4: `slideLayout4.xml`)
* **Content & Narrative**:
  - **Left Column: Proximity & SLA Feasibility**
    - *SLA Threshold*: Set at a 25 km radius from existing RDCs to secure a 2–4 hour delivery SLA across HCMC (assuming 25 km/h urban transit).
    - *Current Coverage*: All 21 districts of HCMC lie within 25 km of Vinh Loc or My Phuoc. However, heavy traffic makes inner-city SLA fulfillment from RDCs highly volatile.
  - **Right Column: Dark Store Strategy & Routing**
    - *Node 1 (Bình Tân/Tân Phú Corridor)*: High-volume cluster (>50,000 units). Vinh Loc is situated 5–7 km away. Recommended to upgrade Vinh Loc's satellite capabilities.
    - *Node 2 (District 1/3/Phú Nhuận CBD)*: Distance to RDCs is 14+ km. Establish a small urban dark store (200–300 m²) stocked with top A-X SKUs.
    - *Order Split Logic*: If HCMC address is < 25 km from Vinh Loc, route to Vinh Loc. If < 35 km from My Phuoc, route to My Phuoc. Otherwise, route via urban dark store.
* **Visuals & Charts**:
  - `outputs/round2/charts/q21_network_coverage.png` (map and scatter plot showing district distances to RDCs vs. B2B quantity)
  - `outputs/round2/charts/q21_hcm_district_volume.png` (column chart ranking HCMC districts by B2B quantity)

---

## Slide 9: Lead Time & Safety Stock Analysis (Part 2 Q2.2)
* **Title**: Lead Time and Class A Safety Stock Optimization
* **Template Layout**: Two Content (Layout 4: `slideLayout4.xml`)
* **Content & Narrative**:
  - **Left Column: Lead Time Profiling**
    - *Mile-Weighted Lead Time*: RDC serves 6 regions. Weighting regional standard lead times by order shares results in a **weighted average lead time of 1.94 days**.
    - *Regional Standards*: Southeast is 1 day (49% of orders); Central is 3 days (19.2% of orders); Mekong Delta is 2 days (15.0% of orders); North is 4 days (9.4% of orders).
  - **Right Column: Safety Stock Determination**
    - *Safety Stock Model*: Simplified demand-uncertainty formula over 7 months (Jun–Dec 2025) at a 95% service level ($Z = 1.645$):
      $$SS = Z \cdot \sigma_{daily} \cdot \sqrt{LT_{avg}}$$
    - *Class A Results*: Total safety stock across all 28 Class A SKUs is **12,168 units** under a pooled model.
    - *Lead Time Sensitivity*: Safety stock grows sub-linearly ($\sqrt{LT}$). Lowering average lead time from 1.94 days to 1.0 day yields a 28.2% safety stock reduction (to 8,736 units).
* **Visuals & Charts**:
  - `outputs/round2/charts/q22_lead_time_sensitivity.png` (line chart showing Class A Safety Stock requirements relative to replenishment lead time in days)

---

## Slide 10: Virtual Inventory Pooling Strategy & Operations Summary (Part 2 Q2.2 & Part 3)
* **Title**: Inventory Pooling & Operational Control
* **Template Layout**: Comparison (Layout 5: `slideLayout5.xml`)
* **Content & Narrative**:
  - **Left Column: Virtual Pooling & Savings**
    - *Virtual Pooling Model*: Merging B2B and B2C inventories into a single physical pool in WMS/OMS, rather than physically dedicating stock.
    - *Financial Impact*: Reduces total required safety stock by **61.8%** (12,168 units vs. 31,852 units), saving **19,684 units** of inventory.
    - *Operational Rules*: Enforce 6 controls: (R1) Common Pool; (R2) Per-channel ROP floors; (R3) Amber alert thresholds; (R4) Red conflict priority routing (MT first, TT last); (R5) SKU spike freezes; (R6) EOD rebalancing.
  - **Right Column: Part 3 Warehouse Operations Summary**
    - *Model 2 Ergonomic Slotting*: Sub-tiers Class A into A1 Pallet (pallet share > 40%), A2 Big-Face (carton share > 80% at waist-height), and A3 Mixed.
    - *Expected Travel Distance Reduction*: Model 2 yields a **77.5% expected travel-time reduction** (vs 51.6% for Model 1), driven by forklift aisle separation and waist-height picking for fast-movers.
    - *Pick-and-Pack Processes*: B2B utilizes total pallet picking and direct dock staging. B2C utilizes batch wave picking, trolley carts, and sort-consolidate QC.
* **Visuals & Charts**:
  - `outputs/round2/charts/q22_inventory_pooling.png` (bar chart comparing separated vs. pooled safety stock)
  - `outputs/round2/charts/q31_slotting_analysis.png` (chart comparing picker travel distance across slotting scenarios)

---

## Slide 11: Conclusion (Strategic Recommendations)
* **Title**: Strategic Recommendations & Execution Roadmap
* **Template Layout**: Title and Content (Layout 2: `slideLayout2.xml`)
* **Content & Narrative**:
  - **Immediate Actions (Q1–Q2)**:
    - *Deploy Virtual Inventory Pooling*: Transition to a single physical WMS pool and implement the 6 conflict control rules (R1-R6) to capture the 61.8% safety stock savings.
    - *Implement Model 2 Ergonomic Slotting*: Reconfigure My Phuoc's layout to separate forklift pallet lanes (A1) from manual carton pick-faces (A2) to secure the 77.5% travel time reduction.
  - **Mid-Term Expansion (Q3–Q4)**:
    - *Establish HCMC Urban Fulfillment Network*: Upgrade Vinh Loc's satellite capabilities to launch a pilot dark store in the Bình Tân/Tân Phú corridor, securing same-day B2C SLAs.
    - *Resolve ERP Invoicing Bias*: Correct invoicing-location logic in the ERP to ensure physical dispatches from Vinh Loc are not mistakenly attributed to My Phuoc.
* **Visuals & Charts**:
  - `outputs/round2/charts/q32_pick_pack_flowchart.png` (diagram mapping out the omni-channel pick-and-pack workflow and stock conflict escalation logic)
