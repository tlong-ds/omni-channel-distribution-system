import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import subprocess

from src.logage2026.config import NOTES_DIR


NOTE1_FILENAME = "part1_question_summary.tex"
NOTE2_FILENAME = "part2_question_summary.tex"


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
    safety_stock_class_a: pd.DataFrame,
    lead_time_sensitivity: pd.DataFrame,
    inventory_pooling_summary: pd.DataFrame,
    hcm_district_summary: pd.DataFrame,
    network_model_evaluation: pd.DataFrame,
    q21_channel_flow_summary: pd.DataFrame,
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

    # Part 2 Variables
    separated_ss = inventory_pooling_summary.loc[inventory_pooling_summary['scenario'] == 'Separated B2B + B2C', 'total_ss'].iloc[0]
    pooled_ss = inventory_pooling_summary.loc[inventory_pooling_summary['scenario'] == 'Pooled (Shared)', 'total_ss'].iloc[0]
    savings_pct = inventory_pooling_summary.loc[inventory_pooling_summary['scenario'] == 'Pooled (Shared)', 'savings_pct'].iloc[0]
    
    total_hcm_b2b_qty = hcm_district_summary['quantity'].sum()
    top5_qty = hcm_district_summary.head(5)['quantity'].sum()
    top5_pct = top5_qty / total_hcm_b2b_qty if total_hcm_b2b_qty else 0
    
    # Q2.1 Variables
    adequate_districts = network_model_evaluation[network_model_evaluation["sla_status"] == "Adequate"]
    needs_ds_districts = network_model_evaluation[network_model_evaluation["sla_status"] == "Needs Dark Store"]
    adequate_qty = adequate_districts["quantity"].sum()
    needs_ds_qty = needs_ds_districts["quantity"].sum()
    total_hcm_qty_nme = network_model_evaluation["quantity"].sum()
    adequate_pct = adequate_qty / total_hcm_qty_nme if total_hcm_qty_nme else 0
    needs_ds_pct = needs_ds_qty / total_hcm_qty_nme if total_hcm_qty_nme else 0
    n_adequate = len(adequate_districts)
    n_needs_ds = len(needs_ds_districts)

    # Q2.1 Channel flow variables (from build_q21_channel_flow_summary / Book5)
    def _cf(wh, ch, col):
        """Safe lookup for channel-flow KPI."""
        sub = q21_channel_flow_summary[
            (q21_channel_flow_summary["warehouse"] == wh)
            & (q21_channel_flow_summary["channel"] == ch)
        ]
        return sub.iloc[0][col] if not sub.empty else 0

    mp_b2b_orders = _cf("My Phuoc", "B2B", "orders")
    mp_b2c_orders = _cf("My Phuoc", "B2C", "orders")
    vl_b2b_orders = _cf("Vinh Loc", "B2B", "orders")
    vl_b2c_orders = _cf("Vinh Loc", "B2C", "orders")

    mp_b2b_cbm = _cf("My Phuoc", "B2B", "total_cbm")
    mp_b2c_cbm = _cf("My Phuoc", "B2C", "total_cbm")
    vl_b2b_cbm = _cf("Vinh Loc", "B2B", "total_cbm")
    vl_b2c_cbm = _cf("Vinh Loc", "B2C", "total_cbm")

    mp_b2b_vol_idx = _cf("My Phuoc", "B2B", "volatility_index")
    mp_b2c_vol_idx = _cf("My Phuoc", "B2C", "volatility_index")
    vl_b2b_vol_idx = _cf("Vinh Loc", "B2B", "volatility_index")
    vl_b2c_vol_idx = _cf("Vinh Loc", "B2C", "volatility_index")

    mp_b2b_flow = _cf("My Phuoc", "B2B", "flow_type")
    mp_b2c_flow = _cf("My Phuoc", "B2C", "flow_type")
    vl_b2b_flow = _cf("Vinh Loc", "B2B", "flow_type")
    vl_b2c_flow = _cf("Vinh Loc", "B2C", "flow_type")

    mp_total_orders = mp_b2b_orders + mp_b2c_orders
    vl_total_orders = vl_b2b_orders + vl_b2c_orders

    mp_b2b_cbm_share = mp_b2b_cbm / (mp_b2b_cbm + mp_b2c_cbm) if (mp_b2b_cbm + mp_b2c_cbm) else 0
    vl_b2b_cbm_share = vl_b2b_cbm / (vl_b2b_cbm + vl_b2c_cbm) if (vl_b2b_cbm + vl_b2c_cbm) else 0

    # Timeline metadata
    mp_period_note = _cf("My Phuoc", "B2B", "period_note") if "period_note" in q21_channel_flow_summary.columns else "Jun to Nov 2025 (6 months)"
    vl_period_note = _cf("Vinh Loc", "B2B", "period_note") if "period_note" in q21_channel_flow_summary.columns else "Dec 2025 only (1 month)"
    mp_operating_months = _cf("My Phuoc", "B2B", "operating_months") if "operating_months" in q21_channel_flow_summary.columns else 6.0
    vl_operating_months = _cf("Vinh Loc", "B2B", "operating_months") if "operating_months" in q21_channel_flow_summary.columns else 1.0
    mp_avg_orders_per_day = _cf("My Phuoc", "B2B", "avg_orders_per_day")
    vl_avg_orders_per_day = _cf("Vinh Loc", "B2B", "avg_orders_per_day")

    # Pre-computed strings for f-string safety
    mp_b2b_cbm_share_str = f"{mp_b2b_cbm_share * 100:.1f}\\%"
    vl_b2b_cbm_share_str = f"{vl_b2b_cbm_share * 100:.1f}\\%"
    mp_b2b_vol_idx_str = f"{mp_b2b_vol_idx:.2f}"
    mp_b2c_vol_idx_str = f"{mp_b2c_vol_idx:.2f}"
    vl_b2b_vol_idx_str = f"{vl_b2b_vol_idx:.2f}"
    vl_b2c_vol_idx_str = f"{vl_b2c_vol_idx:.2f}"
    mp_avg_orders_day_str = f"{mp_avg_orders_per_day:.1f}"
    vl_avg_orders_day_str = f"{vl_avg_orders_per_day:.1f}"
    
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

    # Dynamic recalculation for Q1.2 Warehouse Imbalance
    mp_raw = shipments[shipments['source_warehouse'] == 'My Phuoc']
    vl_raw = shipments[shipments['source_warehouse'] == 'Vinh Loc']
    
    mp_raw_qty = mp_raw['quantity'].sum()
    vl_raw_qty = vl_raw['quantity'].sum()
    tot_raw_qty = shipments['quantity'].sum()
    
    mp_raw_cbm = mp_raw['cbm_total'].sum()
    vl_raw_cbm = vl_raw['cbm_total'].sum()
    tot_raw_cbm = shipments['cbm_total'].sum()
    
    mp_raw_rows = len(mp_raw)
    vl_raw_rows = len(vl_raw)
    tot_raw_rows = len(shipments)
    
    resolved = shipments[shipments['known_geography_flag'] == True]
    mp_res_qty = resolved[resolved['source_warehouse'] == 'My Phuoc']['quantity'].sum()
    vl_res_qty = resolved[resolved['source_warehouse'] == 'Vinh Loc']['quantity'].sum()
    tot_res_qty = resolved['quantity'].sum()
    
    vl_missing_rows = vl_raw_rows - len(resolved[resolved['source_warehouse'] == 'Vinh Loc'])
    vl_missing_rows_pct = (vl_missing_rows / vl_raw_rows) if vl_raw_rows else 0
    vl_volume_coverage_pct = (vl_res_qty / vl_raw_qty) if vl_raw_qty else 0
    
    mp_qty_pct = mp_raw_qty / tot_raw_qty if tot_raw_qty else 0
    vl_qty_pct = vl_raw_qty / tot_raw_qty if tot_raw_qty else 0
    
    mp_cbm_pct = mp_raw_cbm / tot_raw_cbm if tot_raw_cbm else 0
    vl_cbm_pct = vl_raw_cbm / tot_raw_cbm if tot_raw_cbm else 0
    
    mp_row_pct = mp_raw_rows / tot_raw_rows if tot_raw_rows else 0
    vl_row_pct = vl_raw_rows / tot_raw_rows if tot_raw_rows else 0
    
    mp_res_pct = mp_res_qty / tot_res_qty if tot_res_qty else 0
    vl_res_pct = vl_res_qty / tot_res_qty if tot_res_qty else 0

    top_regions = q12_region_orders_quantity_summary.sort_values("quantity", ascending=False).head(3)
    tot_region_qty = q12_region_orders_quantity_summary["quantity"].sum()
    region_items = []
    for _, r in top_regions.iterrows():
        qty_share = r['quantity'] / tot_region_qty if tot_region_qty else 0
        region_items.append(rf"\item \textbf{{{r['region']}}}: Accounts for \textbf{{{pct(qty_share)}}} of resolved volume ({r['quantity']:,.2f} units).")
    region_list_tex = "\n".join(region_items)

    top_provs = q12_province_cluster_summary.sort_values("quantity", ascending=False).head(5)
    tot_prov_qty = q12_province_cluster_summary["quantity"].sum()
    tot_prov_orders = q12_province_cluster_summary["orders"].sum()
    prov_items = []
    for _, p in top_provs.iterrows():
        qty_share = p['quantity'] / tot_prov_qty if tot_prov_qty else 0
        ord_share = p['orders'] / tot_prov_orders if tot_prov_orders else 0
        prov_items.append(rf"\item \textbf{{{p['province']}}}: {int(p['orders']):,} orders, {p['quantity']:,.2f} quantity (representing \textbf{{{pct(ord_share)}}} of resolved orders and \textbf{{{pct(qty_share)}}} of resolved quantity).")
    prov_list_tex = "\n".join(prov_items)

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
        f"\\item \\textbf{{ERP Centralized Invoicing Distortion}}: Geographic demand analyses reveal that My Phuoc seemingly dominates {pct(mp_res_pct)} of resolved volume. However, this is an artificial bias caused by centralized ERP invoicing. In reality, Vinh Loc's raw outbound shipments account for {pct(vl_qty_pct)} of total volume, but {pct(vl_missing_rows_pct)} of its transactions are unresolved and excluded from standard maps. Using \\textbf{{Approach A (Statistical Scaling)}}, we restore and analyze the true {pct(mp_qty_pct)} My Phuoc vs {pct(vl_qty_pct)} Vinh Loc volume split.",
        f"\\item \\textbf{{Clear Segment Profiles}}: Modern Trade orders are large, consolidated, and heavily palletized ({pct(mt_pkg_shares.get('pallet', 0.0))} of quantity). Traditional Trade orders are smaller, highly fragmented ({pct(tt_pkg_shares.get('carton', 0.0))} carton / {pct(tt_pkg_shares.get('loose', 0.0))} loose), and spread across {tt_prof['province_count']} provinces, presenting different operational picking requirements.",
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
        r"A finding from our data cleansing pipeline is a \textbf{minor geography resolution limit}:",
        r"\begin{itemize}",
        f"\\item \\textbf{{Row-level coverage}}: \\textbf{{{pct(geo_cov['shipment_row_coverage'])}}} of transaction rows ({geo_cov['shipment_rows_known_geography']:,} out of {geo_cov['shipment_rows_total']:,}) could be mapped to a known customer location.",
        f"\\item \\textbf{{Quantity-level coverage}}: \\textbf{{{pct(geo_cov['quantity_coverage'])}}} of outbound quantities ({geo_cov['quantity_known_geography']:,.2f} out of {geo_cov['quantity_total']:,.2f}) are linked to known coordinates.",
        f"\\item \\textbf{{Root Cause}}: \\texttt{{{geo_cov['shipment_rows_unknown_geography']:,}}} assignment-window rows are unresolved, of which \\textbf{{{geo_cov['rows_unresolved_customer']:,} rows}} are due to \\texttt{{Ship-to Customer}} being logged as \\texttt{{'unknown'}} in the database.",
        r"\end{itemize}",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q12_geography_coverage_map.png}",
        r"\caption{Q1.2 Geography coverage map}",
        r"\label{fig:q12-geo-coverage}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Warehouse Imbalance}\label{warehouse-imbalance}",
        r"To provide a clear view of warehouse throughput, we compare raw volume totals against the geographically resolved volumes:",
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
        f"\\textbf{{Raw Outbound Quantity}} & {mp_raw_qty:,.2f} & {pct(mp_qty_pct)} & {vl_raw_qty:,.2f} & {pct(vl_qty_pct)} & {tot_raw_qty:,.2f} & 100.00\\% \\\\",
        f"\\textbf{{Raw Outbound CBM}} & {mp_raw_cbm:,.2f} & {pct(mp_cbm_pct)} & {vl_raw_cbm:,.2f} & {pct(vl_cbm_pct)} & {tot_raw_cbm:,.2f} & 100.00\\% \\\\",
        f"\\textbf{{Raw Transaction Rows}} & {mp_raw_rows:,} & {pct(mp_row_pct)} & {vl_raw_rows:,} & {pct(vl_row_pct)} & {tot_raw_rows:,} & 100.00\\% \\\\",
        f"\\textbf{{Resolved Quantity}} & {mp_res_qty:,.2f} & {pct(mp_res_pct)} & {vl_res_qty:,.2f} & {pct(vl_res_pct)} & {tot_res_qty:,.2f} & 100.00\\% \\\\",
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"\caption{Comparison of Raw and Resolved Throughput}",
        r"\label{tab:q12-wh-throughput}",
        r"\end{table}",
        r"",
        f"\\textbf{{Conclusion}}: While Vinh Loc represents {pct(vl_row_pct)} of transaction rows, it accounts for {pct(vl_qty_pct)} of outbound quantity. My Phuoc handles {pct(mp_qty_pct)} of the quantity. The geographic resolution coverage is very high, so the resolved regional distribution perfectly aligns with the true operational split of \\textbf{{{pct0(mp_qty_pct)} My Phuoc vs {pct0(vl_qty_pct)} Vinh Loc}}. The comparison of raw and resolved throughput is detailed in the table above, while the regional warehouse dominance is shown in Figure \\ref{{fig:q12-wh-imbalance}}.",
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
        region_list_tex,
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
        prov_list_tex,
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
        r"My Phuoc handles significantly more volume than Vinh Loc and appears dominant in almost all regions. This dominance pattern and the resulting spatial market coverage of both warehouses are mapped in Figure \ref{fig:q12-wh-dominance}.",
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
    
    text2 = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{graphicx}",
        r"\usepackage{float}",
        r"\usepackage{xcolor}",
        r"\usepackage{booktabs}",
        r"\usepackage{caption}",
        r"\usepackage{makecell}",
        r"\usepackage{enumitem}",
        r"\usepackage{hyperref}",
        r"",
        r"\title{\textbf{LOGage 2026: Round 2 — Part 2 Summary}}",
        r"\author{Omni-Channel Strategy Analysis}",
        r"\date{\today}",
        r"",
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\newpage",
        r"",
        r"\section{PART 2: OMNI-CHANNEL FULFILLMENT STRATEGY DESIGN}",
        r"",
        # ── Q2.1 ────────────────────────────────────────────────
        r"\subsection{Question 2.1: Network Model Evaluation \& Design}",
        r"",
        r"\subsubsection{Current Two-RDC Model Assessment}",
        r"",
        r"The brand currently operates two Regional Distribution Centers (RDCs):",
        r"\begin{itemize}",
        r"  \item \textbf{My Phuoc Warehouse} — Industrial Zone, Binh Duong Province",
        r"  \item \textbf{Vinh Loc Warehouse} — Binh Chanh District, Ho Chi Minh City",
        r"\end{itemize}",
        r"",
        r"\textbf{Strengths of the current model:}",
        r"\begin{itemize}",
        r"  \item Good regional separation: My Phuoc serves northern (B2B factory-sourced) flows; Vinh Loc is positioned for inner-city B2C proximity.",
        r"  \item Both RDCs handle mixed-channel flows, demonstrating operational flexibility.",
        r"  \item Physical locations bracket the Eastern\textendash{}Western commercial corridor of HCMC, covering most \DJ{}\^ong Nam B\^o volume.",
        r"\end{itemize}",
        r"",
        r"\textbf{Important context: Non-overlapping operating timelines}",
        r"\begin{itemize}",
        f"  \\item \\textbf{{My Phuoc}} ({mp_period_note}): The \\textit{{primary}} warehouse, operational across the full 6-month analysis window. All June--November 2025 throughput flowed through My Phuoc.",
        f"  \\item \\textbf{{Vinh Loc}} ({vl_period_note}): A \\textit{{new}} warehouse that came online in December 2025 only. Raw volume totals are therefore \\textbf{{not directly comparable}} between the two facilities.",
        r"\end{itemize}",
        r"",
        r"\textbf{Data-driven channel flow analysis} (per-day rates, Figure \ref{fig:q21-channel-flow}):",
        r"\begin{itemize}",
        f"  \\item \\textbf{{My Phuoc}} ({int(mp_b2b_orders):,} B2B + {int(mp_b2c_orders):,} B2C orders over 6 months): B2B is a \\textit{{{mp_b2b_flow}}} accounting for \\textbf{{{mp_b2b_cbm_share_str}}} of CBM. B2B avg \\textbf{{{mp_avg_orders_day_str} orders/active day}}, volatility index \\textbf{{B2B = {mp_b2b_vol_idx_str}}}.",
        f"  \\item \\textbf{{Vinh Loc}} ({int(vl_b2b_orders):,} B2B + {int(vl_b2c_orders):,} B2C orders in 1 month): B2B is a \\textit{{{vl_b2b_flow}}} accounting for \\textbf{{{vl_b2b_cbm_share_str}}} of CBM. B2B avg \\textbf{{{vl_avg_orders_day_str} orders/active day}}, volatility index \\textbf{{B2B = {vl_b2b_vol_idx_str}}}.",
        r"  \item On a per-day basis, Vinh Loc processed B2B orders at a comparable daily rate to My Phuoc despite being open for only one month, indicating strong December surge demand (year-end push).",
        r"\end{itemize}",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=\linewidth]{../charts/q21_channel_flow_profile.png}",
        r"\caption{Q2.1 Warehouse $\times$ Channel Flow Profile (per-day rates normalized to each RDC operating window)}",
        r"\label{fig:q21-channel-flow}",
        r"\end{figure}",
        r"",
        r"\textbf{Limitations for simultaneous B2B + B2C:}",
        r"\begin{itemize}",
        r"  \item Lead times from both RDCs are too long for the 2\textendash{}4 hour B2C SLA required for e-commerce \textendash{} even Vinh Loc is \textgreater{}10 km from central districts.",
        r"  \item Shared inventory creates channel conflict: B2B bulk orders may deplete stock that B2C needs for same-day fulfillment.",
        r"  \item Pick-and-pack processes for large pallet B2B orders disrupt small-unit B2C wave picking.",
        r"\end{itemize}",
        r"",
        r"\subsubsection{B2C E-Commerce SLA Assessment}",
        r"",
        r"To meet a 2--4 hour delivery SLA across Ho Chi Minh City, we applied a 25 km distance threshold from the nearest RDC as the feasibility cut-off (assuming average urban speed of $\sim$25 km/h, 25 km $\approx$ 60 min travel, leaving buffer for pick/pack and handoff).",
        r"",
        f"The analysis of \\textbf{{{len(network_model_evaluation)} HCM districts}} reveals a clear split:",
        r"\begin{itemize}",
        f"  \\item \\textbf{{\\color{{green!60!black}}{n_adequate} districts — Adequate:}} These districts can be served within the 2h SLA from the existing RDCs and account for \\textbf{{{adequate_pct * 100:.1f}\\%}} of total HCM B2B volume (\\textbf{{{adequate_qty:,.0f} units}}).",
        f"  \\item \\textbf{{\\color{{red}}{n_needs_ds} districts — Require Dark Stores:}} These are \\textgreater{{}}25 km from both RDCs, placing them outside reliable SLA reach. They represent \\textbf{{{needs_ds_pct * 100:.1f}\\%}} of volume (\\textbf{{{needs_ds_qty:,.0f} units}}).",
        r"\end{itemize}",
        r"",
        r"Figure \ref{fig:q21-network-coverage} shows the district-level breakdown.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=\linewidth]{../charts/q21_network_coverage.png}",
        r"\caption{Q2.1 HCM District Proximity to Existing RDCs vs B2B Demand Volume}",
        r"\label{fig:q21-network-coverage}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Dark Store Node Recommendation}",
        r"",
        r"Based on the demand concentration and distance analysis, we recommend placing \textbf{1--2 urban micro-fulfillment (dark store) nodes} in HCMC:",
        r"\begin{enumerate}",
        r"  \item \textbf{Primary node — Bình Tân / Tân Phú corridor}: These two adjacent districts are among the highest-volume B2B districts (combined \textgreater{}50,000 units) and are already well-served by Vinh Loc (5--7 km). Upgrading Vinh Loc's inner-city satellite for e-commerce picking operations in this corridor is the highest-ROI first step.",
        r"  \item \textbf{Secondary node — District 1 / District 3 / Phú Nhuận cluster}: The CBD and premium residential cluster lies 14+ km from Vinh Loc, making 2h SLA difficult. A small dark store (200--300 m²) in this zone, stocked with the top Class A SKUs, would close the gap.",
        r"\end{enumerate}",
        r"",
        r"\subsubsection{Order Split Logic Design (HCM)}",
        r"",
        r"For urban B2B order fulfillment in Ho Chi Minh City, network design relies on understanding sub-regional demand density. We analyzed the historical B2B shipments across all HCM districts.",
        r"",
        f"The demand is highly concentrated: the top 5 districts alone command \\textbf{{{top5_qty:,.0f} units}} — \\textbf{{{top5_pct * 100:.1f}\\%}} of all HCM B2B volume — as shown in Figure \\ref{{fig:q21-hcm-district-volume}}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q21_hcm_district_volume.png}",
        r"\caption{Q2.1 Top Ho Chi Minh Districts by B2B Quantity}",
        r"\label{fig:q21-hcm-district-volume}",
        r"\end{figure}",
        r"",
        r"\textbf{Recommended order split logic:} Given this concentration, the dispatch decision tree should be:",
        r"\begin{enumerate}",
        r"  \item If delivery district is within 25 km of Vinh Loc $\rightarrow$ dispatch from \textbf{Vinh Loc} (B2C-optimized lane).",
        r"  \item If delivery district is within 35 km of My Phuoc but $>$25 km from Vinh Loc $\rightarrow$ dispatch from \textbf{My Phuoc} (B2B bulk lane).",
        r"  \item If district is $>$25 km from both RDCs $\rightarrow$ \textbf{route via dark store} (pending network expansion).",
        r"\end{enumerate}",
        r"",
        # ── Q2.2 ────────────────────────────────────────────────
        r"\subsection{Question 2.2: Inventory Optimization}",
        r"",
        r"\subsubsection{Lead Time Assumptions \& Validation}",
        r"",
        r"\textbf{Definition:} Replenishment Lead Time is the duration from when the warehouse identifies a replenishment need until the goods are ready to pick again. This is distinct from the customer-facing delivery SLA.",
        r"",
        r"\textbf{Data limitation:} The dataset only contains \texttt{created\_date} (outbound dispatch date). There is no PO creation date or Goods Receipt date, so lead time cannot be measured directly. The values below are \textit{justified assumptions} cross-validated against inter-shipment intervals in the transaction log.",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Lead Time Component Breakdown by Channel}",
        r"\begin{tabular}{lccl}",
        r"\toprule",
        r"\textbf{Component} & \textbf{B2B (Factory→RDC)} & \textbf{B2C (RDC→Dark Store)} & \textbf{Rationale} \\",
        r"\midrule",
        r"T\_review (stock check) & 1.0 day & 0.5 day & B2B daily review; B2C twice-daily auto-trigger \\",
        r"T\_PO (create \& approve PO) & 0.5 day & 0 day & B2C uses auto-replenishment, no manual PO \\",
        r"T\_supplier (preparation) & 1.5 days & 0 day & Factory batch lead time; B2C pulls from RDC stock \\",
        r"T\_transport & 1.0 day & 0.5 day & Intra-ĐNB region; B2C last-mile $<$15 km same-day \\",
        r"T\_receiving (QC check-in) & 0.5 day & 0.5 day & Physical count \& inspection \\",
        r"T\_putaway (shelf-ready) & 0.5 day & 0.5 day & Ready to pick \\",
        r"\midrule",
        r"\textbf{Total Lead Time} & \textbf{5 days} & \textbf{2 days} & \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        r"\textbf{Empirical cross-validation from data:}",
        r"\begin{itemize}",
        r"  \item Median inter-shipment gap for Class A SKUs = \textbf{2.0 days} $\rightarrow$ matches LT\textsubscript{B2C} = 2 days",
        r"  \item Mean inter-shipment gap = \textbf{7.7 days} (long tail from bulk lot orders) $\rightarrow$ consistent with LT\textsubscript{B2B} $\approx$ 5 days",
        r"  \item \textit{Conclusion: Assumptions are well-calibrated to observable shipment rhythms.}",
        r"\end{itemize}",
        r"",
        r"\subsubsection{Safety Stock Formula \& Results}",
        r"",
        r"Safety stock for each Class A SKU is calculated using the full lead-time uncertainty formula:",
        r"\[",
        r"SS = Z \cdot \sqrt{LT \cdot \sigma_d^2 + \mu_d^2 \cdot \sigma_{LT}^2}",
        r"\]",
        r"where $Z = 1.645$ (95\% service level), $\mu_d$ = mean daily demand, $\sigma_d$ = std of daily demand, $LT$ = mean lead time, and $\sigma_{LT}$ = lead time std dev (B2B: 1.0 day, B2C: 0.5 day).",
        r"",
        r"\textbf{Key result:} This section details the required safety stock for Class A SKUs to support omni-channel fulfillment under different lead time configurations.",
        r"",
        f"Under the \\textbf{{separated channel}} setup (B2B: 5-day LT, B2C: 2-day LT), the total required safety stock for Class A SKUs is \\textbf{{{separated_ss:,.0f} units}}.",
        r"",
        r"We then evaluated the impact of varying the replenishment lead time on total safety stock requirements. As illustrated in Figure \ref{fig:q22-lead-time-sensitivity}, safety stock exhibits a sub-linear (square root) growth relative to lead time.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q22_lead_time_sensitivity.png}",
        r"\caption{Q2.2 Lead Time Sensitivity for Class A Safety Stock}",
        r"\label{fig:q22-lead-time-sensitivity}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Inventory Pooling Strategy}",
        r"",
        r"\textbf{Principle — Why pooling reduces safety stock:}",
        r"\begin{itemize}",
        r"  \item Separated: $SS = Z\sigma(\sqrt{LT_{B2B}} + \sqrt{LT_{B2C}}) = Z\sigma(\sqrt{5}+\sqrt{2}) = Z\sigma \times 3.650$",
        r"  \item Pooled: $SS = Z\sigma\sqrt{\frac{LT_{B2B}+LT_{B2C}}{2}} = Z\sigma\sqrt{3.5} = Z\sigma \times 1.871$",
        r"  \item \textbf{Reduction factor} = $\frac{\sqrt{3.5}}{\sqrt{5}+\sqrt{2}} = 0.5125$ $\rightarrow$ pooling reduces safety stock by $\approx$48.7\%",
        r"\end{itemize}",
        r"",
        f"By centralizing inventory into a shared pool with an effective average lead time of 3.5 days, the required safety stock drops from \\textbf{{{separated_ss:,.0f}}} to \\textbf{{{pooled_ss:,.0f} units}}, saving \\textbf{{{savings_pct * 100:.1f}\\%}} as shown in Figure \\ref{{fig:q22-inventory-pooling}}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.75\linewidth]{../charts/q22_inventory_pooling.png}",
        r"\caption{Q2.2 Inventory Pooling Impact on Safety Stock}",
        r"\label{fig:q22-inventory-pooling}",
        r"\end{figure}",
        r"",
        r"\textbf{Dynamic Allocation Rules (to prevent simultaneous stockout):}",
        r"\begin{enumerate}",
        r"  \item \textbf{R1 — Common Pool:} Merge B2B and B2C inventory per SKU into a single real-time pool tracked in WMS.",
        r"  \item \textbf{R2 — Reserved Floor per channel:} Each channel maintains a floor reserve = its own ROP. Neither channel can dip below the other's floor.",
        r"  \item \textbf{R3 — Amber Alert:} When total pool $<$ (SS\textsubscript{B2B} + SS\textsubscript{B2C}): system raises alert and prioritizes confirmed B2B purchase orders (contractual commitments).",
        r"  \item \textbf{R4 — Red Conflict:} If same SKU is simultaneously short for both channels: B2B receives its full contracted PO quantity (penalty risk); B2C receives remainder + escalated to next pick wave + customer notified.",
        r"  \item \textbf{R5 — AZ Spike Freeze:} For AZ-class SKUs showing demand spikes: temporarily freeze B2C allocations, concentrate stock for B2B, trigger emergency replenishment.",
        r"  \item \textbf{R6 — End-of-Day Rebalance:} Rebalance channel inventory ratios to target ROP proportions based on rolling 7-day demand forecast.",
        r"\end{enumerate}",
        r"",
        r"\end{document}",
    ]
    
    (NOTES_DIR / NOTE1_FILENAME).write_text("\n".join(text) + "\n", encoding="utf-8")
    (NOTES_DIR / NOTE2_FILENAME).write_text("\n".join(text2) + "\n", encoding="utf-8")
    
    # Run xelatex twice to resolve references and labels
    print("Compiling LaTeX to PDF using xelatex...")
    for filename in [NOTE1_FILENAME, NOTE2_FILENAME]:
        for _ in range(2):
            subprocess.run(
                ["/Library/TeX/texbin/xelatex", "-interaction=nonstopmode", filename],
                cwd=NOTES_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


NOTE3_FILENAME = "part3_question_summary.tex"


def write_part3_notes(abc_xyz: pd.DataFrame) -> None:
    """Generate the Part 3 LaTeX report (Q3.1 Slotting + Q3.2 Pick-Pack) and compile to PDF."""
    from src.logage2026.analysis import build_slotting_plan, compute_travel_time_metrics

    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    slotting = build_slotting_plan(abc_xyz)
    metrics = compute_travel_time_metrics(abc_xyz)

    N = metrics["N"]
    Na, Nb, Nc = metrics["zone_counts"]["A"], metrics["zone_counts"]["B"], metrics["zone_counts"]["C"]
    Pa, Pb, Pc = metrics["zone_probs"]["A"], metrics["zone_probs"]["B"], metrics["zone_probs"]["C"]
    e_rnd = metrics["random_baseline"]
    e_qty = metrics["zoned_qty"]
    e_freq = metrics["zoned_freq"]
    e_opt = metrics["continuous_optimal"]
    red_qty = metrics["reduction_qty"] * 100
    red_freq = metrics["reduction_freq"] * 100
    red_opt = metrics["reduction_optimal"] * 100

    # AX fast-movers
    ax_skus = abc_xyz[(abc_xyz["abc_quantity"] == "A") & (abc_xyz["xyz_frequency"] == "X")]
    ax_count = len(ax_skus)
    ax_freq_share = ax_skus["order_frequency"].sum() / abc_xyz["order_frequency"].sum() * 100
    ax_qty_share = ax_skus["quantity"].sum() / abc_xyz["quantity"].sum() * 100

    # Top 5 Class A by frequency for the table
    top_a = (
        abc_xyz[abc_xyz["abc_quantity"] == "A"]
        .sort_values("order_frequency", ascending=False)
        .head(5)[["sku_code", "product_name", "abc_quantity", "xyz_frequency", "order_frequency", "quantity"]]
        .reset_index(drop=True)
    )

    def pct(v: float) -> str:
        return f"{v * 100:.2f}\\%"

    # Build LaTeX rows for top-5 table
    top5_rows = []
    for rank, (_, row) in enumerate(top_a.iterrows(), 1):
        name = str(row["product_name"])[:40].replace("&", "\\&").replace("_", "\\_")
        top5_rows.append(
            f"        {rank} & {row['sku_code']} & {name} & A-{row['xyz_frequency']} "
            f"& {int(row['order_frequency']):,} & {int(row['quantity']):,} \\\\"
        )
    top5_tex = "\n".join(top5_rows)

    # Zone summary table rows
    zone_rows = [
        f"        Pick-Face Zone & A & {Na} & {Pa * 100:.1f}\\% & {pct(abc_xyz[abc_xyz['abc_quantity'] == 'A']['quantity'].sum() / abc_xyz['quantity'].sum())} \\\\",
        f"        Forward Reserve Zone & B & {Nb} & {Pb * 100:.1f}\\% & {pct(abc_xyz[abc_xyz['abc_quantity'] == 'B']['quantity'].sum() / abc_xyz['quantity'].sum())} \\\\",
        f"        Reserve / Bulk Zone & C & {Nc} & {Pc * 100:.1f}\\% & {pct(abc_xyz[abc_xyz['abc_quantity'] == 'C']['quantity'].sum() / abc_xyz['quantity'].sum())} \\\\",
    ]
    zone_tex = "\n".join(zone_rows)

    tex = [
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
        r"\section{Part 3: Warehouse Operations Solutions}\label{part3}",
        r"",
        r"\subsection{Question 3.1: Slotting Optimization}\label{q3.1}",
        r"",
        r"Using the ABC-XYZ classification from Part 1 and the physical SKU attributes from the",
        f"Master Data, we assigned all {N} classified SKUs to three warehouse zones following the",
        r"VILAS SNP (Supply \& Network Planning) slotting framework.",
        r"",
        r"\subsubsection{Zone Assignment Framework}\label{zone-framework}",
        r"",
        r"\begin{itemize}",
        r"    \item \textbf{Pick-Face Zone (Ground Level)} — Class A SKUs: lowest racks at ergonomic",
        r"          height (waist-to-shoulder), positioned nearest to the I/O dock and packing station.",
        r"          Pickers retrieve these items manually without MHE vertical travel.",
        r"    \item \textbf{Forward Reserve Zone} — Class B SKUs: intermediate racking with a",
        r"          two-bin replenishment logic. A forward pick-face bin is replenished from the",
        r"          bulk reserve when stock hits its reorder point (WMS-triggered).",
        r"    \item \textbf{Reserve / Bulk Zone} — Class C SKUs: upper racks and pallet-in /",
        r"          pallet-out storage. Slow-movers occupy the highest slots farthest from the dock.",
        r"\end{itemize}",
        r"",
        r"\subsubsection{Zone Distribution}\label{zone-distribution}",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Slotting Zone Summary — All SKUs}",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"Zone & Class & SKU Count & \% of Picks & \% of Volume \\",
        r"\midrule",
        zone_tex,
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        f"The Pick-Face Zone contains only {Na} SKUs ({Na / N * 100:.1f}\\% of the assortment) yet",
        f"they account for \\textbf{{{Pa * 100:.1f}\\%}} of all pick transactions and",
        f"\\textbf{{{abc_xyz[abc_xyz['abc_quantity'] == 'A']['quantity'].sum() / abc_xyz['quantity'].sum() * 100:.1f}\\%}} of total outbound volume.",
        f"Within this zone, the \\textbf{{{ax_count} Class A-X fast-movers}} (highest velocity",
        r"\emph{and} highest consistency) occupy rank slots 1--" + str(ax_count) + r", directly adjacent to the packing",
        r"station, and collectively drive \textbf{" + f"{ax_freq_share:.2f}\\%" + r"} of pick frequency",
        r"and \textbf{" + f"{ax_qty_share:.2f}\\%" + r"} of total outbound volume.",
        r"",
        r"\subsubsection{Top Pick-Face SKUs (Class A, by Frequency)}\label{top-a}",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Top 5 Class-A SKUs assigned to Pick-Face Zone}",
        r"\begin{tabular}{clllrr}",
        r"\toprule",
        r"Rank & SKU Code & Product & Class & Picks (6M) & Volume (units) \\",
        r"\midrule",
        top5_tex,
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        r"\subsubsection{Quantitative Travel Time Analysis}\label{travel-time}",
        r"",
        r"\paragraph{Model Assumption.}",
        r"The warehouse has $N$ numbered rack slots $1, 2, \ldots, N$ starting from the I/O dock.",
        r"The travel cost of a single pick equals the slot number of the target SKU.",
        r"Expected travel distance is therefore:",
        r"$$E[\text{travel}] = \sum_{i=1}^{N} p_i \cdot s_i$$",
        r"where $p_i$ is the pick probability of SKU $i$ (its order frequency share) and $s_i$ is",
        r"its assigned slot number.",
        r"",
        r"\paragraph{Results.}",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Expected Picker Travel Distance by Slotting Scenario}",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"Scenario & Expected Distance (slot units) & Reduction vs Baseline \\",
        r"\midrule",
        f"        Random Baseline (no logic) & {e_rnd:.2f} & — \\\\",
        f"        ABC Zoned (Quantity-Based) & {e_qty:.2f} & \\textbf{{{red_qty:.1f}\\%}} \\\\",
        f"        XYZ Zoned (Frequency-Based) & {e_freq:.2f} & \\textbf{{{red_freq:.1f}\\%}} \\\\",
        f"        Velocity-Ranked (Optimal) & {e_opt:.2f} & {red_opt:.1f}\\% \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        f"The ABC-zoned slotting plan achieves a \\textbf{{{red_qty:.1f}\\% reduction}} in expected",
        r"picker travel distance versus the random baseline, comfortably exceeding the",
        r"\textbf{30\% target}. The concentration effect is structural: Class A SKUs generate",
        f"{Pa * 100:.1f}\\% of all picks yet are confined to the nearest {Na} slots.",
        r"The XYZ-zoned variant reaches " + f"{red_freq:.1f}\\%" + r" reduction by exploiting the",
        r"even sharper pick-probability concentration among Class X (consistent-demand) SKUs.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.95\linewidth]{../charts/q31_slotting_analysis.png}",
        r"\caption{Q3.1 Slotting Analysis: Zone Distribution and Travel Time Comparison}",
        r"\label{fig:q31-slotting}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Layout Recommendations (VILAS SNP Framework)}\label{layout}",
        r"\begin{itemize}",
        r"    \item \textbf{U-flow configuration}: Receiving and shipping docks on the same wall",
        r"          naturally concentrate the highest-convenience storage locations at the dock end.",
        r"    \item \textbf{Golden Zone}: AX SKUs placed at waist-to-shoulder ergonomic height,",
        r"          eliminating both horizontal travel distance and vertical MHE movement.",
        r"    \item \textbf{Two-bin replenishment for Class B}: A forward pick-face bin is",
        r"          replenished from the bulk reserve when on-hand drops below the ROP.",
        r"          WMS triggers the replenishment task automatically.",
        r"\end{itemize}",
        r"",
        r"\subsection{Question 3.2: Omni-Channel Pick-and-Pack Process Design}\label{q3.2}",
        r"",
        r"The outbound fulfillment process uses distinct operational pathways for B2B and B2C",
        r"channels, unified by a structured inventory allocation policy when stock is contested.",
        r"",
        r"\subsubsection{B2B Pathway — Pallet / Total Picking}\label{b2b-path}",
        r"\begin{enumerate}",
        r"    \item \textbf{Order release}: WMS validates on-hand stock against the B2B",
        r"          purchase order (contractual quantities and lead times).",
        r"    \item \textbf{Pick instruction}: Full-pallet or full-CTN pick task issued to operator.",
        r"    \item \textbf{Pick execution}: Operator uses forklift or reach truck to retrieve",
        r"          entire pallet(s) from the Forward Reserve Zone (B) or Reserve/Bulk Zone (C).",
        r"          Items bypass individual sortation.",
        r"    \item \textbf{B2B QC Station}: Wrap inspection, quantity verification, and",
        r"          outbound labeling.",
        r"    \item \textbf{Dispatch}: Pallets staged at outbound dock, loaded onto FTL truck.",
        r"\end{enumerate}",
        r"",
        r"\subsubsection{B2C / E-Commerce Pathway — Batch Picking + Zone Routing}\label{b2c-path}",
        r"\begin{enumerate}",
        r"    \item \textbf{Batch wave release}: Multiple B2C orders are grouped into a single",
        r"          pick wave based on SKU proximity and delivery-window urgency.",
        r"    \item \textbf{Batch pick-to-cart}: Picker traverses Zone 1 (Pick-Face Zone) in a",
        r"          single pass with a multi-compartment cart, collecting all items for the wave.",
        r"    \item \textbf{Sort \& consolidate}: At the sortation station, items are separated",
        r"          by individual order and consolidated into shipment boxes.",
        r"    \item \textbf{QC + pack}: Bubble wrap or polybag packing, shipping label applied.",
        r"    \item \textbf{Dispatch}: Parcels handed to last-mile courier.",
        r"\end{enumerate}",
        r"",
        r"\subsubsection{Stock Allocation Conflict and Escalation Policy}\label{conflict}",
        r"",
        r"When the same SKU is ordered simultaneously by a B2B client and a B2C customer",
        r"and on-hand stock is insufficient for both, the system resolves the shortage in two stages:",
        r"",
        r"\paragraph{Stage 1 — Automated Allocation (WMS).}",
        r"\begin{itemize}",
        r"    \item \textit{Rule 1 (SLA Protection)}: Allocate the full contractual quantity to",
        r"          the B2B order first, preventing penalty fees for under-delivery.",
        r"    \item \textit{Rule 2 (Pro-rata B2C)}: Distribute remaining stock to B2C orders",
        r"          pro-rata, with priority to orders with the shortest delivery windows.",
        r"\end{itemize}",
        r"",
        r"\paragraph{Stage 2 — Managerial Escalation (if Stage 1 insufficient).}",
        r"The WMS raises a critical ticket to the \textbf{Inventory Control \& Demand Planning Manager},",
        r"who can execute one or more of:",
        r"\begin{itemize}",
        r"    \item \textit{Action 1 (Safety Stock Draw)}: Release uncommitted buffer safety stock",
        r"          from the common pool (pre-computed for all Class A SKUs in Q2.2).",
        r"    \item \textit{Action 2 (Emergency Transfer)}: Initiate an inter-hub transfer",
        r"          between My Phuoc and Vinh Loc warehouses, leveraging their proximity",
        r"          within the Greater Ho Chi Minh City area.",
        r"    \item \textit{Action 3 (Partial Shipment)}: Contact the B2B client to obtain approval",
        r"          for a partial fulfillment; B2C customers notified of delay with revised ETA.",
        r"\end{itemize}",
        r"",
        r"Upon resolution, ERP and WMS records are updated and adjusted pick lists are",
        r"released to the warehouse floor. Figure \ref{fig:q32-flowchart} illustrates the",
        r"complete decision logic.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.88\linewidth]{../charts/q32_pick_pack_flowchart.png}",
        r"\caption{Q3.2 Omni-Channel Pick-and-Pack Process and Conflict Resolution Flowchart}",
        r"\label{fig:q32-flowchart}",
        r"\end{figure}",
        r"",
        r"\end{document}",
    ]

    tex_path = NOTES_DIR / NOTE3_FILENAME
    tex_path.write_text("\n".join(tex) + "\n", encoding="utf-8")
    print(f"Written {tex_path.name}")

    # Compile to PDF (try pdflatex, fall back to xelatex)
    import shutil
    compiler = shutil.which("pdflatex") or "/Library/TeX/texbin/pdflatex"
    if not Path(compiler).exists():
        compiler = shutil.which("xelatex") or "/Library/TeX/texbin/xelatex"
    if Path(compiler).exists():
        print(f"Compiling {NOTE3_FILENAME} with {Path(compiler).name} ...")
        for _ in range(2):
            subprocess.run(
                [compiler, "-interaction=nonstopmode", NOTE3_FILENAME],
                cwd=NOTES_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        pdf_path = NOTES_DIR / NOTE3_FILENAME.replace(".tex", ".pdf")
        if pdf_path.exists():
            print(f"Compiled {pdf_path.name} successfully.")
        else:
            print("PDF compilation may have failed; check the .log file.")
    else:
        print("No LaTeX compiler found — .tex file written but PDF not compiled.")


if __name__ == "__main__":

    import sys
    from pathlib import Path
    
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    
    from src.logage2026.config import CLEANED_DIR, TABLES_DIR
    
    print("Loading static cleaned data from disk...")
    try:
        shipments = pd.read_csv(CLEANED_DIR / "shipments_cleaned.csv")
        abc_xyz = pd.read_csv(TABLES_DIR / "q11_sku_abc_xyz.csv")
        abc_xyz_matrix = pd.read_csv(TABLES_DIR / "q11_abc_xyz_matrix_frequency_summary.csv")
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
        
        # NOTE: When running statically from __main__, Part 2 tables must also be loaded.
        # Since this __main__ block is mainly for testing Part 1, we provide dummy/empty dfs for Part 2
        # if the files don't exist yet, to prevent it from crashing.
        try:
            safety_stock_class_a = pd.read_csv(TABLES_DIR / "safety_stock_class_a.csv")
            lead_time_sensitivity = pd.read_csv(TABLES_DIR / "lead_time_sensitivity.csv")
            inventory_pooling_summary = pd.read_csv(TABLES_DIR / "inventory_pooling_summary.csv")
            hcm_district_summary = pd.read_csv(TABLES_DIR / "hcm_district_summary.csv")
            network_model_evaluation = pd.read_csv(TABLES_DIR / "q21_network_model_evaluation.csv")
            cf_path = TABLES_DIR / "q21_channel_flow_summary.csv"
            q21_channel_flow_summary = pd.read_csv(cf_path) if cf_path.exists() else pd.DataFrame()
        except FileNotFoundError:
            safety_stock_class_a = pd.DataFrame()
            lead_time_sensitivity = pd.DataFrame()
            inventory_pooling_summary = pd.DataFrame([{"scenario": "Separated B2B + B2C", "total_ss": 0, "savings_pct": 0}, {"scenario": "Pooled (Shared)", "total_ss": 0, "savings_pct": 0}])
            hcm_district_summary = pd.DataFrame({"quantity": [0]})
            network_model_evaluation = pd.DataFrame({"sla_status": [], "quantity": [], "orders": [], "best_rdc_km": []})
            q21_channel_flow_summary = pd.DataFrame()
            
        abc_xyz_matrix_volatility = pd.read_csv(TABLES_DIR / "q11_abc_xyz_matrix_volatility_summary.csv")
        print("Generating report text from static output...")
        write_notes(
            shipments, abc_xyz, abc_xyz_matrix, abc_xyz_matrix_volatility, fast_moving_summary,
            classification_metadata, missing_data_summary, geography_coverage_summary,
            warehouse_region_summary, customer_cluster_summary, warehouse_imbalance_summary,
            q12_region_orders_quantity_summary, q12_province_cluster_summary,
            q12_province_demand_summary, q12_province_warehouse_dominance_summary,
            q12_urban_provincial_summary,
            q12_warehouse_imbalance_visual_summary,
            q13_segment_profile_summary, q13_segment_packaging_summary,
            q13_segment_geographic_spread_summary,
            safety_stock_class_a, lead_time_sensitivity, inventory_pooling_summary,
            hcm_district_summary, network_model_evaluation, q21_channel_flow_summary,
        )
        print(f"Reports written successfully to outputs/round2/notes/{NOTE1_FILENAME} and {NOTE2_FILENAME}!")
    except Exception as e:
        print(f"Error loading static output: {e}")
        print("Please run run_analysis.py first to generate the outputs.")

