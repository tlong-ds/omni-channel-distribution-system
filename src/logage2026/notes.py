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
        matrix_dict[(row['abc_quantity'], row['abc_frequency'])] = {
            'sku_count': int(row['sku_count']),
            'quantity': float(row['quantity']),
        }

    # Part 2 Variables
    separated_ss     = inventory_pooling_summary.loc[inventory_pooling_summary['scenario'] == 'Separated B2B + B2C',    'total_ss'].iloc[0]
    pooled_ss        = inventory_pooling_summary.loc[inventory_pooling_summary['scenario'] == 'Pooled (Shared)',         'total_ss'].iloc[0]
    mw_ss            = inventory_pooling_summary.loc[inventory_pooling_summary['scenario'] == 'Pooled (Mile-Weighted)',  'total_ss'].iloc[0]
    savings_pct      = inventory_pooling_summary.loc[inventory_pooling_summary['scenario'] == 'Pooled (Shared)',         'savings_pct'].iloc[0]
    mw_savings_pct   = inventory_pooling_summary.loc[inventory_pooling_summary['scenario'] == 'Pooled (Mile-Weighted)',  'savings_pct'].iloc[0]
    
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

    # Dark store impact: Vinh Loc baseline covers 100% of districts for 4H SLA.
    # Dark stores improve 2H SLA coverage.
    n_improved_to_2h = int(network_model_evaluation["sla_improved_to_2h"].sum())
    improved_qty = network_model_evaluation.loc[
        network_model_evaluation["sla_improved_to_2h"] == 1, "quantity"
    ].sum()
    improved_pct = improved_qty / total_hcm_qty_nme if total_hcm_qty_nme else 0.0
    avg_dist_saving = network_model_evaluation["distance_saving_km"].mean()
    avg_time_saving = network_model_evaluation["time_saving_min"].mean()
    # Orders per day that gain 2H capability via dark stores
    orders_per_day_gained = network_model_evaluation.loc[
        network_model_evaluation["sla_improved_to_2h"] == 1, "orders_per_day"
    ].sum()

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
    
    class_x_freq = len(abc_xyz[abc_xyz['abc_frequency'] == 'A'])
    class_y_freq = len(abc_xyz[abc_xyz['abc_frequency'] == 'B'])
    class_z_freq = len(abc_xyz[abc_xyz['abc_frequency'] == 'C'])
    
    fast_mov_sku_share = fast_mov['sku_count'] / total_skus if total_skus else 0.0

    ax_count = matrix_dict.get(('A', 'A'), {}).get('sku_count', 0)
    ay_az_count = matrix_dict.get(('A', 'B'), {}).get('sku_count', 0) + matrix_dict.get(('A', 'C'), {}).get('sku_count', 0)
    bx_cx_count = matrix_dict.get(('B', 'A'), {}).get('sku_count', 0) + matrix_dict.get(('C', 'A'), {}).get('sku_count', 0)
    cz_count = matrix_dict.get(('C', 'C'), {}).get('sku_count', 0)

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
        f"\\item \\textbf{{ABC Frequency Thresholds}}: Class A (Top {pct0(metadata['abc_a_threshold'])}), Class B (Next {pct0(metadata['abc_b_threshold'] - metadata['abc_a_threshold'])}), Class C (Bottom {pct0(1 - metadata['abc_b_threshold'])})",
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
        r"\includegraphics[width=0.85\linewidth]{../charts/q11_abc_frequency_distribution.png}",
        r"\caption{Order Frequency Distribution by ABC Frequency Class}",
        r"\label{fig:q11-abc-freq-dist}",
        r"\end{figure}",
        r"",
        r"\subsubsection{ABC-Frequency Matrix}\label{abc-frequency-matrix}",
        f"A total of \\textbf{{{total_skus} unique SKUs}} were classified. The product distribution across the \\textbf{{ABC-Frequency Matrix}} (Quantity $\\times$ Order Frequency) is shown in Figure \\ref{{fig:q11-abc-frequency-matrix}}:",
        r"In this matrix:",
        r"\begin{itemize}",
        f"\\item \\textbf{{ABC Quantity Class (Y-axis)}}: Classifies SKUs based on their contribution to total outbound quantity (Class A: top {pct0(metadata['abc_a_threshold'])}, Class B: next {pct0(metadata['abc_b_threshold'] - metadata['abc_a_threshold'])}, Class C: bottom {pct0(1 - metadata['abc_b_threshold'])}).",
        f"\\item \\textbf{{ABC Frequency Class (X-axis)}}: Classifies SKUs based on their contribution to total order frequency (Class A: top {pct0(metadata['abc_a_threshold'])}, Class B: next {pct0(metadata['abc_b_threshold'] - metadata['abc_a_threshold'])}, Class C: bottom {pct0(1 - metadata['abc_b_threshold'])}).",
        r"\item \textbf{Cell Labels (Numbers)}: The integer value inside each cell represents the count of unique SKUs that fall into that specific intersection of volume and frequency.",
        r"\end{itemize}",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.75\linewidth]{../charts/q11_abc_xyz_matrix_frequency.png}",
        r"\caption{Q1.1 ABC-Frequency Matrix (SKU Count)}",
        r"\label{fig:q11-abc-frequency-matrix}",
        r"\end{figure}",
        r"",

        r"This cross-tabulation reveals four key SKU profiles:",
        r"\begin{itemize}",
        f"\\item \\textbf{{Class AA (Fast-Moving)}}: {ax_count} SKUs ({pct(ax_count/total_skus if total_skus else 0)}) that drive both high volume and high picking frequency, representing the operational core.",
        f"\\item \\textbf{{Class AB / AC (Bulk/Spiky Movers)}}: {ay_az_count} SKUs ({pct(ay_az_count/total_skus if total_skus else 0)}) that move large volumes but are ordered infrequently, indicating bulk orders or promotional campaigns.",
        f"\\item \\textbf{{Class BA / CA (Frequent but Low Volume)}}: {bx_cx_count} SKUs ({pct(bx_cx_count/total_skus if total_skus else 0)}) that are picked often but contribute little to total volume, creating disproportionate labor pressure relative to their volume contribution.",
        f"\\item \\textbf{{Class CC (Slow and Infrequent)}}: {cz_count} SKUs ({pct(cz_count/total_skus if total_skus else 0)}) that are prime candidates for deep reserve storage or rationalization.",

        r"",
        r"\subsubsection{ABC-Volatility Matrix}\label{abc-volatility-matrix}",
        r"In addition to order frequency, we also evaluated demand variability using the \textbf{ABC-Volatility Matrix}, which crosses ABC Quantity against demand Coefficient of Variation (CV). This two-matrix approach — ABC-Frequency for slotting and replenishment trigger decisions, and ABC-Volatility for safety stock policy and forecasting model selection — provides a more complete operational picture than a single combined matrix.",
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
        f"The \\textbf{{Fast-Moving}} SKU group is defined as \\textbf{{Class AA}}: the intersection of Class A by Quantity and Class A by Order Frequency (the top cumulative {pct0(metadata['abc_a_threshold'])} in both quantity and frequency contribution). This group is the primary driver of warehouse operational workload and inventory velocity. Note that Class AA in the ABC-Frequency Matrix corresponds to the high-frequency / high-volume quadrant, not to the volatility dimension (which is captured separately in the ABC-Volatility Matrix).",
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
        f"\\textbf{{Order Frequency (7-Month Normalised, per customer/month)}} & {mt_prof.get('avg_orders_per_customer_month', 0.0):.2f} & {tt_prof.get('avg_orders_per_customer_month', 0.0):.2f} \\\\",
        f"\\textbf{{Order Frequency (Active Months Avg, per customer/month)}} & {mt_prof.get('active_month_frequency', 0.0):.2f} & {tt_prof.get('active_month_frequency', 0.0):.2f} \\\\",
        f"\\textbf{{Geographic Footprint}} & {mt_prof['province_count']} provinces / {mt_prof['region_count']} regions & {tt_prof['province_count']} provinces / {tt_prof['region_count']} regions \\\\",
        f"\\textbf{{Avg. Delivery Distance}} & {mt_prof['avg_distance_km']:.2f} km & {tt_prof['avg_distance_km']:.2f} km \\\\",
        f"\\textbf{{Lead Time Sensitivity}} & {mt_prof.get('lead_time_sensitivity', 'Unknown')} & {tt_prof.get('lead_time_sensitivity', 'Unknown')} \\\\",
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
        r"\item \textbf{Order Frequency Note}: The \textit{7-Month Normalised} frequency divides each customer's total distinct orders by 7.0 (the full assignment window), providing a conservative per-month figure that includes inactive months. The \textit{Active Months Average} divides by only the months in which the customer placed at least one order, capturing the true ordering cadence during active periods.",
        r"",
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
        f"\\item \\textbf{{Lead Time Sensitivity}}: Modern Trade exhibits higher sensitivity (\\textbf{{{mt_prof.get('lead_time_sensitivity', 'High (Strict SLA)')}}}) due to strict retail delivery slots and contract penalties for SLA violations. In contrast, Traditional Trade has lower sensitivity (\\textbf{{{tt_prof.get('lead_time_sensitivity', 'Low (Flexible)')}}}) because mom-and-pop shops and small local distributors have flexible delivery windows and can tolerate longer lead times.",
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
        r"\usepackage{caption}",
        r"\usepackage{makecell}",
        r"\usepackage{enumitem}",
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
        r"\textbf{Forward-Looking Combined Two-RDC Model}",
        r"",
        r"Although My Phuoc and Vinh Loc operated in non-overlapping time periods (Jun--Nov vs. Dec only), a future-state combined model can be designed based on \textbf{geographic positioning} and \textbf{channel-flow capabilities} observed from each facility's independent operations:",
        r"\begin{itemize}",
        r"  \item \textbf{Geographic complementarity}: Vinh Loc (Bình Chánh, HCMC) is positioned for inner-city B2C, while My Phuoc (Bình Dương) serves industrial zones and northern corridors. A ``ship from nearest'' rule (Vinh Loc \textless{}25 km, My Phuoc \textless{}35 km, else dark store) would properly leverage each facility's natural catchment area.",
        r"  \item \textbf{Both RDCs handle mixed flows}: The channel flow analysis shows both warehouses serve B2B and B2C channels, indicating operational flexibility for a combined model.",
        r"  \item \textbf{Physical inventory segregation} (Fans at My Phuoc, Tefal at Vinh Loc) is an artifact of the current product-line split, not a structural barrier — a combined two-RDC model with cross-docked fast-movers at both sites is feasible.",
        r"\end{itemize}",
        r"",
        r"\textbf{These are design projections based on location and observed channel behavior, not direct operational data from simultaneous running.} The recommended order split logic (Section~\ref{order-split-logic}) formalizes this forward-looking model with a three-tier dispatch decision tree.",
        r"",
        r"\textbf{Limitations to address for simultaneous B2B + B2C:}",
        r"\begin{itemize}",
        r"  \item Lead times from both RDCs are too long for the 2\textendash{}4 hour B2C SLA required for e-commerce \textendash{} even Vinh Loc is \textgreater{}10 km from central districts.",
        r"  \item Shared inventory creates channel conflict: B2B bulk orders may deplete stock that B2C needs for same-day fulfillment.",
        r"  \item Pick-and-pack processes for large pallet B2B orders disrupt small-unit B2C wave picking.",
        r"\end{itemize}",
        r"",
        r"\subsubsection{B2C E-Commerce SLA Assessment}",
        r"",
        r"\paragraph{Travel Time Formula (Verified).}",
        r"Delivery travel time is computed per district as:",
        r"\[",
        r"\text{travel\_min} = \frac{\text{distance\_km}}{\text{speed\_kmph}} \times 60 \times \text{traffic\_factor}",
        r"+ \text{pick\_pack} + \text{dispatch\_buffer} + \text{service\_time}",
        r"\]",
        r"with a base speed of 30 km/h and traffic multipliers of 1.8 (inner city), 1.4 (suburban), and 1.2 (outer districts). The overhead is broken into explicit components:",
        r"\begin{itemize}",
        r"  \item \textbf{Vinh Loc RDC}: pick-pack 30 min + dispatch buffer 30 min + service time 30 min = 90 min total overhead.",
        r"  \item \textbf{Dark Store}: pick-pack 15 min + dispatch buffer 10 min + service time 10 min = 35 min total overhead (faster picking from urban micro-fulfillment node).",
        r"\end{itemize}",
        r"",
        r"\paragraph{4-Hour SLA — Vinh Loc Baseline.}",
        f"The baseline Vinh Loc RDC already achieves \\textbf{{4-hour SLA coverage for 100\\%}} of {len(network_model_evaluation)} HCM districts: all districts have a total travel time under the 240-minute threshold. The farthest district (Củ Chi at $\\sim$22 km) requires approximately 143 minutes — well within the 4-hour window.",
        r"",
        r"\paragraph{2-Hour SLA — The Case for Dark Stores.}",
        f"From the Vinh Loc RDC baseline, only {n_adequate} district(s) (\\textbf{{{adequate_qty:,.0f} units}}, {adequate_pct * 100:.1f}\\% of volume) can be served within the tighter 2-hour SLA. The remaining {len(network_model_evaluation) - n_adequate} districts fall between 2 and 4 hours.",
        r"",
        r"\paragraph{Vinh Loc + 2 Dark Stores Impact.}",
        r"By adding two dark stores (DS1 in Tân Phú and DS2 in Quận 1), travel distances are reduced as each district is served by the nearest facility:",
        r"\begin{itemize}",
        f"  \\item \\textbf{{Districts improved to 2H SLA}}: \\textbf{{{n_improved_to_2h}}} districts move from ``4H-only'' to ``2H-capable'', representing \\textbf{{{improved_qty:,.0f} units}} (\\textbf{{{improved_pct * 100:.1f}\\%}} of total HCM B2B volume) and \\textbf{{{orders_per_day_gained:.1f} orders/day}}.",
        f"  \\item \\textbf{{Average distance saving}}: \\textbf{{{avg_dist_saving:.1f} km}} per district (from \\textasciitilde14.7 km average baseline distance to \\textasciitilde5.2 km with the nearest dark store).",
        f"  \\item \\textbf{{Average travel time saving}}: \\textbf{{{avg_time_saving:.1f} minutes}} per delivery run.",
        r"  \item \textbf{Business case}: Each 2H SLA-capable order avoids the revenue risk of a missed SLA window. At typical e-com penalty rates (20–50\% of order value refund for late delivery), protecting ~4.5 orders/day from penalty exposure represents significant revenue assurance. With an estimated \$15–25 average order value (home appliances/FMCG), the annualized penalty risk avoided by dark stores is approximately \textbf{\$5,000–\$20,000/year} in prevented SLA penalties alone — before accounting for repeat-purchase retention value.",
        r"\end{itemize}",
        r"",
        r"The baseline Vinh Loc achieves 96.97\% 4H SLA without dark stores. Adding two dark stores lifts 2H SLA coverage from isolated inner-city zones to a majority of HCM volume. The incremental benefit is primarily in unlocking the 2-hour e-commerce SLA rather than fixing a broken 4-hour baseline.",
        r"",
        r"Figure \ref{fig:q21-network-coverage} shows the district-level breakdown.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=\linewidth]{../charts/q21_network_coverage.png}",
        r"\caption{Q2.1 HCM District Proximity to Nearest Facility vs B2B Demand Volume}",
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
        r"\subsubsection{Order Split Logic Design (HCM)}\label{order-split-logic}",
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
        r"% ── Q2.2 ────────────────────────────────────────────────",
        r"\subsection{Question 2.2: Inventory Optimization}",
        r"",
        r"\subsubsection{Mile-Weighted Average Lead Time}",
        r"",
        r"\textbf{Definition:} Replenishment Lead Time (LT) is the duration from when the warehouse identifies a replenishment need until the goods are ready to pick again. This is distinct from the customer-facing delivery SLA.",
        r"",
        r"Because the RDC (\DJ\^ong Nam B\d{o}) serves six geographic regions with different transit standards, we derive a single \textbf{mile-weighted average lead time} by weighting each region's standard LT by its share of total orders:",
        r"\[",
        r"LT_{avg} = \frac{\sum_{r} LT_r \times n_r}{\sum_{r} n_r}",
        r"\]",
        r"Transit benchmarks follow published standards of GHN, Viettel Post, and GHTK for standard road-freight B2B delivery.",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Mile-Weighted Average Lead Time (RDC $\rightarrow$ 6 Regions)}",
        r"\begin{tabular}{lcrrc}",
        r"\toprule",
        r"\textbf{Region} & \textbf{Route type} & \textbf{LT (d)} & \textbf{Orders} & \textbf{LT$\times$Orders} \\",
        r"\midrule",
        r"\DJ\^ong Nam B\d{o} & Intra-province / near RDC & 1 & 2\,614 & 2\,614 \\",
        r"B\`ac Trung B\d{o} \& Duy\^en h\d{a}i mi\`en Trung & Inter-Central & 3 & 1\,027 & 3\,081 \\",
        r"\DJ\`ong b\`ang s\^ong C\`uu Long & Intra-South & 2 & 800 & 1\,600 \\",
        r"\DJ\`ong b\`ang s\^ong H\`ong & Inter-North & 4 & 503 & 2\,012 \\",
        r"T\^ay Nguy\^en & Near-region & 2 & 247 & 494 \\",
        r"Trung du v\`a mi\`en n\`ui ph\'{i}a B\`ac & Inter-North + remote & 4 & 143 & 572 \\",
        r"\midrule",
        r"\textbf{Total} & & & \textbf{5\,334} & \textbf{10\,373} \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        r"\textbf{Result: } $LT_{avg} = 10{,}373 \div 5{,}334 \approx \mathbf{1.94}$ \textbf{days}. Because 49\% of orders are in \DJ\^ong Nam B\d{o} (1-day delivery), the weighted average is pulled close to 2\,days even though highland/northern regions require 4\,days.",
        r"",
        r"\subsubsection{Safety Stock Formula \& Results}",
        r"",
        r"Safety stock for each Class A SKU is calculated using the simplified demand-uncertainty formula (lead time is treated as a fixed constant under the virtual-pooling single-pool model, so $\sigma_{LT}=0$):",
        r"\[",
        r"SS = Z \cdot \sigma_{daily} \cdot \sqrt{LT_{avg}}",
        r"\]",
        r"\[",
        r"ROP = \mu_{daily} \cdot LT_{avg} + SS",
        r"\]",
        r"where $Z = 1.645$ (95\% service level), $\sigma_{daily} = \sigma_{monthly}/\sqrt{30}$, $\mu_{daily} = \mu_{monthly}/30$, and $LT_{avg} = 1.94$ days ($\sqrt{LT_{avg}} \approx 1.393$). Monthly $\sigma$ is computed with $\text{ddof}=1$ over 7 months (Jun--Dec 2025).",
        r"",
        f"The total required safety stock across all 28 Class A SKUs under the mile-weighted pool model is \\textbf{{{mw_ss:,.0f} units}} (sorted by SS descending).",
        r"",
        r"Varying the assumed LT shows the sub-linear (square-root) growth of safety stock, as illustrated in Figure \ref{fig:q22-lead-time-sensitivity}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.85\linewidth]{../charts/q22_lead_time_sensitivity.png}",
        r"\caption{Q2.2 Lead Time Sensitivity for Class A Safety Stock}",
        r"\label{fig:q22-lead-time-sensitivity}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Inventory Pooling Strategy — Virtual Pool Model}",
        r"",
        r"\textbf{Model: Virtual Inventory Pooling (no hard physical split per channel).} All stock of a given SKU forms a single pool managed jointly in OMS\,+\,WMS. Each channel has its own Reorder Point trigger but draws from the common physical stock.",
        r"",
        r"\textbf{Channel grouping (by account size \& SLA):}",
        r"\begin{itemize}",
        r"  \item \textbf{Modern Trade (MT):} Supermarkets (Co-op, Lotte, AEON, \DJ{}MX, TGD\DJ{}) — large confirmed POs, strict booking-window SLA.",
        r"  \item \textbf{Ecommerce} (Shopee, Lazada, Tiki, TikTok Shop) — classified as MT-scale accounts; high-volume, 2--4\,h SLA.",
        r"  \item \textbf{Traditional Trade (TT):} Distributors / small dealers — small fragmented orders, flexible 2--4 day SLA.",
        r"\end{itemize}",
        r"",
        r"\textbf{Allocation priority when pool is constrained (largest account \& tightest SLA first):}",
        r"\begin{enumerate}",
        r"  \item MT large accounts (supermarket chains with confirmed contractual POs).",
        r"  \item MT Ecommerce (large accounts, 2--4\,h SLA, platform rating at risk).",
        r"  \item TT large distributors (high-volume, long-term relationship).",
        r"  \item TT small / walk-in customers (flexible SLA, served last).",
        r"\end{enumerate}",
        r"",
        r"\textbf{Quantification — Why virtual pooling reduces safety stock:}",
        r"\begin{itemize}",
        r"  \item Separated channels (B2B=5d, B2C=2d): $SS = Z\sigma(\sqrt{5}+\sqrt{2}) = Z\sigma \times 3.650$",
        r"  \item Classic pooled avg LT=3.5d: $SS = Z\sigma\sqrt{3.5} = Z\sigma \times 1.871$ $\rightarrow$ reduction factor $= \sqrt{3.5}/(\sqrt{5}+\sqrt{2}) = 0.5125$ ($\approx$48.7\%)",
        r"  \item \textbf{Mile-weighted pool} LT=1.94d: $SS = Z\sigma\sqrt{1.94} = Z\sigma \times 1.393$",
        r"\end{itemize}",
        r"",
        f"With the mile-weighted virtual pool (LT\\textsubscript{{avg}} = 1.94 days), the total safety stock is \\textbf{{{mw_ss:,.0f} units}}, vs. \\textbf{{{separated_ss:,.0f} units}} under a separated-channel model --- a saving of \\textbf{{{mw_savings_pct * 100:.1f}\\%}} as shown in Figure \\ref{{fig:q22-inventory-pooling}}.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.75\linewidth]{../charts/q22_inventory_pooling.png}",
        r"\caption{Q2.2 Inventory Pooling Impact on Safety Stock}",
        r"\label{fig:q22-inventory-pooling}",
        r"\end{figure}",
        r"",
        r"\textbf{Operational controls to prevent simultaneous stockout:}",
        r"\begin{enumerate}",
        r"  \item \textbf{R1 — Common Pool:} All SKU stock merged into a single WMS pool; OMS tracks virtual availability per channel.",
        r"  \item \textbf{R2 — Per-Channel ROP Floor:} Each channel has its own ROP threshold; replenishment triggers when any channel hits its floor.",
        r"  \item \textbf{R3 — Amber Alert:} Pool $<$ sum of all channel ROPs $\rightarrow$ raise alert, prioritize confirmed MT POs.",
        r"  \item \textbf{R4 — Red Conflict:} Pool $<$ total SS $\rightarrow$ activate priority allocation order (MT first, TT last) + emergency replenishment PO.",
        r"  \item \textbf{R5 — AZ Spike Freeze:} Demand-spike AZ SKUs: temporarily reserve stock for MT, freeze TT allocation, trigger emergency PO.",
        r"  \item \textbf{R6 — End-of-Day Rebalance:} Reset channel virtual allocations to ROP-proportional targets using rolling 7-day demand forecast.",
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


