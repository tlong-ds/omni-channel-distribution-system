from copy import copy
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from src.logage2026.config import Q11_WORKBOOK_OUTPUT


THIN_BORDER = Border(
    left=Side(style="thin", color="D9DEE5"),
    right=Side(style="thin", color="D9DEE5"),
    top=Side(style="thin", color="D9DEE5"),
    bottom=Side(style="thin", color="D9DEE5"),
)
TITLE_FILL = PatternFill("solid", fgColor="0F4C81")
SECTION_FILL = PatternFill("solid", fgColor="D9EAF7")
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
SUBHEADER_FILL = PatternFill("solid", fgColor="EAF2F8")
CLASS_FILLS = {
    "A": PatternFill("solid", fgColor="DDEBF7"),
    "B": PatternFill("solid", fgColor="FFF2CC"),
    "C": PatternFill("solid", fgColor="F4CCCC"),
    "X": PatternFill("solid", fgColor="D9EAD3"),
    "Y": PatternFill("solid", fgColor="FCE5CD"),
    "Z": PatternFill("solid", fgColor="F4CCCC"),
}
TITLE_FONT = Font(bold=True, color="FFFFFF", size=14)
SECTION_FONT = Font(bold=True, color="1F1F1F", size=11)
HEADER_FONT = Font(bold=True, color="FFFFFF")
BOLD_FONT = Font(bold=True)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)


def _write_dataframe_sheet(ws, title_text: str, df: pd.DataFrame) -> None:
    ws.column_dimensions[get_column_letter(1)].width = 3
    for col in range(2, len(df.columns) + 2):
        ws.column_dimensions[get_column_letter(col)].width = 18
    _apply_title(ws, "B1", len(df.columns) + 1, title_text)
    
    for col, value in enumerate(df.columns, start=2):
        ws.cell(2, col, str(value))
    _style_range(ws, 2, 2, len(df.columns) + 1, fill=HEADER_FILL, font=HEADER_FONT, alignment=CENTER)
    
    for row_idx, row in enumerate(df.itertuples(index=False), start=3):
        for col_idx, value in enumerate(row, start=2):
            cell = ws.cell(row_idx, col_idx, value)
            cell.border = THIN_BORDER
            cell.alignment = LEFT if isinstance(value, str) else CENTER
            if isinstance(value, float):
                cell.number_format = "0.00"
    
    ws.freeze_panes = "B3"
    ws.auto_filter.ref = f"B2:{get_column_letter(len(df.columns) + 1)}{len(df) + 2}"


def write_summary_workbook(
    abc_xyz: pd.DataFrame,
    abc_xyz_matrix: pd.DataFrame,
    monthly_demand: pd.DataFrame,
    q11_shipments: pd.DataFrame,
    warehouse_region_summary: pd.DataFrame,
    q12_top_demand_provinces_summary: pd.DataFrame,
    warehouse_imbalance_summary: pd.DataFrame,
    q13_segment_profile_summary: pd.DataFrame,
    q13_segment_packaging_summary: pd.DataFrame,
    q13_segment_geographic_spread_summary: pd.DataFrame,
    safety_stock_class_a: pd.DataFrame,
    lead_time_sensitivity: pd.DataFrame,
    inventory_pooling_summary: pd.DataFrame,
    hcm_district_summary: pd.DataFrame,
    output_path: Path,
) -> Path:
    workbook = Workbook()
    dashboard = workbook.active
    dashboard.title = "Q1.1 Dashboard"
    _write_dashboard(dashboard, abc_xyz, abc_xyz_matrix, q11_shipments)
    _write_full_sku_ranking(workbook.create_sheet("Q1.1 Full SKU Ranking"), abc_xyz)
    _write_monthly_demand_sheet(workbook.create_sheet("Q1.1 Monthly Demand"), monthly_demand)
    _write_class_a_deep_dive(workbook.create_sheet("Q1.1 Class A Deep Dive"), monthly_demand)
    
    _write_dataframe_sheet(workbook.create_sheet("Q1.2 Warehouse by Region"), "QUESTION 1.2 — WAREHOUSE REGION SUMMARY", warehouse_region_summary)
    _write_dataframe_sheet(workbook.create_sheet("Q1.2 Top Provinces"), "QUESTION 1.2 — TOP DEMAND PROVINCES", q12_top_demand_provinces_summary)
    _write_dataframe_sheet(workbook.create_sheet("Q1.2 Warehouse Imbalance"), "QUESTION 1.2 — WAREHOUSE IMBALANCE", warehouse_imbalance_summary)
    
    _write_dataframe_sheet(workbook.create_sheet("Q1.3 Segment Profile"), "QUESTION 1.3 — ORDER PROFILE BY SEGMENT", q13_segment_profile_summary)
    _write_dataframe_sheet(workbook.create_sheet("Q1.3 Packaging"), "QUESTION 1.3 — PACKAGING SPREAD BY SEGMENT", q13_segment_packaging_summary)
    _write_dataframe_sheet(workbook.create_sheet("Q1.3 Geo Spread"), "QUESTION 1.3 — GEOGRAPHIC SPREAD BY SEGMENT", q13_segment_geographic_spread_summary)
    
    _write_dataframe_sheet(workbook.create_sheet("Q2.2 Safety Stock"), "QUESTION 2.2 — CLASS A SAFETY STOCK", safety_stock_class_a)
    _write_dataframe_sheet(workbook.create_sheet("Q2.2 Lead Time Sensitivity"), "QUESTION 2.2 — LEAD TIME SENSITIVITY", lead_time_sensitivity)
    _write_dataframe_sheet(workbook.create_sheet("Q2.2 Inventory Pooling"), "QUESTION 2.2 — INVENTORY POOLING SUMMARY", inventory_pooling_summary)
    _write_dataframe_sheet(workbook.create_sheet("Q2.1 HCM Districts"), "QUESTION 2.1 — HCM DISTRICT SUMMARY", hcm_district_summary)
            
    workbook.save(output_path)
    return output_path


