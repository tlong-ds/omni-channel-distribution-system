# Round 2 Executive Summary & Narrative Analysis

## Executive Summary

This report provides the outbound flow analysis, customer profiling, and geographic demand mapping for the Round 2 competition based on the transaction logs spanning June to December 2025. The core analysis focuses on the 6-month Assignment Window (July 1 – December 31, 2025), which contains **43,894 shipment rows**, **355,364.80 units of outbound demand**, and **19,653.78 CBM of volume**.

Key takeaways include:
1. **Extreme Assortment Concentration**: A tiny fraction of SKUs drives the vast majority of volume and warehouse activities. A dedicated 'Fast-Moving' group of 59 SKUs accounts for 65.06% of outbound quantity and 49.61% of order frequency.
2. **ERP Centralized Invoicing Distortion**: Geographic demand analyses reveal that My Phuoc seemingly dominates 92.22% of resolved volume. However, this is an artificial bias caused by centralized ERP invoicing. In reality, Vinh Loc's raw outbound shipments account for 28.75% of total volume, but 80.10% of its transactions have missing customer names and are excluded from standard maps. Using **Approach A (Statistical Scaling)**, we restore and analyze the true 71.25% My Phuoc vs 28.75% Vinh Loc volume split.
3. **Clear Segment Profiles**: Modern Trade orders are large, consolidated, and heavily palletized (69.17% of quantity). Traditional Trade orders are smaller, highly fragmented (51.49% carton / 8.07% loose), and spread across 57 provinces, presenting different operational picking requirements.

---

## Q1.1 Demand Pattern Classification (ABC-XYZ Analysis)

The product assortment was analyzed across two dimensions using a joint ABC-XYZ matrix based on outbound volume (Quantity) and transaction frequency (Order Frequency) over the last 6 months of 2025. The overall concentration of shipped volume across SKUs is shown in Figure \ref{fig:q11-abc-qty-dist}.

![Q1.1 ABC quantity distribution\label{fig:q11-abc-qty-dist}](../charts/q11_abc_quantity_distribution.png)

### Classification Thresholds
- **ABC Quantity Thresholds**: Class A (Top 80%), Class B (Next 15%), Class C (Bottom 5%)
- **XYZ Variability Thresholds**: Class X (CV $\le$ 0.50), Class Y (CV $\le$ 1.00), Class Z (CV > 1.00 or Low Sample)
- **Low-Sample Filter**: SKUs with fewer than 4 nonzero sales weeks are automatically downgraded to Class Z to prevent statistical skew.

### Joint ABC-XYZ Matrix Summary
A total of **572 unique SKUs** were classified. The product distribution across the ABC-XYZ matrix is shown in the summary table below:

| XYZ \ ABC | Class A (Top 80% Vol, 79 SKUs) | Class B (Next 15% Vol, 118 SKUs) | Class C (Bottom 5% Vol, 375 SKUs) |
| :--- | :---: | :---: | :---: |
| **Class X** (Stable demand) | 1 SKUs (0.17%) | 0 SKUs (0.00%) | 0 SKUs (0.00%) |
| **Class Y** (Variable demand) | 19 SKUs (3.32%) | 19 SKUs (3.32%) | 9 SKUs (1.57%) |
| **Class Z** (Irregular/Spiky) | 59 SKUs (10.31%) | 99 SKUs (17.31%) | 366 SKUs (63.99%) |

### Identification of the 'Fast-Moving' SKU Group
The **Fast-Moving** SKU group is defined as the intersection of Class A by Quantity and Class A by Order Frequency (Class A-A). This group is the primary driver of warehouse operational workload and inventory velocity.

- **SKU Count**: **59 SKUs** (representing **10.31%** of the total assortment).
- **Volume Contribution**: Accounts for **231211.92 units** (**65.06%** of total outbound volume).
- **Fulfillment Workload**: Drives **20615 orders** (**49.61%** of all outbound transaction lines).
- **Top 10 Fast-Moving SKUs**: `4200009163, 4200000163, 4200009000, 4200008101, 4200008999, 4200008102, 4200007858, 1830009179, 4200008229, 4200000164`.

> [!TIP]
> **Operational Recommendation**: Because only ~10% of the SKUs drive nearly 2/3 of all shipped quantities, these 59 SKUs should be assigned to the most ergonomic pick-faces (lower levels, close to the packing stations) with dedicated replenishment pathways to minimize picking travel time.

---

## Q1.2 Distribution Heatmap and Warehouse Imbalance Analysis

### 1. Data Quality and Resolution Ceiling
A critical finding from our data cleansing pipeline is a **severe geography resolution ceiling**:
- **Row-level coverage**: Only **36.69%** of transaction rows (16,104 out of 43,894) could be mapped to a known customer location.
- **Quantity-level coverage**: Only **44.92%** of outbound quantities (159,635.70 out of 355,364.80) are linked to known coordinates.
- **Root Cause**: `27,790` assignment-window rows are unresolved, of which **25,693 rows** are due to `Ship-to Customer` being logged as `'unknown'` in the database.