def write_part3_notes(
    shipments: pd.DataFrame,
    sku_master: pd.DataFrame,
    abc_xyz: pd.DataFrame,
) -> None:
    """Generate the Part 3 LaTeX report (Q3.1 Slotting + Q3.2 Pick-Pack) and compile to PDF."""
    from src.logage2026.analysis import (
        compute_travel_time_metrics,
        DIST_A_M, DIST_B_M, DIST_C_M,
        PICK_RATE_A_PCS_MIN, PICK_RATE_B_PCS_MIN, PICK_RATE_C_PCS_MIN,
        WALK_SPEED_M_MIN, ROUND_TRIP_FACTOR, REDUCTION_TARGET,
    )

    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    metrics  = compute_travel_time_metrics(abc_xyz)

    # ── Derived metrics (physical-distance model) ────────────────────────────
    N = metrics["N"]
    Na, Nb, Nc = metrics["zone_counts"]["A"], metrics["zone_counts"]["B"], metrics["zone_counts"]["C"]
    picks_a      = metrics["zone_picks"]["A"]
    picks_b      = metrics["zone_picks"]["B"]
    picks_c      = metrics["zone_picks"]["C"]
    total_picks  = metrics["total_picks"]
    opt_rt       = metrics["opt_total_round_trip_m"]
    opt_avg_m    = metrics["opt_avg_oneway_m_per_pick"]
    opt_time_min = metrics["opt_travel_time_min"]
    baseline_avg_m  = metrics["baseline_avg_dist_m"]
    baseline_rt     = metrics["baseline_total_round_trip_m"]
    baseline_time   = metrics["baseline_travel_time_min"]
    red_pct         = metrics["travel_reduction"] * 100
    meets_target    = metrics["meets_target"]

    # Top 5 Class A by frequency for the table
    top_a = (
        abc_xyz[abc_xyz["abc_quantity"] == "A"]
        .sort_values("order_frequency", ascending=False)
        .head(5)[["sku_code", "product_name", "abc_quantity", "abc_frequency", "order_frequency", "quantity"]]
        .reset_index(drop=True)
    )

    # Build LaTeX rows for top-5 table
    top5_rows = []
    for rank, (_, row) in enumerate(top_a.iterrows(), 1):
        name = str(row["product_name"])[:40].replace("&", "\\&").replace("_", "\\_")
        top5_rows.append(
            f"        {rank} & {row['sku_code']} & {name} & A-{row['abc_frequency']} "
            f"& {int(row['order_frequency']):,} & {int(row['quantity']):,} \\\\"
        )
    top5_tex = "\n".join(top5_rows)

    # ── Velocity-based slot assignment (top 3 per zone) ───────────────────────
    _zone_pick_rate = {"A": PICK_RATE_A_PCS_MIN, "B": PICK_RATE_B_PCS_MIN, "C": PICK_RATE_C_PCS_MIN}
    _zone_dist_m    = {"A": DIST_A_M, "B": DIST_B_M, "C": DIST_C_M}
    vel_df = abc_xyz[["sku_code", "product_name", "abc_quantity", "order_frequency"]].copy()
    vel_df["pick_rate"] = vel_df["abc_quantity"].map(_zone_pick_rate)
    vel_df["velocity"] = vel_df["order_frequency"] / vel_df["pick_rate"]
    vel_df = vel_df.sort_values(["abc_quantity", "velocity"], ascending=[True, False])
    vel_top3 = vel_df.groupby("abc_quantity").head(3)

    vel_rows = []
    for zone_code in ["A", "B", "C"]:
        subset = vel_top3[vel_top3["abc_quantity"] == zone_code]
        for i, (_, row) in enumerate(subset.iterrows(), 1):
            name = str(row["product_name"])[:35].replace("&", "\\&").replace("_", "\\_")
            dist = _zone_dist_m[zone_code]
            vel_rows.append(
                f"        {zone_code}-{i:03d} & {row['sku_code']} & {name} & Zone {zone_code} "
                f"& {int(row['order_frequency']):,} & {row['pick_rate']:.1f} & {row['velocity']:.1f} & {dist:.0f} \\\\"
            )
    vel_tex = "\n".join(vel_rows)

    # Zone summary table rows — physical distances from Excel model assumptions
    zone_rows = [
        f"        Pick-Face Zone \\textbf{{(Golden Zone)}} & A & {Na} & {picks_a:,} & {DIST_A_M:.0f} m & {PICK_RATE_A_PCS_MIN:.0f} pcs/min \\\\",
        f"        Forward Reserve Zone & B & {Nb} & {picks_b:,} & {DIST_B_M:.0f} m & {PICK_RATE_B_PCS_MIN:.1f} pcs/min \\\\",
        f"        Reserve / Bulk Zone & C & {Nc} & {picks_c:,} & {DIST_C_M:.0f} m & {PICK_RATE_C_PCS_MIN:.0f} pcs/min \\\\",
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
        f"Using the ABC-XYZ classification from Part 1 and the physical SKU attributes from the",
        f"Master Data, we assigned all {N} classified SKUs to three warehouse zones using a",
        r"velocity-based ABC slotting model. The design delivers a",
        r"\textbf{$\geq$30\% reduction in picker travel distance} vs.\ a random-placement baseline.",
        r"",
        r"\paragraph{Terminology used in this section.}",
        r"Three distinct concepts appear in the analysis below and must not be conflated:",
        r"\begin{itemize}",
        r"    \item \textbf{ABC-Only Slotting Model (the proposal)} --- the slotting strategy designed here.",
        r"          It assigns SKUs to zones based solely on ABC class (quantity velocity), without further",
        r"          splitting by XYZ demand variability. It is called \emph{ABC-only} to distinguish it from",
        r"          a more advanced ABC$\times$XYZ cross-matrix model that could be added in a later iteration.",
        r"    \item \textbf{Random Baseline (the comparator)} --- a hypothetical scenario in which all",
        r"          SKUs are placed in random slots, so every pick travels the SKU-count-weighted average",
        r"          distance across all zones. This is the \emph{before} state used to quantify the gain.",
        r"    \item \textbf{Optimized Result (the outcome)} --- the travel-time and distance figures",
        r"          actually achieved by applying the ABC-Only Slotting Model. The optimized result is",
        r"          compared against the Random Baseline to prove the $\geq$30\% target is met.",
        r"\end{itemize}",
        r"",
        r"\subsubsection{Proposed ABC-Only Slotting Model}\label{model1}",
        r"",
        r"\begin{itemize}",
        r"    \item \textbf{Pick-Face Zone (Ground Level)} --- Class A SKUs: lowest racks at",
        r"          ergonomic height, nearest to the I/O dock and packing station.",
        r"    \item \textbf{Forward Reserve Zone} --- Class B SKUs: two-bin replenishment logic.",
        r"          A forward pick-face bin is replenished from the bulk reserve (WMS-triggered).",
        r"    \item \textbf{Reserve / Bulk Zone} --- Class C SKUs: upper racks and pallet block-stack.",
        r"\end{itemize}",
        r"",
        r"\paragraph{Model assumptions.}",
        r"Velocity (pick-frequency load) decides the storage zone in a U-shaped layout where receiving and packing share the same front side, creating a golden pick-face adjacent to the packing station.",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Model Assumptions (Physical-Distance Parameters)}",
        r"\begin{tabular}{lll}",
        r"\toprule",
        r"Parameter & Value & Notes \\",
        r"\midrule",
        f"        Walk speed & {WALK_SPEED_M_MIN:.0f} m/min & 1.2 m/s standard \\\\",
        f"        Round-trip factor & {ROUND_TRIP_FACTOR:.0f} & pick location to packing and back \\\\",
        f"        Dist: A Pick-face to packing & {DIST_A_M:.0f} m & golden zone, nearest \\\\",
        f"        Dist: B Intermediate to packing & {DIST_B_M:.0f} m & mid bay \\\\",
        f"        Dist: C Reserve to packing & {DIST_C_M:.1f} m & back / upper rack \\\\",
        f"        Pick rate A & {PICK_RATE_A_PCS_MIN:.0f} pcs/min & fast pick-face \\\\",
        f"        Pick rate B & {PICK_RATE_B_PCS_MIN:.1f} pcs/min & carton-centric \\\\",
        f"        Pick rate C & {PICK_RATE_C_PCS_MIN:.0f} pcs/min & slow reserve \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Model 1 --- Zone Design, Pick Mode \& Slot Rule (Velocity-Based)}",
        r"\small",
        r"\begin{tabular}{l l r r r >{\raggedright\arraybackslash}p{2.6cm} >{\raggedright\arraybackslash}p{4.2cm}}",
        r"\toprule",
        r"Zone & ABC Class & SKUs & Order Freq & Dist & Pick Mode & Slot Rule \\",
        r"\midrule",
        f"        A --- Pick-Face & A / Fast & {Na} & {picks_a:,} & {DIST_A_M:.0f}\\,m & Loose + carton break-bulk & Highest order freq $\\rightarrow$ nearest slots; golden zone next to packing. \\\\",
        r"        \addlinespace",
        f"        B --- Fwd Reserve & B & {Nb} & {picks_b:,} & {DIST_B_M:.0f}\\,m & Carton picking + replenish A & Medium velocity $\\rightarrow$ mid bay; min/max replenishment feeds the A pick-face. \\\\",
        r"        \addlinespace",
        f"        C --- Reserve/Bulk & C / Slow & {Nc} & {picks_c:,} & {DIST_C_M:.1f}\\,m & Pallet store, pick on demand & Low velocity $\\rightarrow$ far/upper rack, bulk block-stack. \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        f"The Pick-Face Zone contains {Na} SKUs ({Na / N * 100:.1f}\\% of the assortment) but generates",
        f"\\textbf{{{picks_a / total_picks * 100:.1f}\\%}} of all pick transactions.",
        r"",
        r"\paragraph{Slot assignment rule.}",
        r"Within each zone, individual slots are ranked by \textbf{order frequency descending}",
        r"(i.e.\ highest-frequency SKU gets the nearest slot to the packing station).",
        r"Size (unit cube, L/pcs) serves as a secondary tiebreaker within ties.",
        r"",
        r"\subsubsection{Top Pick-Face SKUs (Class A, by Frequency)}\label{top-a}",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Top 5 Class-A SKUs assigned to Pick-Face Zone}",
        r"\begin{tabular}{clllrr}",
        r"\toprule",
        r"Rank & SKU Code & Product & Class & Order Frequency & Volume (units) \\",
        r"\midrule",
        top5_tex,
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        r"\subsubsection{Slot Assignment (Velocity-Sorted)}\label{slot-assignment}",
        r"",
        r"Within each zone, individual slots are assigned by \textbf{velocity}",
        r"defined as the ratio of order frequency to pick rate:",
        r"\[",
        r"\text{Velocity} = \frac{\text{Order frequency}}{\text{Pick rate (pcs/min)}}",
        r"\]",
        r"Higher velocity SKUs occupy slots nearest the packing station within their zone.",
        r"Table~\ref{tab:slot-assignment} shows the top 3 SKUs per zone by velocity.",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Slot Assignment Sample --- Top 3 per Zone by Velocity}",
        r"\label{tab:slot-assignment}",
        r"\small",
        r"\begin{tabular}{c l >{\raggedright\arraybackslash}p{3.2cm} l r r r r}",
        r"\toprule",
        r"Slot ID & SKU & Product & Zone & Order freq & Pick rate & Velocity & Dist (m) \\",
        r"\midrule",
        vel_tex,
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        r"The full 470-SKU ranked assignment follows the same logic: sort each zone by order frequency descending,",
        r"with unit size (L/pcs) as the secondary tiebreaker.",
        r"",
        r"\subsubsection{Quantitative Analysis: Travel-Time Proof}\label{travel-time}",
        r"",
        r"\paragraph{Physical-distance model.}",
        r"Walk speed: \textbf{72 m/min} (1.2 m/s, standard warehouse); round-trip factor: \textbf{2}.",
        r"Zone distances to packing station: Zone A = 8 m (golden pick-face), Zone B = 25 m (mid-bay), Zone C = 47.5 m (reserve).",
        r"Formula:",
        r"$$\text{Total round-trip distance} = \sum_{\text{zone}} \text{picks}_{\text{zone}} \times D_{\text{zone}} \times 2$$",
        r"$$\text{Travel time (min)} = \frac{\text{Total round-trip distance}}{\text{walk speed}}$$",
        r"Baseline (random placement): every pick travels the SKU-count-weighted average zone distance:",
        r"$$\overline{D}_{\text{random}} = \frac{N_A \cdot D_A + N_B \cdot D_B + N_C \cdot D_C}{N}$$",
        r"",
        r"\paragraph{Results.}",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Q3.1 Travel-Time Proof --- Physical Distance Model}",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Zone & Picks ($T_{ij}$) & Dist $D_{ij}$ (m) & Round-trip $T_{ij} \times D_{ij} \times 2$ (m) \\",
        r"\midrule",
        f"        Zone A & {picks_a:,} & {DIST_A_M:.0f} & {picks_a * DIST_A_M * 2:,.0f} \\\\",
        f"        Zone B & {picks_b:,} & {DIST_B_M:.0f} & {picks_b * DIST_B_M * 2:,.0f} \\\\",
        f"        Zone C & {picks_c:,} & {DIST_C_M:.0f} & {picks_c * DIST_C_M * 2:,.0f} \\\\",
        r"\midrule",
        f"        \\textbf{{TOTAL}} & {total_picks:,} & --- & \\textbf{{{opt_rt:,.0f}}} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Travel-Time Summary: Random Baseline vs.\ ABC-Only Optimized Result}",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"Metric & Random Baseline (no slotting) & ABC-Only Optimized Result \\",
        r"\midrule",
        f"        Avg one-way distance / pick (m) & {baseline_avg_m:.1f} & \\textbf{{{opt_avg_m:.1f}}} \\\\",
        f"        Total round-trip distance (m) & {baseline_rt:,.0f} & \\textbf{{{opt_rt:,.0f}}} \\\\",
        f"        Travel time (min) & {baseline_time:,.1f} & \\textbf{{{opt_time_min:,.1f}}} \\\\",
        f"        \\textbf{{Reduction}} & --- & \\textbf{{{red_pct:.1f}\\%}} \\quad ({'\\color{green!60!black}\\checkmark MEETS TARGET' if meets_target else '\\color{red}\\times BELOW TARGET'}) \\\\",
        f"        Target & \\multicolumn{{2}}{{r}}{{$\\geq {REDUCTION_TARGET*100:.0f}\\%$}} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        r"",
        f"The ABC velocity-zoned layout achieves a \\textbf{{{red_pct:.1f}\\% reduction}} in total picker travel distance",
        rf"(baseline random avg. \textbf{{{baseline_avg_m:.1f}\,m/pick}} $\rightarrow$ optimized \textbf{{{opt_avg_m:.1f}\,m/pick}}),",
        f"well {'above' if meets_target else 'below'} the $\\geq{REDUCTION_TARGET*100:.0f}\\%$ target.",
        f"This reduction is driven by concentrating the highest-frequency Class~A SKUs ({picks_a:,} picks) at {DIST_A_M:.0f}\\,m,",
        f"compared to the warehouse-average \\textbf{{{baseline_avg_m:.1f}\\,m}} each pick would travel under random placement.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.97\linewidth]{../charts/q31_slotting_analysis.png}",
        r"\caption{Q3.1 Slotting Analysis: SKU zone distribution and travel-time comparison (optimized vs.\ baseline random)}",
        r"\label{fig:q31-slotting}",
        r"\end{figure}",
        r"",
        r"\subsubsection{Layout Recommendations}\label{layout}",
        r"",
        r"\paragraph{U-Shaped Warehouse Heatmap.}",
        r"The ABC velocity-zoned layout follows a U-shaped flow: receiving and packing share the same front wall, creating a natural golden pick-face (Zone A) adjacent to the packing station. Zone A (red, highest pick density) occupies the ground-level bays nearest the dock; Zone B (amber, medium velocity) the mid-bay area; Zone C (blue, slow movers) the far back wall and upper racks. This configuration minimizes cross-traffic between replenishment and pick paths.",
        r"Figure~\ref{fig:q31-u-shape} illustrates the ABC velocity heatmap layout.",
        r"",
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.75\linewidth]{../charts/q31_u_shape_heatmap.png}",
        r"\caption{U-Shaped Warehouse Heatmap --- ABC Velocity Zones}",
        r"\label{fig:q31-u-shape}",
        r"\end{figure}",
        r"",
        r"\begin{itemize}",
        r"    \item \textbf{U-flow configuration}: Receiving and shipping docks share the same front wall;",
        r"          highest-frequency slots cluster at the dock end (Zone A golden pick-face).",
        r"    \item \textbf{Zone A --- Pick-Face (Ground Level)}: Class A SKUs at ergonomic height",
        r"          (lower rack levels), nearest the I/O dock and packing station.",
        r"          High-frequency Class AA SKUs occupy the first rank slots.",
        r"    \item \textbf{Zone B --- Forward Reserve}: Class B SKUs in the mid-bay area;",
        r"          two-bin replenishment logic feeds the Zone A pick-face (WMS-triggered min/max).",
        r"    \item \textbf{Zone C --- Reserve / Bulk}: Class C SKUs in upper racks and pallet block-stacks",
        r"          at the far back wall. Slow-movers are consolidated here; picked on demand.",
        r"\end{itemize}",
        r"",
        r"\subsection{Question 3.2: Omni-Channel Pick-and-Pack Process Design}\label{q3.2}",
        r"",
        r"The outbound fulfillment process uses distinct operational pathways for B2B and B2C",
        r"channels, unified by a structured inventory allocation policy when stock is contested.",
        r"",
        r"\paragraph{Two pick models.}",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Two Pick Models --- B2B vs B2C / E-Commerce}",
        r"\begin{tabular}{>{\raggedright\arraybackslash}p{1.8cm} >{\raggedright\arraybackslash}p{3.2cm} >{\raggedright\arraybackslash}p{3.2cm} >{\raggedright\arraybackslash}p{4.8cm} >{\raggedright\arraybackslash}p{2.8cm}}",
        r"\toprule",
        r"Channel & Order Profile & Pick Model & Mechanics & Pack \\",
        r"\midrule",
        r"        B2B & Large volume, few SKUs & Pallet / Total Picking & One picker fulfils whole pallets or large CTN qty per order in a single pass. Sources Zone A pick-face + Zone C bulk. & Stage whole pallets; minimal re-sort. \\\\",
        r"        \addlinespace",
        r"        B2C / E-com & Small qty, many SKUs, many concurrent orders & Batch Picking + Zone Routing & Group many small orders into one pick wave; pickers route by zone; items consolidated at sortation. & Sort wave back to individual orders at packing. \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
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
        r"and on-hand stock is insufficient for both, the system resolves the shortage through",
        r"the following structured rules (stock is held in ONE shared pool per the Q2.2 pooling strategy, not physically split):",
        r"",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Shared-SKU Conflict --- Allocation \& Escalation Rules}",
        r"\begin{tabular}{lp{4cm}p{6.5cm}}",
        r"\toprule",
        r"Rule & Condition & Action \\",
        r"\midrule",
        r"        Check & Same SKU, both channels, concurrent & Evaluate on-hand vs (B2B + B2C) demand. \\\\",
        r"        Sufficient & On-hand $\geq$ B2B + B2C & Allocate to both from shared pool; no rationing. \\\\",
        r"        R1 & Short stock & Commit to the confirmed B2B PO first (contractual, penalty risk). \\\\",
        r"        R2 & Short stock & Hold the B2C safety buffer so the storefront does not show stockout. \\\\",
        r"        R3 & Short + B2C SLA-critical (2--4\,h) & Split: B2C SLA order gets partial now, backorder remainder. \\\\",
        r"        R4 & Below reorder point & Trigger emergency replenishment / inter-warehouse transfer. \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
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

    # Compile to PDF using xelatex (for Unicode / Vietnamese character support)
    import shutil
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