def _apply_title(ws, start_cell: str, end_col: int, text: str) -> None:
    row = ws[start_cell].row
    start_col = ws[start_cell].column
    ws.merge_cells(start_row=row, start_column=start_col, end_row=row, end_column=end_col)
    cell = ws[start_cell]
    cell.value = text
    cell.fill = TITLE_FILL
    cell.font = TITLE_FONT
    cell.alignment = LEFT


def _style_range(ws, row: int, start_col: int, end_col: int, *, fill=None, font=None, alignment=None) -> None:
    for col in range(start_col, end_col + 1):
        cell = ws.cell(row, col)
        cell.border = THIN_BORDER
        if fill is not None:
            cell.fill = fill
        if font is not None:
            cell.font = copy(font)
        if alignment is not None:
            cell.alignment = alignment


def _format_share(value: float) -> str:
    return f"{value:.1%}"


def _safe_float(value: object) -> float:
    return 0.0 if pd.isna(value) else float(value)


def _period_label(start: pd.Timestamp, end: pd.Timestamp) -> str:
    if start.year == end.year:
        return f"{start.strftime('%b')}–{end.strftime('%b %Y')}"
    return f"{start.strftime('%b %Y')}–{end.strftime('%b %Y')}"


def _month_columns(monthly_demand: pd.DataFrame) -> list[str]:
    month_like = []
    for column in monthly_demand.columns:
        if column in {"sku_code", "product_name", "category", "abc_quantity", "xyz", "abc_xyz", "Total", "Mean/Mo", "Std Dev", "CV", "quantity", "quantity_share", "order_frequency", "frequency_share", "cbm_total"}:
            continue
        try:
            pd.Period(column, freq="M")
            month_like.append(column)
        except Exception:
            continue
    return month_like


def _operational_category(abc_xyz_code: str) -> str:
    mapping = {
        "AX": "Fast & Predictable",
        "AY": "Fast & Predictable",
        "AZ": "Fast & Volatile",
        "BX": "Medium & Stable",
        "BY": "Medium & Seasonal",
        "BZ": "Medium & Volatile",
        "CX": "Slow & Stable",
        "CY": "Slow & Seasonal",
        "CZ": "Slow & Erratic",
    }
    return mapping.get(abc_xyz_code, "Unclassified")


def _slotting_zone(abc_class: str) -> str:
    if abc_class == "A":
        return "Pick-Face Zone (Ground Level)"
    if abc_class == "B":
        return "Forward Reserve Zone"
    return "Reserve / Bulk Zone"


def _demand_pattern(xyz_class: str) -> str:
    return {"X": "Stable", "Y": "Seasonal", "Z": "Erratic"}.get(xyz_class, "Unknown")


def _stock_strategy(xyz_class: str) -> str:
    return {
        "X": "Fixed ROP + EOQ",
        "Y": "Dynamic MRP + safety stock",
        "Z": "Buffer stock + safety stock",
    }.get(xyz_class, "Manual review")


