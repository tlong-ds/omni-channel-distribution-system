import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import subprocess

from src.logage2026.config import NOTES_DIR


NOTE_FILENAME = "part1_question_summary.tex"


def write_notes(
    shipments: pd.DataFrame,
    abc_xyz: pd.DataFrame,
    abc_xyz_matrix_frequency: pd.DataFrame,
    abc_xyz_matrix_volatility: pd.DataFrame,
    fast_moving_summary: pd.DataFrame,
    classification_metadata: pd.DataFrame,
    missing_data_summary: pd.DataFrame,
    geography_coverage_summary: pd.DataFrame,
    warehouse_region_summary: pd.DataFrame,
    customer_cluster_summary: pd.DataFrame,
    warehouse_imbalance_summary: pd.DataFrame,
    q12_region_orders_quantity_summary: pd.DataFrame,
    q12_province_cluster_summary: pd.DataFrame,
    q12_province_demand_summary: pd.DataFrame,
    q12_province_warehouse_dominance_summary: pd.DataFrame,
    q12_urban_provincial_summary: pd.DataFrame,
    q12_warehouse_imbalance_visual_summary: pd.DataFrame,
    q13_segment_profile_summary: pd.DataFrame,
    q13_segment_packaging_summary: pd.DataFrame,
    q13_segment_geographic_spread_summary: pd.DataFrame,
) -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    metadata = classification_metadata.iloc[0] if not classification_metadata.empty else None
    
    geo_cov = geography_coverage_summary.iloc[0] if not geography_coverage_summary.empty else None
    fast_mov = fast_moving_summary.iloc[0] if not fast_moving_summary.empty else None
    
    # Extract segments
    segments = {row['customer_segment']: row for _, row in q13_segment_profile_summary.iterrows()}
    mt_prof = segments.get("Modern Trade")
    tt_prof = segments.get("Traditional Trade / Distributor")
    
    # Extract segment packaging shares
    mt_pkg = q13_segment_packaging_summary[q13_segment_packaging_summary['customer_segment'] == 'Modern Trade']
    tt_pkg = q13_segment_packaging_summary[q13_segment_packaging_summary['customer_segment'] == 'Traditional Trade / Distributor']
    
    mt_pkg_shares = {row['packaging_unit']: row['quantity_share'] for _, row in mt_pkg.iterrows()}
    tt_pkg_shares = {row['packaging_unit']: row['quantity_share'] for _, row in tt_pkg.iterrows()}
    
    # Build dictionary of matrix cells
    matrix_dict = {}
    for _, row in abc_xyz_matrix_frequency.iterrows():
        matrix_dict[(row['abc_quantity'], row['xyz_frequency'])] = {
            'sku_count': int(row['sku_count']),
            'quantity': float(row['quantity']),
        }
        
    def get_cell_text(abc, xyz):
        cell = matrix_dict.get((abc, xyz))
        if cell is None:
            return "0 SKUs (0.00\\%)"
        sku_count = cell['sku_count']
        total_skus = len(abc_xyz)
        sku_share = sku_count / total_skus if total_skus else 0.0
        return f"{sku_count} SKUs ({sku_share * 100:.2f}\\%)"
        
    total_skus = len(abc_xyz)
    class_a_skus = len(abc_xyz[abc_xyz['abc_quantity'] == 'A'])
    class_b_skus = len(abc_xyz[abc_xyz['abc_quantity'] == 'B'])
    class_c_skus = len(abc_xyz[abc_xyz['abc_quantity'] == 'C'])
    
    class_x_freq = len(abc_xyz[abc_xyz['xyz_frequency'] == 'X'])
    class_y_freq = len(abc_xyz[abc_xyz['xyz_frequency'] == 'Y'])
    class_z_freq = len(abc_xyz[abc_xyz['xyz_frequency'] == 'Z'])
    
    fast_mov_sku_share = fast_mov['sku_count'] / total_skus if total_skus else 0.0

    ax_count = matrix_dict.get(('A', 'X'), {}).get('sku_count', 0)
    ay_az_count = matrix_dict.get(('A', 'Y'), {}).get('sku_count', 0) + matrix_dict.get(('A', 'Z'), {}).get('sku_count', 0)
    bx_cx_count = matrix_dict.get(('B', 'X'), {}).get('sku_count', 0) + matrix_dict.get(('C', 'X'), {}).get('sku_count', 0)
    cz_count = matrix_dict.get(('C', 'Z'), {}).get('sku_count', 0)

    def pct(val):
        return f"{val * 100:.2f}\\%"
        
    def pct0(val):
        return f"{val * 100:.0f}\\%"

    text = [
        r"% Options for packages loaded elsewhere",
        r"\PassOptionsToPackage{unicode}{hyperref}",
        r"\PassOptionsToPackage{hyphens}{url}",
        r"%",
        r"\documentclass[11pt]{article}",
        r"\usepackage{amsmath,amssymb}",
        r"\usepackage{iftex}",
        r"\ifPDFTeX",
        r"  \usepackage[T1]{fontenc}",
        r"  \usepackage[utf8]{inputenc}",
        r"  \usepackage{textcomp}",
        r"\else",
        r"  \usepackage{unicode-math}",
        r"  \defaultfontfeatures{Scale=MatchLowercase}",
        r"  \defaultfontfeatures[\rmfamily]{Ligatures=TeX,Scale=1}",
        r"\fi",
        r"\usepackage{lmodern}",
        r"\usepackage{xcolor}",
        r"\usepackage{booktabs}",
        r"\usepackage{array}",
        r"\usepackage{graphicx}",
        r"\usepackage{float}",
        r"\usepackage{geometry}",
        r"\geometry{a4paper, margin=1in}",
        r"\usepackage{bookmark}",
        r"\hypersetup{",
        r"  hidelinks,",
        r"  pdfcreator={LaTeX}",
        r"}",
        r"\author{}",
        r"\date{}",
        r"",
        r"\begin{document}",
        r"",
        r"\section{Round 2 Executive Summary \& Narrative Analysis}\label{round-2-executive-summary-narrative-analysis}",
        r"",
        r"\subsection{Executive Summary}\label{executive-summary}",
        r"",
        f"This report provides the outbound flow analysis, customer profiling, and geographic demand mapping for the Round 2 competition based on the transaction logs spanning June to December 2025. The core analysis focuses on the 7-month Assignment Window (June 1 -- December 31, 2025), which contains \\textbf{{{len(shipments):,} shipment rows}}, \\textbf{{{shipments['quantity'].sum():,.2f} units of outbound demand}}, and \\textbf{{{shipments['cbm_total'].sum():,.2f} m³ of volume}}.",
        r"",
        r"Key takeaways include:",
        r"\begin{enumerate}",
        f"\\item \\textbf{{Extreme Assortment Concentration}}: A tiny fraction of SKUs drives the vast majority of volume and warehouse activities. A dedicated ``Fast-Moving'' group of {fast_mov['sku_count']} SKUs accounts for {pct(fast_mov['quantity_share'])} of outbound quantity and {pct(fast_mov['frequency_share'])} of order frequency.",
        r"\item \textbf{ERP Centralized Invoicing Distortion}: Geographic demand analyses reveal that My Phuoc seemingly dominates 92.22\% of resolved volume. However, this is an artificial bias caused by centralized ERP invoicing. In reality, Vinh Loc's raw outbound shipments account for 28.75\% of total volume, but 80.10\% of its transactions have missing customer names and are excluded from standard maps. Using \textbf{Approach A (Statistical Scaling)}, we restore and analyze the true 71.25\% My Phuoc vs 28.75\% Vinh Loc volume split.",
        r"\item \textbf{Clear Segment Profiles}: Modern Trade orders are large, consolidated, and heavily palletized (69.17\% of quantity). Traditional Trade orders are smaller, highly fragmented (51.49\% carton / 8.07\% loose), and spread across 57 provinces, presenting different operational picking requirements.",
        r"\end{enumerate}",
        r"",
        r"\subsection{Q1.1 Demand Pattern Classification (ABC-XYZ Analysis)}\label{q1.1-demand-pattern-classification-abc-xyz-analysis}",
        r"",
        r"The product assortment was analyzed across two dimensions using a joint ABC-XYZ matrix based on outbound volume (Quantity) and transaction frequency (Order Frequency) over June to December 2025.",
        r"",
        r"\subsubsection{Classification Thresholds}\label{classification-thresholds}",
        r"\begin{itemize}",
        f"\\item \\textbf{{ABC Quantity Thresholds}}: Class A (Top {pct0(metadata['abc_a_threshold'])}), Class B (Next {pct0(metadata['abc_b_threshold'] - metadata['abc_a_threshold'])}), Class C (Bottom {pct0(1 - metadata['abc_b_threshold'])})",
        f"\\item \\textbf{{XYZ Frequency Thresholds}}: Class X (Top {pct0(metadata['abc_a_threshold'])}), Class Y (Next {pct0(metadata['abc_b_threshold'] - metadata['abc_a_threshold'])}), Class Z (Bottom {pct0(1 - metadata['abc_b_threshold'])})",
        f"\\item \\textbf{{Q1.1 Variability Basis}}: {metadata['q11_variability_grain'].title()} demand buckets from {metadata['q11_variability_period_start']} to {metadata['q11_variability_period_end']} with document types {metadata['q11_document_types']}.",
        r"\end{itemize}",
        r"",
        r"\subsubsection{ABC Volume (Quantity) and Order Frequency Distributions}\label{distributions}",
        r"The distribution of outbound quantities and order frequencies across the SKUs shows a high concentration. Most shipped volumes and orders are driven by a small fraction of the assortment, as visualized in Figures \ref{fig:q11-abc-qty-dist} and \ref{fig:q11-xyz-freq-dist}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q11_abc_quantity_distribution.png}",
        r"\caption{Q1.1 ABC quantity distribution}",
        r"\label{fig:q11-abc-qty-dist}",
        r"\end{figure}",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q11_xyz_frequency_distribution.png}",
        r"\caption{Order Frequency Distribution by XYZ Class}",
        r"\label{fig:q11-xyz-freq-dist}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Joint ABC-XYZ Matrix Summary}\label{joint-abc-xyz-matrix-summary}",
        f"A total of \\textbf{{{total_skus} unique SKUs}} were classified. The product distribution across the ABC-XYZ matrix (using ABC by Quantity) is shown in Figure \\ref{{fig:q11-abc-xyz-matrix}}:",
        r"In this matrix:",
        r"\begin{itemize}",
        f"\\item \\textbf{{ABC Quantity Class (Y-axis)}}: Classifies SKUs based on their contribution to total outbound quantity (Class A: top {pct0(metadata['abc_a_threshold'])}, Class B: next {pct0(metadata['abc_b_threshold'] - metadata['abc_a_threshold'])}, Class C: bottom {pct0(1 - metadata['abc_b_threshold'])}).",
        f"\\item \\textbf{{XYZ Frequency Class (X-axis)}}: Classifies SKUs based on their contribution to total order frequency (Class X: top {pct0(metadata['abc_a_threshold'])}, Class Y: next {pct0(metadata['abc_b_threshold'] - metadata['abc_a_threshold'])}, Class Z: bottom {pct0(1 - metadata['abc_b_threshold'])}).",
        r"\item \textbf{Cell Labels (Numbers)}: The integer value inside each cell represents the count of unique SKUs that fall into that specific intersection of volume and frequency.",
        r"\end{itemize}",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.75\linewidth]{../charts/q11_abc_xyz_matrix_frequency.png}",
        r"\caption{Q1.1 ABC-XYZ SKU count matrix}",
        r"\label{fig:q11-abc-xyz-matrix}",
        r"\end{figure}",
        r"",

        r"This cross-tabulation reveals four key SKU profiles:",
        r"\begin{itemize}",
        f"\\item \\textbf{{A-X (Fast-Moving)}}: {ax_count} SKUs ({pct(ax_count/total_skus)}) that drive both high volume and high picking frequency, representing the operational core.",
        f"\\item \\textbf{{A-Y / A-Z (Bulk/Spiky Movers)}}: {ay_az_count} SKUs ({pct(ay_az_count/total_skus)}) that move large volumes but are ordered infrequently, indicating bulk orders or promotional campaigns.",
        f"\\item \\textbf{{B-X / C-X (Frequent but Low Volume)}}: {bx_cx_count} SKUs ({pct(bx_cx_count/total_skus)}) that are picked often but contribute little to total volume, creating disproportionate labor pressure relative to their volume contribution.",
        f"\\item \\textbf{{C-Z (Slow and Infrequent)}}: {cz_count} SKUs ({pct(cz_count/total_skus)}) that are prime candidates for deep reserve storage or rationalization.",

        r"",
        r"\subsubsection{Quantity-Volatility ABC-XYZ Analysis}\label{quantity-volatility-abc-xyz-analysis}",
        r"In addition to order frequency, we also evaluated demand variability. Volatility is measured using the Coefficient of Variation (CV) over monthly demand.",
        r"\begin{itemize}",
        r"\item \textbf{Class X (Stable)}: $\text{CV} \le 0.50$",
        r"\item \textbf{Class Y (Seasonal/Trend)}: $0.50 < \text{CV} \le 1.00$",
        r"\item \textbf{Class Z (Erratic)}: $\text{CV} > 1.00$",
        r"\end{itemize}",
        r"",
        r"The joint Quantity-Volatility ABC-XYZ matrix is shown in Figure \ref{fig:q11-abc-xyz-matrix-volatility}:",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.75\linewidth]{../charts/q11_abc_xyz_matrix_volatility.png}",
        r"\caption{Q1.1 ABC-XYZ Volatility SKU count matrix}",
        r"\label{fig:q11-abc-xyz-matrix-volatility}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Identification of the ``Fast-Moving'' SKU Group}\label{identification-of-the-fast-moving-sku-group}",
        r"The \textbf{Fast-Moving} SKU group is defined as the intersection of Class A by Quantity and Class X by Order Frequency (Class A-X). This group is the primary driver of warehouse operational workload and inventory velocity.",
        r"",
        r"\begin{itemize}",
        f"\\item \\textbf{{SKU Count}}: \\textbf{{{fast_mov['sku_count']} SKUs}} (representing \\textbf{{{pct(fast_mov_sku_share)}}} of the total assortment).",
        f"\\item \\textbf{{Volume Contribution}}: Accounts for \\textbf{{{fast_mov['quantity']:.2f} units}} (\\textbf{{{pct(fast_mov['quantity_share'])}}} of total outbound volume).",
        f"\\item \\textbf{{Fulfillment Workload}}: Drives \\textbf{{{fast_mov['order_frequency']} orders}} (\\textbf{{{pct(fast_mov['frequency_share'])}}} of all outbound transaction lines).",
        f"\\item \\textbf{{Top 10 Fast-Moving SKUs}}: \\texttt{{{fast_mov['top_skus']}}}.",
        r"\end{itemize}",
        r"",
        r"\begin{quote}",
        f"\\textbf{{Operational Recommendation}}: Because only \\textasciitilde{pct0(fast_mov_sku_share)} of the SKUs drive \\textasciitilde{pct0(fast_mov['quantity_share'])} of all shipped quantities, these {fast_mov['sku_count']} SKUs should be assigned to the most ergonomic pick-faces (lower levels, close to the packing stations) with dedicated replenishment pathways to minimize picking travel time.",
        r"\end{quote}",
        r"",
        r"\subsection{Q1.2 Distribution Heatmap and Warehouse Imbalance Analysis}\label{q1.2-distribution-heatmap-and-warehouse-imbalance-analysis}",
        r"",
        r"\subsubsection{Data Quality and Resolution Ceiling}\label{data-quality-and-resolution-ceiling}",
        r"",
        r"A critical finding from our data cleansing pipeline is a \textbf{severe geography resolution ceiling}:",
        r"\begin{itemize}",
        f"\\item \\textbf{{Row-level coverage}}: Only \\textbf{{{pct(geo_cov['shipment_row_coverage'])}}} of transaction rows (16,104 out of 43,894) could be mapped to a known customer location.",
        f"\\item \\textbf{{Quantity-level coverage}}: Only \\textbf{{{pct(geo_cov['quantity_coverage'])}}} of outbound quantities (159,635.70 out of 355,364.80) are linked to known coordinates.",
        f"\\item \\textbf{{Root Cause}}: \\texttt{{{geo_cov['shipment_rows_unknown_geography']:,}}} assignment-window rows are unresolved, of which \\textbf{{{geo_cov['rows_unresolved_customer']:,} rows}} are due to \\texttt{{Ship-to Customer}} being logged as \\texttt{{'unknown'}} in the database.",
        r"\end{itemize}",
        r"",
        r"\begin{quote}",
        r"\textbf{Central Invoicing Data Bias}: This missing customer data is systemic:",
        r"\begin{itemize}",
        r"\item \textbf{Centralization (Pre-Dec 2025)}: Customer billing was centralized under My Phuoc's ERP account. Consequently, Vinh Loc shipments (representing Tefal products) were logged as internal stock depletion entries without customer details, affecting \textbf{80.10\%} of Vinh Loc rows.",
        r"\item \textbf{Migration (Dec 2025)}: Billing migrated to Vinh Loc, causing My Phuoc's December transactions to lack customer details.",
        r"\item \textbf{Operational Impact}: Vinh Loc is left with an extremely low geographic coverage of \textbf{12.12\% of its volume}, skewing all raw geographic charts to make Vinh Loc look artificially inactive. This systematic bias and the resulting spatial coverage limits are visualized in Figure \ref{fig:q12-geo-coverage}.",
        r"\end{itemize}",
        r"\end{quote}",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q12_geography_coverage_map.png}",
        r"\caption{Q1.2 Geography coverage map}",
        r"\label{fig:q12-geo-coverage}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Corrected Warehouse Imbalance (Approach A: Statistical Scaling)}\label{corrected-warehouse-imbalance}",
        r"To provide a safe and unbiased view of warehouse throughput, we compare raw volume totals against resolved volumes and apply \textbf{Approach A (Statistical Scaling)}:",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{lcccccc}",
        r"\toprule",
        r"Metric & \multicolumn{2}{c}{My Phuoc Warehouse} & \multicolumn{2}{c}{Vinh Loc Warehouse} & \multicolumn{2}{c}{Total} \\",
        r"\cmidrule(r){2-3} \cmidrule(lr){4-5} \cmidrule(l){6-7}",
        r" & Value & \% & Value & \% & Value & \% \\",
        r"\midrule",
        r"\textbf{Raw Outbound Quantity} & 253,197.00 & 71.25\% & 102,167.80 & 28.75\% & 355,364.80 & 100.00\% \\",
        r"\textbf{Raw Outbound CBM} & 13,948.74 & 70.97\% & 5,705.04 & 29.03\% & 19,653.78 & 100.00\% \\",
        r"\textbf{Raw Transaction Rows} & 17,423 & 39.70\% & 26,471 & 60.30\% & 43,894 & 100.00\% \\",
        r"\textbf{Resolved Quantity (Raw)} & 147,258.80 & 92.25\% & 12,382.80 & 7.75\% & 159,635.70 & 100.00\% \\",
        r"\textbf{Imputed Quantity (Approach A)} & \textbf{253,196.01} & \textbf{71.25\%} & \textbf{102,168.32} & \textbf{28.75\%} & \textbf{355,364.33} & \textbf{100.00\%} \\",
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"\caption{Comparison of Raw, Resolved, and Imputed Throughput}",
        r"\label{tab:q12-wh-throughput}",
        r"\end{table}",
        r"",
        r"\textbf{Conclusion}: While Vinh Loc represents 60.30\% of transaction rows (small, frequent orders of Tefal items), it accounts for 28.75\% of outbound quantity. My Phuoc handles 71.25\% of the quantity. The raw resolved geography is heavily biased (92\% vs 8%), but the true operational split is \textbf{71\% My Phuoc vs 29\% Vinh Loc}. The comparison of raw, resolved, and imputed throughput is detailed in the table above, while the regional warehouse dominance gap in the resolved transactions is shown in Figure \ref{fig:q12-wh-imbalance}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q12_warehouse_imbalance.png}",
        r"\caption{Q1.2 Warehouse imbalance}",
        r"\label{fig:q12-wh-imbalance}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Regional Demand and Top Clusters}\label{regional-demand}",
        r"To define the geographic boundaries of our analysis, the standard Vietnam administrative regions are mapped in Figure \ref{fig:q12-vn-regions}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.45\linewidth]{../charts/q12_region_reference_map.png}",
        r"\caption{Q1.2 Vietnam regioning map}",
        r"\label{fig:q12-vn-regions}",
        r"\end{figure}",
        r"",
        r"Within these boundaries, the resolved outbound demand is highly concentrated. As shown in Figure \ref{fig:q12-region-qty}, the region-level order and quantity shares are led by the following regions:",
        r"\begin{itemize}",
        r"\item \textbf{Đông Nam Bộ}: The largest demand region, accounting for \textbf{42.78\%} of resolved volume (68,289.44 units).",
        r"\item \textbf{Bắc Trung Bộ và Duyên hải miền Trung}: The second largest, representing \textbf{28.22\%} (45,044.48 units).",
        r"\item \textbf{Đồng bằng sông Cửu Long}: Accounts for \textbf{13.86\%} (22,132.83 units).",
        r"\end{itemize}",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q12_region_quantity_orders.png}",
        r"\caption{Q1.2 Regional quantity}",
        r"\label{fig:q12-region-qty}",
        r"\end{figure}",
        r"",
        r"\paragraph{Top Customer Clusters (Provinces)}\label{top-provinces}",
        r"At the provincial level, demand clusters heavily around key urban centers. The absolute volume hotspots are highlighted in the top demand provinces map (see Figure \ref{fig:q12-top-provinces}).",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.45\linewidth]{../charts/q12_top_demand_provinces_map.png}",
        r"\caption{Q1.2 Top demand provinces map}",
        r"\label{fig:q12-top-provinces}",
        r"\end{figure}",
        r"",
        r"Specifically, the top five provinces by resolved volume and order counts are led by Hồ Chí Minh City by an overwhelming margin:",
        r"\begin{itemize}",
        r"\item \textbf{Hồ Chí Minh}: 1,267 orders, 42,256.09 quantity (representing \textbf{34.62\% of resolved orders} and \textbf{26.47\% of resolved quantity}).",
        r"\item \textbf{Đồng Nai}: 387 orders, 5,579.33 quantity.",
        r"\item \textbf{Bình Dương}: 194 orders, 19,814.17 quantity (high volume per order).",
        r"\item \textbf{Đà Nẵng}: 204 orders, 15,522.98 quantity (Central hub).",
        r"\item \textbf{Cần Thơ}: 177 orders, 10,561.08 quantity (Mekong Delta hub).",
        r"\end{itemize}",
        r"",
        r"To visualize the full provincial distribution across the nation, Figure \ref{fig:q12-province-demand} displays the provincial demand choropleth maps (by total quantity and total orders).",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q12_province_demand_choropleths.png}",
        r"\caption{Q1.2 Province demand maps}",
        r"\label{fig:q12-province-demand}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Fulfillment Splits and Spatial Dynamics}\label{fulfillment-splits}",
        r"To understand how fulfillment is shared between the facilities, we examine the warehouse-region throughput split.",
        r"",
        r"\paragraph{Warehouse-Region Fulfillment Splits}\label{wh-region-splits}",
        r"Because My Phuoc holds Fans and Vinh Loc holds Tefal, both warehouses ship to the same regions to fulfill their respective product lines. This regional throughput distribution is visualized in Figure \ref{fig:q12-wh-region-split}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q12_warehouse_region_quantity_split.png}",
        r"\caption{Q1.2 Warehouse-region split}",
        r"\label{fig:q12-wh-region-split}",
        r"\end{figure}",
        r"",
        r"However, due to the centralized billing bias, My Phuoc appears dominant in almost all regions. This dominance pattern and the resulting spatial market coverage of both warehouses are mapped in Figure \ref{fig:q12-wh-dominance}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.45\linewidth]{../charts/q12_warehouse_dominance_map.png}",
        r"\caption{Q1.2 Warehouse dominance map}",
        r"\label{fig:q12-wh-dominance}",
        r"\end{figure}",
        r"",
        r"\paragraph{Distance vs. Demand Size Correlation}\label{distance-correlation}",
        r"We also analyze the relationship between delivery distance and order characteristics. There is a clear spatial correlation between order size (CBM) and delivery distance, showing that close-by urban centers (HCMC and surrounding areas) order in higher density and frequency, as illustrated in the scatter plot in Figure \ref{fig:q12-dist-correlation}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q12_province_distance_correlation.png}",
        r"\caption{Q1.2 Province distance correlation}",
        r"\label{fig:q12-dist-correlation}",
        r"\end{figure}",
        r"",
        r"\subsection{Q1.3 Customer Segment Order Profile Comparison}\label{q1.3-customer-segment-order-profile-comparison}",
        r"We compared the order profiles of \textbf{Modern Trade (MT)} (large retail accounts like Co.op Mart, Lotte, etc.) and \textbf{Traditional Trade / Distributor (TT)}.",
        r"",
        r"\subsubsection{Key Profile Comparison Table}\label{key-profile-comparison-table}",
        r"The comparison across the required dimensions is summarized below:",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{lcc}",
        r"\toprule",
        r"Dimension & Modern Trade (MT) & Traditional Trade / Distributor (TT) \\",
        r"\midrule",
        f"\\textbf{{Active Customers}} & {mt_prof['customers']} & {tt_prof['customers']} \\\\",
        f"\\textbf{{Order Count}} & {mt_prof['orders']} & {tt_prof['orders']} \\\\",
        f"\\textbf{{Avg. Order Quantity}} & {mt_prof['avg_order_quantity']:.2f} pcs & {tt_prof['avg_order_quantity']:.2f} pcs \\\\",
        f"\\textbf{{Avg. Order Volume (m³)}} & {mt_prof['avg_order_cbm']:.2f} m³ & {tt_prof['avg_order_cbm']:.2f} m³ \\\\",
        f"\\textbf{{Avg. SKU Breadth / Order}} & {mt_prof['avg_sku_breadth']:.2f} SKUs & {tt_prof['avg_sku_breadth']:.2f} SKUs \\\\",
        f"\\textbf{{Order Frequency (per customer/month)}} & {mt_prof['avg_orders_per_customer_month']:.2f} & {tt_prof['avg_orders_per_customer_month']:.2f} \\\\",
        f"\\textbf{{Geographic Footprint}} & {mt_prof['province_count']} provinces / {mt_prof['region_count']} regions & {tt_prof['province_count']} provinces / {tt_prof['region_count']} regions \\\\",
        f"\\textbf{{Avg. Delivery Distance}} & {mt_prof['avg_distance_km']:.2f} km & {tt_prof['avg_distance_km']:.2f} km \\\\",
        f"\\textbf{{Pallet Share (\\%)}} & \\textbf{{{mt_pkg_shares.get('pallet', 0.0)*100:.2f}\\%}} & \\textbf{{{tt_pkg_shares.get('pallet', 0.0)*100:.2f}\\%}} \\\\",
        f"\\textbf{{Carton Share (\\%)}} & \\textbf{{{mt_pkg_shares.get('carton', 0.0)*100:.2f}\\%}} & \\textbf{{{tt_pkg_shares.get('carton', 0.0)*100:.2f}\\%}} \\\\",
        f"\\textbf{{Loose Share (\\%)}} & \\textbf{{{mt_pkg_shares.get('loose', 0.0)*100:.2f}\\%}} & \\textbf{{{tt_pkg_shares.get('loose', 0.0)*100:.2f}\\%}} \\\\",
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"\caption{Customer Segment Order Profile Comparison}",
        r"\label{tab:q13-profile-comparison}",
        r"\end{table}",
        r"",
        r"\subsubsection{Key Profile Insights}\label{key-profile-insights}",
        r"\begin{enumerate}",
        f"\\item \\textbf{{Order Size \\& Consolidation}}: Modern Trade orders are highly consolidated and large, averaging \\textbf{{{mt_prof['avg_order_quantity']:.2f} pcs}} and \\textbf{{{mt_prof['avg_order_cbm']:.2f} m³}} per order. Traditional Trade orders are much smaller and fragmented, averaging \\textbf{{{tt_prof['avg_order_quantity']:.2f} pcs}} and \\textbf{{{tt_prof['avg_order_cbm']:.2f} m³}}. This comparison of order metrics is visualised in Figure \\ref{{fig:q13-order-profile}}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.75\linewidth]{../charts/q13_order_profile_comparison.png}",
        r"\caption{Q1.3 Order profile comparison}",
        r"\label{fig:q13-order-profile}",
        r"\end{figure}",
        r"",
        f"\\item \\textbf{{Assortment Breadth vs. Depth}}: As shown in Figure \\ref{{fig:q13-order-profile}}, Traditional Trade orders have a higher average SKU breadth (\\textbf{{{tt_prof['avg_sku_breadth']:.2f} SKUs}} per order) than Modern Trade (\\textbf{{{mt_prof['avg_sku_breadth']:.2f} SKUs}}). This indicates that TT customers order small quantities of a wide variety of SKUs, increasing warehouse sorting complexity.",
        r"",
        f"\\item \\textbf{{Packaging Unit Mix}}: Modern Trade is highly pallet-centric, with \\textbf{{{pct(mt_pkg_shares.get('pallet', 0.0))}}} of their items shipped as full pallets. Traditional Trade is highly carton-centric (\\textbf{{{pct(tt_pkg_shares.get('carton', 0.0))}}} of items) and has more loose picking (\\textbf{{{pct(tt_pkg_shares.get('loose', 0.0))}}} vs. {pct(mt_pkg_shares.get('loose', 0.0))} for MT). This breakdown of packaging unit selections is compared in Figure \\ref{{fig:q13-pkg-mix}}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q13_packaging_mix.png}",
        r"\caption{Q1.3 Packaging mix}",
        r"\label{fig:q13-pkg-mix}",
        r"\end{figure}",
        r"",
        f"\\item \\textbf{{Geographic Spread}}: Traditional Trade has a much wider geographic spread, covering \\textbf{{{tt_prof['province_count']} provinces}} compared to MT's \\textbf{{{mt_prof['province_count']} provinces}}, representing a highly fragmented, nation-wide distribution profile. Traditional Trade's demand is also more concentrated, with its top province accounting for \\textbf{{{pct(tt_prof['top_province_quantity_share'])}}} of its total volume, compared to \\textbf{{{pct(mt_prof['top_province_quantity_share'])}}} for Modern Trade. The province coverage and top-province quantity share for each segment are shown in Figure \\ref{{fig:q13-geo-spread}}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q13_geographic_spread.png}",
        r"\caption{Q1.3 Geographic spread}",
        r"\label{fig:q13-geo-spread}",
        r"\end{figure}",
        r"",
        r"To see the spatial distribution of these sales, Figure \ref{fig:q13-segment-geo-maps} shows the choropleth maps of MT and TT customer demand across Vietnam.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q13_segment_geographic_maps.png}",
        r"\caption{Q1.3 Segment geography maps}",
        r"\label{fig:q13-segment-geo-maps}",
        r"\end{figure}",
        r"\end{enumerate}",
        r"",
        r"\end{document}",
    ]
    
    (NOTES_DIR / NOTE_FILENAME).write_text("\n".join(text) + "\n", encoding="utf-8")
    
    # Run xelatex twice to resolve references and labels
    print("Compiling LaTeX to PDF using xelatex...")
    for _ in range(2):
        subprocess.run(
            ["/Library/TeX/texbin/xelatex", "-interaction=nonstopmode", NOTE_FILENAME],
            cwd=NOTES_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    
    from src.logage2026.config import CLEANED_DIR, TABLES_DIR
    
    print("Loading static cleaned data from disk...")
    try:
        shipments = pd.read_csv(CLEANED_DIR / "shipments_cleaned.csv")
        abc_xyz = pd.read_csv(TABLES_DIR / "q11_sku_abc_xyz.csv")
        abc_xyz_matrix = pd.read_csv(TABLES_DIR / "q11_abc_xyz_matrix_summary.csv")
        fast_moving_summary = pd.read_csv(TABLES_DIR / "q11_fast_moving_summary.csv")
        classification_metadata = pd.read_csv(TABLES_DIR / "q11_classification_metadata.csv")
        missing_data_summary = pd.read_csv(TABLES_DIR / "shared_missing_data_summary.csv")
        geography_coverage_summary = pd.read_csv(TABLES_DIR / "q12_geography_coverage_summary.csv")
        warehouse_region_summary = pd.read_csv(TABLES_DIR / "q12_warehouse_region_summary.csv")
        customer_cluster_summary = pd.read_csv(TABLES_DIR / "q12_customer_cluster_summary.csv")
        warehouse_imbalance_summary = pd.read_csv(TABLES_DIR / "q12_warehouse_imbalance_summary.csv")
        q12_region_orders_quantity_summary = pd.read_csv(TABLES_DIR / "q12_region_quantity_orders_summary.csv")
        q12_province_cluster_summary = pd.read_csv(TABLES_DIR / "q12_top_demand_provinces_summary.csv")
        q12_province_demand_summary = pd.read_csv(TABLES_DIR / "q12_province_demand_summary.csv")
        q12_province_warehouse_dominance_summary = pd.read_csv(TABLES_DIR / "q12_province_warehouse_dominance_summary.csv")
        q12_urban_provincial_summary = pd.read_csv(TABLES_DIR / "q12_urban_provincial_summary.csv")
        q12_warehouse_imbalance_visual_summary = pd.read_csv(TABLES_DIR / "q12_warehouse_imbalance_visual_summary.csv")
        q13_segment_profile_summary = pd.read_csv(TABLES_DIR / "q13_segment_profile_summary.csv")
        q13_segment_packaging_summary = pd.read_csv(TABLES_DIR / "q13_segment_packaging_summary.csv")
        q13_segment_geographic_spread_summary = pd.read_csv(TABLES_DIR / "q13_segment_geographic_spread_summary.csv")
        abc_qty_freq_matrix = pd.read_csv(TABLES_DIR / "q11_abc_quantity_frequency_matrix.csv")
        
        # Convert dates
        shipments["created_date"] = pd.to_datetime(shipments["created_date"])
        
        print("Generating report text from static output...")
        write_notes(
            shipments, abc_xyz, abc_xyz_matrix, fast_moving_summary,
            classification_metadata, missing_data_summary, geography_coverage_summary,
            warehouse_region_summary, customer_cluster_summary, warehouse_imbalance_summary,
            q12_region_orders_quantity_summary, q12_province_cluster_summary,
            q12_province_demand_summary, q12_province_warehouse_dominance_summary,
            q12_urban_provincial_summary,
            q12_warehouse_imbalance_visual_summary,
            q13_segment_profile_summary, q13_segment_packaging_summary,
            q13_segment_geographic_spread_summary
        )
        print(f"Report written successfully to outputs/round2/notes/{NOTE_FILENAME}!")
    except Exception as e:
        print(f"Error loading static output: {e}")
        print("Please run run_analysis.py first to generate the outputs.")