> [!IMPORTANT]
> **Central Invoicing Data Bias**: This missing customer data is systemic:
> - **Centralization (Pre-Dec 2025)**: Customer billing was centralized under My Phuoc's ERP account. Consequently, Vinh Loc shipments (representing Tefal products) were logged as internal stock depletion entries without customer details, affecting **80.10%** of Vinh Loc rows.
> - **Migration (Dec 2025)**: Billing migrated to Vinh Loc, causing My Phuoc's December transactions to lack customer details.
> - **Operational Impact**: Vinh Loc is left with an extremely low geographic coverage of **12.12% of its volume**, skewing all raw geographic charts to make Vinh Loc look artificially inactive. This systematic bias and the resulting spatial coverage limits are visualized in Figure \ref{fig:q12-geo-coverage}.

![Q1.2 Geography coverage map\label{fig:q12-geo-coverage}](../charts/q12_geography_coverage_map.png)

### 2. Corrected Warehouse Imbalance (Approach A: Statistical Scaling)
To provide a safe and unbiased view of warehouse throughput, we compare raw volume totals against resolved volumes and apply **Approach A (Statistical Scaling)**:

| Metric | My Phuoc Warehouse | Vinh Loc Warehouse | Total |
| :------------------------------------------- | :-----------------: | :-----------------: | :-----------------: |
| **Raw Outbound Quantity** | 253,197.00 (71.25%) | 102,167.80 (28.75%) | 355,364.80 (100.0%) |
| **Raw Outbound CBM** | 13,948.74 (70.97%) | 5,705.04 (29.03%) | 19,653.78 (100.0%) |
| **Raw Transaction Rows** | 17,423 (39.70%) | 26,471 (60.30%) | 43,894 (100.0%) |
| **Resolved Quantity (Raw)** | 147,258.80 (92.25%) | 12,382.80 (7.75%) | 159,635.70 (100.0%) |
| **Imputed Quantity (Approach A)** | **253,196.01 (71.25%)** | **102,168.32 (28.75%)** | **355,364.33 (100.0%)** |

**Conclusion**: While Vinh Loc represents 60.30% of transaction rows (small, frequent orders of Tefal items), it accounts for 28.75% of outbound quantity. My Phuoc handles 71.25% of the quantity. The raw resolved geography is heavily biased (92% vs 8%), but the true operational split is **71% My Phuoc vs 29% Vinh Loc**. The comparison of raw, resolved, and imputed throughput is detailed in the table above, while the regional warehouse dominance gap in the resolved transactions is shown in Figure \ref{fig:q12-wh-imbalance}.

![Q1.2 Warehouse imbalance\label{fig:q12-wh-imbalance}](../charts/q12_warehouse_imbalance.png)

### 3. Regional Demand and Top Clusters
To define the geographic boundaries of our analysis, the standard Vietnam administrative regions are mapped in Figure \ref{fig:q12-vn-regions}.

![Q1.2 Vietnam regioning map\label{fig:q12-vn-regions}](../charts/q12_region_reference_map.png){width=50%}

Within these boundaries, the resolved outbound demand is highly concentrated. As shown in Figure \ref{fig:q12-region-qty}, the region-level order and quantity shares are led by the following regions:
- **Đông Nam Bộ**: The largest demand region, accounting for **42.78%** of resolved volume (68,289.44 units).
- **Bắc Trung Bộ và Duyên hải miền Trung**: The second largest, representing **28.22%** (45,044.48 units).
- **Đồng bằng sông Cửu Long**: Accounts for **13.86%** (22,132.83 units).

![Q1.2 Regional quantity\label{fig:q12-region-qty}](../charts/q12_region_quantity_orders.png)

#### Top Customer Clusters (Provinces)
At the provincial level, demand clusters heavily around key urban centers. The absolute volume hotspots are highlighted in the top demand provinces map (see Figure \ref{fig:q12-top-provinces}).

![Q1.2 Top demand provinces map\label{fig:q12-top-provinces}](../charts/q12_top_demand_provinces_map.png){width=50%}

Specifically, the top five provinces by resolved volume and order counts are led by Hồ Chí Minh City by an overwhelming margin:
- **Hồ Chí Minh**: 1,267 orders, 42,256.09 quantity (representing **34.62% of resolved orders** and **26.47% of resolved quantity**).
- **Đồng Nai**: 387 orders, 5,579.33 quantity.
- **Bình Dương**: 194 orders, 19,814.17 quantity (high volume per order).
- **Đà Nẵng**: 204 orders, 15,522.98 quantity (Central hub).
- **Cần Thơ**: 177 orders, 10,561.08 quantity (Mekong Delta hub).

To visualize the full provincial distribution across the nation, Figure \ref{fig:q12-province-demand} displays the provincial demand choropleth maps (by total quantity and total orders).

![Q1.2 Province demand maps\label{fig:q12-province-demand}](../charts/q12_province_demand_choropleths.png)