def _reorder_logic(xyz_class: str) -> str:
    return {"X": "Min-Max fixed", "Y": "Weekly forecast", "Z": "Safety stock + review"}.get(xyz_class, "Manual review")


def _dashboard_abc_summary(abc_xyz: pd.DataFrame) -> pd.DataFrame:
    summary = (
        abc_xyz.groupby("abc_quantity", dropna=False)
        .agg(sku_count=("sku_code", "nunique"), total_qty=("quantity", "sum"), total_cbm=("cbm_total", "sum"))
        .reset_index()
    )
    summary["sku_share"] = summary["sku_count"] / abc_xyz["sku_code"].nunique()
    summary["qty_share"] = summary["total_qty"] / abc_xyz["quantity"].sum()
    return summary.set_index("abc_quantity").reindex(["A", "B", "C"]).reset_index()


def _dashboard_xyz_frequency_summary(abc_xyz: pd.DataFrame) -> pd.DataFrame:
    summary = (
        abc_xyz.groupby("xyz_frequency", dropna=False)
        .agg(sku_count=("sku_code", "nunique"), total_freq=("order_frequency", "sum"))
        .reset_index()
    )
    summary["sku_share"] = summary["sku_count"] / abc_xyz["sku_code"].nunique()
    return summary.set_index("xyz_frequency").reindex(["X", "Y", "Z"]).reset_index()

def _dashboard_xyz_volatility_summary(abc_xyz: pd.DataFrame) -> pd.DataFrame:
    summary = (
        abc_xyz.groupby("xyz_volatility", dropna=False)
        .agg(sku_count=("sku_code", "nunique"), avg_cv=("demand_cv", "mean"))
        .reset_index()
    )
    summary["sku_share"] = summary["sku_count"] / abc_xyz["sku_code"].nunique()
    return summary.set_index("xyz_volatility").reindex(["X", "Y", "Z"]).reset_index()


def _write_dashboard(
    ws,
    abc_xyz: pd.DataFrame,
    abc_xyz_matrix: pd.DataFrame,
    q11_shipments: pd.DataFrame,
) -> None:
    period_start = q11_shipments["created_date"].min()
    period_end = q11_shipments["created_date"].max()
    month_count = q11_shipments["created_date"].dt.to_period("M").nunique()
    for idx, width in enumerate([3, 18, 14, 12, 16, 14, 12, 24, 40], start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    _apply_title(ws, "B1", 9, "LOGage 2026 — QUESTION 1.1 | ABC-XYZ ANALYSIS DASHBOARD")
    period_text = (
        f"Data: My Phuoc & Vinh Loc Warehouses  |  Period: {_period_label(period_start, period_end)}  |  "
        f"{len(q11_shipments):,} transaction lines  |  {abc_xyz['sku_code'].nunique():,} unique SKUs"
    )
    ws.merge_cells("B2:I2")
    ws["B2"] = period_text
    ws["B2"].alignment = LEFT
    ws["B2"].font = Font(italic=True, color="5B5B5B")

    r = 4
    abc_summary = _dashboard_abc_summary(abc_xyz)
    ws.merge_cells(f"B{r}:I{r}")
    ws[f"B{r}"] = "A.  ABC CLASSIFICATION — OUTBOUND QUANTITY (threshold: A=70%, B=90%, C=100%)"
    _style_range(ws, r, 2, 9, fill=SECTION_FILL, font=SECTION_FONT, alignment=LEFT)
    r += 1
    headers = ["Class", "SKU Count", "% of SKUs", "Total Qty (pcs)", "% of Total Qty", "Total CBM", "Threshold", "Action"]
    for col, value in enumerate(headers, start=2):
        ws.cell(r, col, value)
    _style_range(ws, r, 2, 9, fill=HEADER_FILL, font=HEADER_FONT, alignment=CENTER)
    r += 1
    thresholds = {"A": "Cum. top 70% volume", "B": "70-90% cum. volume", "C": "Bottom 10% volume"}
    actions = {
        "A": "Pick-face zone | Daily cycle count | Min lead time",
        "B": "Intermediate zone | Weekly review",
        "C": "Reserve/bulk zone | Monthly review",
    }
    for row in abc_summary.itertuples(index=False):
        values = [row.abc_quantity, int(row.sku_count), _format_share(row.sku_share), round(_safe_float(row.total_qty)), _format_share(row.qty_share), round(_safe_float(row.total_cbm)), thresholds[row.abc_quantity], actions[row.abc_quantity]]
        for col, value in enumerate(values, start=2):
            ws.cell(r, col, value)
        _style_range(ws, r, 2, 9, fill=CLASS_FILLS[row.abc_quantity], alignment=LEFT)
        r += 1

    r += 1
    xyz_freq_summary = _dashboard_xyz_frequency_summary(abc_xyz)
    ws.merge_cells(f"B{r}:I{r}")
    ws[f"B{r}"] = "B.  XYZ CLASSIFICATION — ORDER FREQUENCY"
    _style_range(ws, r, 2, 9, fill=SECTION_FILL, font=SECTION_FONT, alignment=LEFT)
    r += 1
    xyz_headers = ["Class", "SKU Count", "% of SKUs", "Order Frequency", "Demand Pattern", "Replenishment Logic", "Safety Stock", ""]
    for col, value in enumerate(xyz_headers, start=2):
        ws.cell(r, col, value)
    _style_range(ws, r, 2, 9, fill=HEADER_FILL, font=HEADER_FONT, alignment=CENTER)
    r += 1
    demand = {"X": "High Frequency", "Y": "Medium Frequency", "Z": "Low Frequency"}
    repl = {"X": "Fixed reorder point (ROP)", "Y": "Dynamic MRP/forecast-based", "Z": "Demand-driven + buffer stock"}
    safety = {"X": "Low — 1-2 weeks cover", "Y": "Medium — 2-4 weeks cover", "Z": "High — 4-8 weeks cover"}
    for row in xyz_freq_summary.itertuples(index=False):
        cls = getattr(row, "xyz_frequency")
        values = [cls, int(row.sku_count), _format_share(row.sku_share), round(_safe_float(row.total_freq)), demand[cls], repl[cls], safety[cls], ""]
        for col, value in enumerate(values, start=2):
            ws.cell(r, col, value)
        _style_range(ws, r, 2, 9, fill=CLASS_FILLS[cls], alignment=LEFT)
        r += 1

    r += 1
    ws.merge_cells(f"B{r}:I{r}")
    ws[f"B{r}"] = "C.  COMBINED ABC-XYZ MATRIX — FREQUENCY"
    _style_range(ws, r, 2, 9, fill=SECTION_FILL, font=SECTION_FONT, alignment=LEFT)
    r += 1
    
    # We need to compute matrix for frequency
    matrix_freq = (
        abc_xyz.groupby(["abc_quantity", "xyz_frequency"]).size().unstack(fill_value=0)
        .reindex(index=["A", "B", "C"], columns=["X", "Y", "Z"])
        .fillna(0)
        .astype(int)
    )
    headers = ["", "X (High Freq)", "Y (Med Freq)", "Z (Low Freq)", "Row Total", "% Volume", "% Freq", "Key Implication"]
    for col, value in enumerate(headers, start=2):
        ws.cell(r, col, value)
    _style_range(ws, r, 2, 9, fill=HEADER_FILL, font=HEADER_FONT, alignment=CENTER)
    r += 1
    volume_share = abc_xyz.groupby("abc_quantity")["quantity"].sum() / abc_xyz["quantity"].sum()
    freq_share = abc_xyz.groupby("abc_quantity")["order_frequency"].sum() / abc_xyz["order_frequency"].sum()
    implications = {
        "A": "HIGH PRESSURE — Daily ops, premium slots, SLA-critical",
        "B": "MODERATE — Standard fulfillment, replenishment planning",
        "C": "LOW PRIORITY — Bulk storage, periodic review",
    }
    for abc_class in ["A", "B", "C"]:
        values = [abc_class, int(matrix_freq.loc[abc_class, "X"]), int(matrix_freq.loc[abc_class, "Y"]), int(matrix_freq.loc[abc_class, "Z"]), int(matrix_freq.loc[abc_class].sum()), _format_share(_safe_float(volume_share.get(abc_class))), _format_share(_safe_float(freq_share.get(abc_class))), implications[abc_class]]
        for col, value in enumerate(values, start=2):
            ws.cell(r, col, value)
        _style_range(ws, r, 2, 9, fill=CLASS_FILLS[abc_class], alignment=LEFT)
        r += 1
    total_values = ["TOTAL", int(matrix_freq["X"].sum()), int(matrix_freq["Y"].sum()), int(matrix_freq["Z"].sum()), int(matrix_freq.values.sum()), "", "", ""]
    for col, value in enumerate(total_values, start=2):
        ws.cell(r, col, value)
    _style_range(ws, r, 2, 9, fill=SUBHEADER_FILL, font=BOLD_FONT, alignment=CENTER)
    r += 1

    r += 1
    xyz_vol_summary = _dashboard_xyz_volatility_summary(abc_xyz)
    ws.merge_cells(f"B{r}:I{r}")
    ws[f"B{r}"] = f"D.  XYZ CLASSIFICATION — DEMAND VARIABILITY (Coefficient of Variation over {month_count} months)"
    _style_range(ws, r, 2, 9, fill=SECTION_FILL, font=SECTION_FONT, alignment=LEFT)
    r += 1
    xyz_headers = ["Class", "SKU Count", "% of SKUs", "CV Range", "Avg CV", "Demand Pattern", "Replenishment Logic", "Safety Stock"]
    for col, value in enumerate(xyz_headers, start=2):
        ws.cell(r, col, value)
    _style_range(ws, r, 2, 9, fill=HEADER_FILL, font=HEADER_FONT, alignment=CENTER)
    r += 1
    cv_ranges = {"X": "CV <= 0.50", "Y": "0.50 < CV <= 1.00", "Z": "CV > 1.00"}
    demand = {"X": "Stable / consistent", "Y": "Seasonal or trend", "Z": "Erratic / unpredictable"}
    for row in xyz_vol_summary.itertuples(index=False):
        cls = getattr(row, "xyz_volatility")
        values = [cls, int(row.sku_count), _format_share(row.sku_share), cv_ranges[cls], round(_safe_float(row.avg_cv), 2), demand[cls], repl[cls], safety[cls]]
        for col, value in enumerate(values, start=2):
            ws.cell(r, col, value)
        _style_range(ws, r, 2, 9, fill=CLASS_FILLS[cls], alignment=LEFT)
        r += 1

    r += 1
    ws.merge_cells(f"B{r}:I{r}")
    ws[f"B{r}"] = "E.  COMBINED ABC-XYZ MATRIX — VOLATILITY"
    _style_range(ws, r, 2, 9, fill=SECTION_FILL, font=SECTION_FONT, alignment=LEFT)
    r += 1
    
    matrix_vol = (
        abc_xyz.groupby(["abc_quantity", "xyz_volatility"]).size().unstack(fill_value=0)
        .reindex(index=["A", "B", "C"], columns=["X", "Y", "Z"])
        .fillna(0)
        .astype(int)
    )
    headers = ["", "X (Stable)", "Y (Seasonal)", "Z (Erratic)", "Row Total", "% Volume", "% Freq", "Key Implication"]
    for col, value in enumerate(headers, start=2):
        ws.cell(r, col, value)
    _style_range(ws, r, 2, 9, fill=HEADER_FILL, font=HEADER_FONT, alignment=CENTER)
    r += 1
    for abc_class in ["A", "B", "C"]:
        values = [abc_class, int(matrix_vol.loc[abc_class, "X"]), int(matrix_vol.loc[abc_class, "Y"]), int(matrix_vol.loc[abc_class, "Z"]), int(matrix_vol.loc[abc_class].sum()), _format_share(_safe_float(volume_share.get(abc_class))), _format_share(_safe_float(freq_share.get(abc_class))), implications[abc_class]]
        for col, value in enumerate(values, start=2):
            ws.cell(r, col, value)
        _style_range(ws, r, 2, 9, fill=CLASS_FILLS[abc_class], alignment=LEFT)
        r += 1
    total_values = ["TOTAL", int(matrix_vol["X"].sum()), int(matrix_vol["Y"].sum()), int(matrix_vol["Z"].sum()), int(matrix_vol.values.sum()), "", "", ""]
    for col, value in enumerate(total_values, start=2):
        ws.cell(r, col, value)
    _style_range(ws, r, 2, 9, fill=SUBHEADER_FILL, font=BOLD_FONT, alignment=CENTER)
    r += 1

    r += 1
    class_a = abc_xyz[abc_xyz["abc_quantity"].eq("A")].copy()
    ws.merge_cells(f"B{r}:I{r}")
    ws[f"B{r}"] = "F.  FAST-MOVING SKU GROUP (Class A) — Primary Source of Warehouse Operational Pressure"
    _style_range(ws, r, 2, 9, fill=SECTION_FILL, font=SECTION_FONT, alignment=LEFT)
    r += 1
    headers = ["Metric", "AX — Stable Fast", "AY — Seasonal Fast", "AZ — Volatile Fast", "ALL Class A Total", "% of Grand Total", "Operational Priority"]
    for col, value in enumerate(headers, start=2):
        ws.cell(r, col, value)
    _style_range(ws, r, 2, 8, fill=HEADER_FILL, font=HEADER_FONT, alignment=CENTER)
    r += 1
    subgroup_values = {}
    for subgroup in ["AX", "AY", "AZ"]:
        subset = class_a[class_a["abc_xyz_frequency"].eq(subgroup)]
        subgroup_values[subgroup] = {
            "sku_count": int(subset["sku_code"].nunique()),
            "quantity": subset["quantity"].sum(),
            "order_frequency": subset["order_frequency"].sum(),
            "avg_cv": subset["demand_cv"].mean(),
            "cbm_total": subset["cbm_total"].sum(),
        }
    metrics = [
        ("SKU Count", "sku_count", f"{_format_share(class_a['sku_code'].nunique() / abc_xyz['sku_code'].nunique())} of all SKUs", "Fast-moving concentration remains high"),
        ("Total Qty (pcs)", "quantity", f"{_format_share(class_a['quantity'].sum() / abc_xyz['quantity'].sum())} of total volume", "Prioritize in pick-face zone"),
        ("Order Frequency", "order_frequency", f"{_format_share(class_a['order_frequency'].sum() / abc_xyz['order_frequency'].sum())} of orders", "High pick frequency -> batch picking"),
        ("Avg Monthly Demand", None, "-", f"{month_count}-month average"),
        ("Avg CV (Variability)", "avg_cv", "-", "High safety stock needed"),
        ("Total CBM", "cbm_total", f"{_format_share(class_a['cbm_total'].sum() / abc_xyz['cbm_total'].sum())} of total CBM", "Slotting space priority"),
    ]
    for metric, key, pct_text, priority_text in metrics:
        ws.cell(r, 2, metric)
        for col_idx, subgroup in enumerate(["AX", "AY", "AZ"], start=3):
            value = subgroup_values[subgroup].get(key) if key else "-"
            if key in {"quantity", "order_frequency", "cbm_total"}:
                value = f"{round(_safe_float(value)):,}"
            elif key == "avg_cv":
                value = f"{_safe_float(value):.2f}"
            elif key == "sku_count":
                value = str(value)
            ws.cell(r, col_idx, value)
        total_value = "-"
        if key == "sku_count":
            total_value = str(int(class_a["sku_code"].nunique()))
        elif key == "quantity":
            total_value = f"{round(class_a['quantity'].sum()):,}"
        elif key == "order_frequency":
            total_value = f"{round(class_a['order_frequency'].sum()):,}"
        elif key == "avg_cv":
            total_value = f"{class_a['demand_cv'].mean():.2f}"
        elif key == "cbm_total":
            total_value = f"{round(class_a['cbm_total'].sum()):,}"
        elif metric == "Avg Monthly Demand":
            total_value = f"{round(class_a['quantity'].sum() / month_count):,}"
        ws.cell(r, 6, total_value)
        ws.cell(r, 7, pct_text)
        ws.cell(r, 8, priority_text)
        _style_range(ws, r, 2, 8, fill=SUBHEADER_FILL if r % 2 == 0 else None, alignment=LEFT)
        r += 1

    predictable = int(class_a["abc_xyz_frequency"].isin(["AX", "AY"]).sum())
    volatile = int(class_a["abc_xyz_frequency"].eq("AZ").sum())
    key_finding = (
        f"KEY FINDING: {int(class_a['sku_code'].nunique())} Class A SKUs "
        f"({_format_share(class_a['sku_code'].nunique() / abc_xyz['sku_code'].nunique())} of portfolio) account for "
        f"{_format_share(class_a['quantity'].sum() / abc_xyz['quantity'].sum())} of outbound volume and "
        f"{_format_share(class_a['order_frequency'].sum() / abc_xyz['order_frequency'].sum())} of order frequency. "
        f"Of these, {predictable} SKUs (AX+AY) are predictable enough for fixed slotting and ROP-based replenishment. "
        f"The {volatile} AZ SKUs require demand buffering and escalation protocols."
    )
    ws.merge_cells(f"B{r}:I{r}")
    ws[f"B{r}"] = key_finding
    _style_range(ws, r, 2, 9, fill=TITLE_FILL, font=Font(bold=True, color="FFFFFF"), alignment=LEFT)
    r += 1

def _write_full_sku_ranking(ws, abc_xyz: pd.DataFrame) -> None:
    widths = [3, 10, 14, 15, 10, 11, 10, 10, 10, 10, 11, 10, 12, 10, 8, 10, 22, 28]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    _apply_title(
        ws,
        "B1",
        18,
        f"FULL SKU RANKING TABLE — ABC-XYZ CLASSIFICATION ({abc_xyz['sku_code'].nunique():,} SKUs | Jun\u2013Dec 2025)",
    )
    headers = [
        "Rank\n(Qty)",
        "SKU Code",
        "Total Qty\n(pcs)",
        "% Qty",
        "Cum %\nQty",
        "ABC\n(Qty)",
        "Rank\n(Freq)",
        "Order\nFreq",
        "% Freq",
        "Cum Freq Share",
        "Total CBM",
        "CV",
        "XYZ\n(Freq)",
        "ABC-XYZ\n(Freq)",
        "XYZ\n(Vol)",
        "ABC-XYZ\n(Vol)",
        "Operational Category",
        "Slotting Zone",
    ]
    for col, value in enumerate(headers, start=2):
        ws.cell(2, col, value)
    _style_range(ws, 2, 2, 17, fill=HEADER_FILL, font=HEADER_FONT, alignment=CENTER)

    qty_sorted = abc_xyz.sort_values(["quantity", "sku_code"], ascending=[False, True]).reset_index(drop=True)
    qty_rank = {sku: idx for idx, sku in enumerate(qty_sorted["sku_code"], start=1)}
    freq_sorted = abc_xyz.sort_values(["order_frequency", "sku_code"], ascending=[False, True]).reset_index(drop=True)
    freq_rank = {sku: idx for idx, sku in enumerate(freq_sorted["sku_code"], start=1)}

    for row_idx, row in enumerate(qty_sorted.itertuples(index=False), start=3):
        values = [
            qty_rank[row.sku_code],
            row.sku_code,
            _safe_float(row.quantity),
            _safe_float(row.quantity_share),
            _safe_float(row.quantity_cumulative_share),
            row.abc_quantity,
            freq_rank[row.sku_code],
            _safe_float(row.order_frequency),
            _safe_float(row.frequency_share),
            _safe_float(row.frequency_cumulative_share),
            _safe_float(row.cbm_total),
            _safe_float(row.demand_cv),
            row.xyz_frequency,
            row.abc_xyz_frequency,
            row.xyz_volatility,
            row.abc_xyz_volatility,
            _operational_category(row.abc_xyz_frequency),
            _slotting_zone(row.abc_quantity),
        ]
        for col, value in enumerate(values, start=2):
            ws.cell(row_idx, col, value)
        _style_range(ws, row_idx, 2, 17, fill=CLASS_FILLS.get(row.abc_quantity), alignment=CENTER)
        ws.cell(row_idx, 3).alignment = LEFT
        ws.cell(row_idx, 16).alignment = LEFT
        ws.cell(row_idx, 17).alignment = LEFT
        ws.cell(row_idx, 5).number_format = "0.00%"
        ws.cell(row_idx, 6).number_format = "0.0%"
        ws.cell(row_idx, 10).number_format = "0.00%"
        ws.cell(row_idx, 11).number_format = "0.0%"
        ws.cell(row_idx, 13).number_format = "0.000"
    ws.freeze_panes = "B3"
    ws.auto_filter.ref = f"B2:Q{ws.max_row}"


def _write_monthly_demand_sheet(ws, monthly_demand: pd.DataFrame) -> None:
    ab = monthly_demand[monthly_demand["abc_quantity"].isin(["A", "B"])].copy()
    month_columns = _month_columns(monthly_demand)
    widths = [3, 14, 8, 8] + [11] * len(month_columns) + [12, 11, 11, 8, 10]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    _apply_title(ws, "B1", 6 + len(month_columns) + 4, "MONTHLY DEMAND TABLE — A & B CLASS SKUs (XYZ Calculation Base)")
    headers = ["SKU Code", "ABC", "XYZ (Freq)", "ABC-XYZ (Freq)", "XYZ (Vol)", "ABC-XYZ (Vol)", *month_columns, "Total", "Mean/Mo", "Std Dev", "CV"]
    for col, value in enumerate(headers, start=2):
        ws.cell(2, col, value)
    _style_range(ws, 2, 2, 1 + len(headers), fill=HEADER_FILL, font=HEADER_FONT, alignment=CENTER)
    for row_idx, (_, row) in enumerate(ab.iterrows(), start=3):
        values = [
            row["sku_code"],
            row["abc_quantity"],
            row["xyz_frequency"],
            row["abc_xyz_frequency"],
            row["xyz_volatility"],
            row["abc_xyz_volatility"],
            *[row[column] for column in month_columns],
            row["Total"],
            row["Mean/Mo"],
            row["Std Dev"],
            row["CV"],
        ]
        for col, value in enumerate(values, start=2):
            ws.cell(row_idx, col, value)
        _style_range(ws, row_idx, 2, 1 + len(headers), fill=CLASS_FILLS.get(row["abc_quantity"]), alignment=CENTER)
        ws.cell(row_idx, 2).alignment = LEFT
        total_col = 2 + 6 + len(month_columns)
        mean_col = total_col + 1
        std_col = total_col + 2
        cv_col = total_col + 3
        ws.cell(row_idx, mean_col).number_format = "0.0"
        ws.cell(row_idx, std_col).number_format = "0.0"
        ws.cell(row_idx, cv_col).number_format = "0.000"
    ws.freeze_panes = "B3"
    ws.auto_filter.ref = f"B2:{get_column_letter(1 + len(headers))}{ws.max_row}"


def _write_class_a_deep_dive(ws, monthly_demand: pd.DataFrame) -> None:
    class_a = monthly_demand[monthly_demand["abc_quantity"].eq("A")].copy().sort_values("quantity", ascending=False)
    widths = [3, 8, 14, 12, 12, 12, 12, 12, 12, 12, 10, 14, 22, 20, 18]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    _apply_title(
        ws,
        "B1",
        15,
        f"CLASS A SKUs — FAST-MOVING DEEP DIVE ({len(class_a):,} SKUs | {_format_share(class_a['quantity'].sum() / monthly_demand['quantity'].sum())} of Volume)",
    )
    ws.merge_cells("B2:O2")
    ws["B2"] = (
        "These SKUs create the highest operational pressure: prioritize pick-face slotting, cycle counting, "
        "and safety stock buffering for AZ subgroup."
    )
    ws["B2"].alignment = LEFT
    ws["B2"].font = Font(italic=True, color="5B5B5B")
    headers = [
        "Rank",
        "SKU Code",
        "ABC-XYZ\n(Freq)",
        "ABC-XYZ\n(Vol)",
        "Total Qty\n(pcs)",
        "% of Total\nQty",
        "Order\nFrequency",
        "% of Total\nFreq",
        "Total CBM",
        "Avg Monthly\nDemand",
        "CV",
        "Demand\nPattern",
        "Stock\nStrategy",
        "Slotting\nPriority",
        "Reorder\nLogic",
    ]
    for col, value in enumerate(headers, start=2):
        ws.cell(3, col, value)
    _style_range(ws, 3, 2, 15, fill=HEADER_FILL, font=HEADER_FONT, alignment=CENTER)
    total_qty = monthly_demand["quantity"].sum()
    total_freq = monthly_demand["order_frequency"].sum()
    for row_idx, (_, row) in enumerate(class_a.iterrows(), start=4):
        values = [
            row_idx - 3,
            row["sku_code"],
            row["abc_xyz_frequency"],
            row["abc_xyz_volatility"],
            _safe_float(row["quantity"]),
            _safe_float(row["quantity"]) / total_qty if total_qty else 0.0,
            _safe_float(row["order_frequency"]),
            _safe_float(row["order_frequency"]) / total_freq if total_freq else 0.0,
            _safe_float(row["cbm_total"]),
            _safe_float(row["Mean/Mo"]),
            _safe_float(row["CV"]),
            _demand_pattern(row["xyz_volatility"]),
            _stock_strategy(row["xyz_volatility"]),
            "Ground Level - Zone 1",
            _reorder_logic(row["xyz_frequency"]),
        ]
        for col, value in enumerate(values, start=2):
            ws.cell(row_idx, col, value)
        _style_range(ws, row_idx, 2, 15, fill=CLASS_FILLS.get(row["xyz_frequency"]), alignment=CENTER)
        ws.cell(row_idx, 3).alignment = LEFT
        ws.cell(row_idx, 6).number_format = "0.00%"
        ws.cell(row_idx, 8).number_format = "0.00%"
        ws.cell(row_idx, 10).number_format = "0.0"
        ws.cell(row_idx, 11).number_format = "0.000"
        ws.cell(row_idx, 12).alignment = LEFT
        ws.cell(row_idx, 13).alignment = LEFT
        ws.cell(row_idx, 14).alignment = LEFT
        ws.cell(row_idx, 15).alignment = LEFT
    ws.freeze_panes = "B4"
    ws.auto_filter.ref = f"B3:O{ws.max_row}"