### 4. Fulfillment Splits and Spatial Dynamics
To understand how fulfillment is shared between the facilities, we examine the warehouse-region throughput split.

#### Warehouse-Region Fulfillment Splits
Because My Phuoc holds Fans and Vinh Loc holds Tefal, both warehouses ship to the same regions to fulfill their respective product lines. This regional throughput distribution is visualized in Figure \ref{fig:q12-wh-region-split}.

![Q1.2 Warehouse-region split\label{fig:q12-wh-region-split}](../charts/q12_warehouse_region_quantity_split.png)

However, due to the centralized billing bias, My Phuoc appears dominant in almost all regions. This dominance pattern and the resulting spatial market coverage of both warehouses are mapped in Figure \ref{fig:q12-wh-dominance}.

![Q1.2 Warehouse dominance map\label{fig:q12-wh-dominance}](../charts/q12_warehouse_dominance_map.png){width=50%}

#### Distance vs. Demand Size Correlation
We also analyze the relationship between delivery distance and order characteristics. There is a clear spatial correlation between order size (CBM) and delivery distance, showing that close-by urban centers (HCMC and surrounding areas) order in higher density and frequency, as illustrated in the scatter plot in Figure \ref{fig:q12-dist-correlation}.

![Q1.2 Province distance correlation\label{fig:q12-dist-correlation}](../charts/q12_province_distance_correlation.png)

#### Urban vs. Provincial Demand Split
Finally, we segment the outbound volume into urban centers (HCMC, Hanoi, Da Nang, Can Tho, Haiphong) versus the remaining provinces. As shown in Figure \ref{fig:q12-urban-provincial}, urban centers drive a disproportionately large and concentrated volume compared to the more fragmented provincial demand.

![Q1.2 Urban and provincial split\label{fig:q12-urban-provincial}](../charts/q12_urban_provincial_split.png){width=70%}

---

## Q1.3 Customer Segment Order Profile Comparison

We compared the order profiles of **Modern Trade (MT)** (large retail accounts like Co.op Mart, Lotte, etc.) and **Traditional Trade / Distributor (TT)**.

### Key Profile Comparison Table
The comparison across the required dimensions is summarized below:

| Dimension | Modern Trade (MT) | Traditional Trade / Distributor (TT) |
| :--- | :---: | :---: |
| **Active Customers** | 117 | 253 |
| **Order Count** | 1315 | 3258 |
| **Avg. Order Quantity** | 65.02 units | 37.73 units |
| **Avg. Order Volume (CBM)** | 4.12 m³ | 1.91 m³ |
| **Avg. SKU Breadth / Order** | 3.09 SKUs | 4.43 SKUs |
| **Order Frequency (per customer/month)** | 1.87 | 2.15 |
| **Geographic Footprint** | 41 provinces / 6 regions | 57 provinces / 6 regions |
| **Avg. Delivery Distance** | 341.80 km | 298.76 km |
| **Pallet Share (%)** | **69.17%** | **40.44%** |
| **Carton Share (%)** | **27.57%** | **51.49%** |
| **Loose Share (%)** | **3.25%** | **8.07%** |

### Key Profile Insights
1. **Order Size & Consolidation**: Modern Trade orders are highly consolidated and large, averaging **65.02 units** and **4.12 CBM** per order. Traditional Trade orders are much smaller and fragmented, averaging **37.73 units** and **1.91 CBM**. This comparison of order metrics is visualised in Figure \ref{fig:q13-order-profile}.

![Q1.3 Order profile comparison\label{fig:q13-order-profile}](../charts/q13_order_profile_comparison.png){width=85%}

2. **Assortment Breadth vs. Depth**: As shown in Figure \ref{fig:q13-order-profile}, Traditional Trade orders have a higher average SKU breadth (**4.43 SKUs** per order) than Modern Trade (**3.09 SKUs**). This indicates that TT customers order small quantities of a wide variety of SKUs, increasing warehouse sorting complexity.

3. **Packaging Unit Mix**: Modern Trade is highly pallet-centric, with **69.17%** of their items shipped as full pallets. Traditional Trade is highly carton-centric (**51.49%** of items) and has more loose picking (**8.07%** vs. 3.25% for MT). This breakdown of packaging unit selections is compared in Figure \ref{fig:q13-pkg-mix}.

![Q1.3 Packaging mix\label{fig:q13-pkg-mix}](../charts/q13_packaging_mix.png)

4. **Geographic Spread**: Traditional Trade has a much wider geographic spread, covering **57 provinces** compared to MT's **41 provinces**, representing a highly fragmented, nation-wide distribution profile. The count of active provinces and regions for each segment is shown in Figure \ref{fig:q13-geo-spread}.

![Q1.3 Geographic spread\label{fig:q13-geo-spread}](../charts/q13_geographic_spread.png)

To see the spatial distribution of these sales, Figure \ref{fig:q13-segment-geo-maps} shows the choropleth maps of MT and TT customer demand across Vietnam.

![Q1.3 Segment geography maps\label{fig:q13-segment-geo-maps}](../charts/q13_segment_geographic_maps.png)
