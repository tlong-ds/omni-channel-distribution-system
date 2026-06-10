"""Build the 8-slide LOGage 2026 Round 2 presentation from template."""
import shutil
import re
import os
from pathlib import Path
from lxml import etree

UNPACKED = Path("unpacked")
SLIDES_DIR = UNPACKED / "ppt" / "slides"
RELS_DIR = SLIDES_DIR / "_rels"
MEDIA_DIR = UNPACKED / "ppt" / "media"
PRES_XML = UNPACKED / "ppt" / "presentation.xml"
PRES_RELS = UNPACKED / "ppt" / "_rels" / "presentation.xml.rels"
CONTENT_TYPES = UNPACKED / "[Content_Types].xml"
CHARTS_DIR = Path("outputs/charts")

# Tab data: (new_name, textbox_id, original_xml_position_data)
TABS = [
    ("ABC-XYZ Analysis", 9, "x:0 y:74332 w:2579097"),
    ("Distribution Heatmap", 10, "x:2036732 y:65512 w:4986612"),
    ("Order Profiling", 11, "x:6352096 y:65512 w:2398777"),
    ("Network Design", 12, "x:9252261 y:74332 w:2446219"),
    ("Inventory Optimization", 13, "x:12485773 y:65512 w:2351335"),
    ("Warehouse Operations", 14, "x:14656133 y:65512 w:3995364"),
]

# For each slide: which tab is active (0-indexed), title, content description
SLIDES = [
    {  # Slide 1 - Cover
        "active_tab": None,
        "title": "LOGage 2026",
        "subtitle": "Omni-Channel Distribution System Optimization — Round 2",
        "description": "Network Profiling · Fulfillment Strategy · Warehouse Operations",
        "chart": None,
        "background_title": True,
    },
    {  # Slide 2 - ABC-XYZ Analysis
        "active_tab": 0,
        "title": "Q1.1 — ABC-XYZ Analysis: 19 Class AA SKUs Drive 57.9% of Volume",
        "bullets": [
            ("19 Fast-Moving SKUs", "Class AA: 57.9% volume, 25.9% order frequency"),
            ("Top SKU 4200009163", "163,014 units, 5,381 orders — highest operational pressure"),
            ("Classification", "Volume A ≥70%, Volume B ≥90%; Frequency A = top frequency class"),
            ("Fast-Moving Group", "Creates highest warehouse fulfillment pressure — prioritize slotting"),
        ],
        "charts": ["q11_abc_xyz_matrix_frequency.png", "q11_abc_xyz_matrix_volatility.png"],
        "chart_caption": "ABC-XYZ Matrix: Frequency and Volatility classifications — AA cluster highlighted",
    },
    {  # Slide 3 - Distribution Heatmap
        "active_tab": 1,
        "title": "Q1.2 — Severe Geographic Imbalance: My Phuoc Ships 92% of HCMC Volume",
        "bullets": [
            ("HCMC Top Province", "65,527 units — 23.7% of total outbound volume"),
            ("Binh Duong", "43,012 units, #2 province — near My Phuoc RDC"),
            ("Warehouse Imbalance", "My Phuoc dominates all regions; Vinh Loc only leads in Bắc Ninh"),
            ("Key Gap", "Vinh Loc (in HCMC) ships only 8% of HCMC volume — severe underutilization"),
        ],
        "charts": ["q12_province_demand_choropleths.png"],
        "chart_caption": "Province demand choropleth map and warehouse dominance visualization",
    },
    {  # Slide 4 - Order Profiling
        "active_tab": 2,
        "title": "Q1.3 — Modern Trade vs Traditional Trade: Two Distinct Fulfillment Profiles",
        "bullets": [
            ("Modern Trade", "80.2 units/order, 75% pallet, 2.8 SKUs/order — bulk B2B"),
            ("Traditional Trade", "41.3 units/order, 49% carton, 4.3 SKUs/order — fragmented B2B/B2C"),
            ("Lead Time Sensitivity", "Modern Trade: High (4,948 SS); Traditional: Low (3,963 SS)"),
            ("Geographic Spread", "Modern: 34 provinces; Traditional: 60 provinces — wider network"),
        ],
        "charts": ["q13_order_profile_comparison.png", "q13_packaging_mix.png"],
        "chart_caption": "Order profile comparison (left) and packaging unit mix (right)",
    },
    {  # Slide 5 - Network Evaluation
        "active_tab": 3,
        "title": "Q2.1 — Current Two-RDC Model Fails B2C 2hr SLA for 85% of HCMC Districts",
        "bullets": [
            ("Baseline Service", "105–156 minutes (pick 30 + pack 30 + dispatch 30 + drive)"),
            ("SLA Compliance", "Only 3/19 districts meet 2hr SLA: Bình Tân, Tân Phú, Bình Chánh"),
            ("Strengths", "Good B2B coverage; My Phuoc well-positioned for industrial zones"),
            ("Limitations", "Vinh Loc too far from HCMC core; no urban fulfillment nodes"),
        ],
        "charts": ["q21_network_coverage.png"],
        "chart_caption": "Network coverage map showing existing RDC locations and service areas",
    },
    {  # Slide 6 - Dark Store Strategy
        "active_tab": 3,
        "title": "Q2.1 — Two Dark Stores Enable 100% HCMC Coverage Within 2hr SLA",
        "bullets": [
            ("DS1 — Tân Phú", "Covers West HCMC: 6 districts, avg 63 min drive saving"),
            ("DS2 — Quận 1", "Covers Central/East: 12 districts, avg 92 min drive saving"),
            ("Investment Case", "Top 6 HCMC districts = 77% of volume — justifies dark store investment"),
            ("Vinh Loc Retained", "Củ Chi & suburban coverage; maintains B2B capability"),
        ],
        "charts": ["q21_hcm_district_volume.png"],
        "chart_caption": "HCMC district order volume distribution and service time analysis",
    },
    {  # Slide 7 - Inventory Optimization
        "active_tab": 4,
        "title": "Q2.2 — Pooling Reduces Safety Stock 49–62% While Preventing Cross-Channel Stockouts",
        "bullets": [
            ("Formula", "SS = Z × σ_daily × √LT (Z=1.645, LT=1.94 days avg)"),
            ("Top SKU SS", "4200009163: 3,174 units, ROP: 3,676 units"),
            ("Pooling Scenarios", "Separated: 31,852 → Shared Pool: 16,325 (−49%) → Mile-Weighted: 12,168 (−62%)"),
            ("Allocation Rule", "Real-time ATP → B2C priority if SLA-critical → B2B 24hr backorder → Escalate"),
        ],
        "charts": ["q22_inventory_pooling.png", "q22_lead_time_sensitivity.png"],
        "chart_caption": "Inventory pooling scenarios (left) and lead time sensitivity analysis (right)",
    },
    {  # Slide 8 - Warehouse Operations (Q3.1)
        "active_tab": 5,
        "title": "Q3.1 — U-Shape Slotting Optimization: 38.2% Travel Time Reduction",
        "bullets": [
            ("Slotting Zones", "Pick-Face (28 Class A) → Forward Reserve (Class B) → Reserve (Class C)"),
            ("Travel Time", "Baseline: 210m/order → Optimized: 130m/order"),
            ("Methodology", "ABC-based zoning with ergonomic height and proximity to packing"),
            ("Result", "SKU-to-zone assignment minimizes cross-aisle travel by 38.2%"),
        ],
        "charts": ["q31_u_shape_heatmap.png"],
        "chart_caption": "U-Shape slotting heatmap showing pick-face zone assignment",
    },
    {  # Slide 9 - Pick-and-Pack Process Flow
        "active_tab": 5,
        "title": "Q3.2 — Omni-Channel Pick-and-Pack Decision Flowchart",
        "bullets": [],
        "charts": [],
        "flowchart": "q32_pick_pack_flowchart.png",
    },
]

NSMAP = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}


def get_next_slide_number():
    existing = [int(m.group(1)) for f in SLIDES_DIR.glob("slide*.xml")
                if (m := re.match(r"slide(\d+)\.xml", f.name))]
    return max(existing) + 1 if existing else 1


def _add_to_content_types(dest_path):
    content = CONTENT_TYPES.read_text(encoding="utf-8")
    override = f'<Override PartName="/ppt/slides/{dest_path}" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
    # Remove existing override for same path
    content = re.sub(
        f'<Override PartName="/ppt/slides/{re.escape(dest_path)}".*?/>\n?',
        '',
        content,
    )
    content = content.replace("</Types>", f"  {override}\n</Types>")
    CONTENT_TYPES.write_text(content, encoding="utf-8")


def _add_to_presentation_rels(dest_path):
    content = PRES_RELS.read_text(encoding="utf-8")
    # Remove existing reference to same slide
    content = re.sub(
        f'<Relationship[^>]*Target="slides/{re.escape(dest_path)}"[^>]*/>\n?',
        '',
        content,
    )
    rids = [int(m) for m in re.findall(r'Id="rId(\d+)"', content)]
    next_rid = max(rids) + 1 if rids else 1
    rid = f"rId{next_rid}"
    new_rel = f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/{dest_path}"/>'
    content = content.replace("</Relationships>", f"  {new_rel}\n</Relationships>")
    PRES_RELS.write_text(content, encoding="utf-8")
    return rid


def _add_to_presentation(dest_path, rid):
    content = PRES_XML.read_text(encoding="utf-8")
    # Remove existing sldId for the slide number
    slide_num_match = re.search(r'slide(\d+)\.xml', dest_path)
    # We can't easily find by slide number in XML, so just ensure we don't have duplicates
    content = re.sub(
        f'<p:sldId[^>]*r:id="{re.escape(rid)}"[^>]*/>\n?',
        '',
        content,
    )
    slide_ids = [int(m) for m in re.findall(r'<p:sldId[^>]*id="(\d+)"', content)]
    next_id = max(slide_ids) + 1 if slide_ids else 256
    new_entry = f'\n    <p:sldId id="{next_id}" r:id="{rid}"/>'
    content = content.replace("</p:sldIdLst>", f"{new_entry}\n  </p:sldIdLst>")
    PRES_XML.write_text(content, encoding="utf-8")


def _add_image_to_content_types(img_path):
    """Add image content type reference."""
    content = CONTENT_TYPES.read_text(encoding="utf-8")
    ext = os.path.splitext(img_path)[1].lower()
    ct_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
    ct = ct_map.get(ext, 'image/png')
    override = f'<Override PartName="/ppt/media/{img_path}" ContentType="{ct}"/>'
    # Remove existing
    content = re.sub(
        f'<Override PartName="/ppt/media/{re.escape(img_path)}".*?/>\n?',
        '',
        content,
    )
    content = content.replace("</Types>", f"  {override}\n</Types>")
    CONTENT_TYPES.write_text(content, encoding="utf-8")


def create_slides():
    """Create slides 2-9 by duplicating slide1."""
    for slide_num in range(2, 10):
        source = "slide1.xml"
        dest = f"slide{slide_num}.xml"
        dest_path = SLIDES_DIR / dest

        # Remove existing slide if any
        if dest_path.exists():
            dest_path.unlink()
        dest_rels = RELS_DIR / f"{dest}.rels"
        if dest_rels.exists():
            dest_rels.unlink()

        # Copy slide XML
        shutil.copy2(SLIDES_DIR / source, dest_path)

        # Copy rels (includes image reference)
        source_rels = RELS_DIR / f"{source}.rels"
        if source_rels.exists():
            dest_rels = RELS_DIR / f"{dest}.rels"
            shutil.copy2(source_rels, dest_rels)
            # Remove notes slide reference if any
            rels_content = dest_rels.read_text(encoding="utf-8")
            rels_content = re.sub(
                r'\s*<Relationship[^>]*Type="[^"]*notesSlide"[^>]*/>\s*',
                "\n",
                rels_content,
            )
            dest_rels.write_text(rels_content, encoding="utf-8")

        # Add to Content_Types.xml
        _add_to_content_types(dest)

        # Add to presentation.xml.rels
        rid = _add_to_presentation_rels(dest)

        # Add sldId to presentation.xml
        _add_to_presentation(dest, rid)

        print(f"Created {dest} (rid={rid})")


def embed_image(slide_num, chart_name):
    """Copy chart image to media folder and add relationship."""
    src = CHARTS_DIR / chart_name
    if not src.exists():
        print(f"  Warning: {src} not found")
        return None

    # Copy to media
    dest_name = f"image_chart_s{slide_num}_{chart_name}"
    shutil.copy2(src, MEDIA_DIR / dest_name)

    # Add to Content_Types
    _add_image_to_content_types(dest_name)

    # Update slide rels
    slide_num_str = f"slide{slide_num}"
    rels_path = RELS_DIR / f"{slide_num_str}.xml.rels"
    rels_content = rels_path.read_text(encoding="utf-8")

    # Find next rId
    rids = [int(m) for m in re.findall(r'Id="rId(\d+)"', rels_content)]
    next_rid = max(rids) + 1 if rids else 3
    rid = f"rId{next_rid}"

    new_rel = f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{dest_name}"/>'
    rels_content = rels_content.replace("</Relationships>", f"  {new_rel}\n</Relationships>")
    rels_path.write_text(rels_content, encoding="utf-8")

    print(f"  Embedded {chart_name} as {rid} in {slide_num_str}")
    return rid


def edit_slide(slide_num, slide_data):
    """Edit a slide's XML content."""
    slide_path = SLIDES_DIR / f"slide{slide_num}.xml"
    tree = etree.parse(str(slide_path))
    root = tree.getroot()

    # Register namespaces
    for prefix, uri in NSMAP.items():
        etree.register_namespace(prefix, uri)

    # Find the spTree element (contains all shapes)
    sp_tree = root.find('.//p:cSld/p:spTree', NSMAP)

    # --- 1. Rename tabs ---
    # Tab 1 (TextBox 9) through Tab 6 (TextBox 14)
    tab_map = {
        9: TABS[0][0],
        10: TABS[1][0],
        11: TABS[2][0],
        12: TABS[3][0],
        13: TABS[4][0],
        14: TABS[5][0],
    }

    for tab_id, tab_name in tab_map.items():
        # Find the textbox by id using python iteration
        for sp in root.iter(f'{{{NSMAP["p"]}}}sp'):
            nv_pr = sp.find(f'{{{NSMAP["p"]}}}nvSpPr')
            if nv_pr is not None:
                cnv_pr = nv_pr.find(f'{{{NSMAP["p"]}}}cNvPr')
                if cnv_pr is not None and cnv_pr.get('id') == str(tab_id):
                    # Found the tab - update text
                    for t_elem in sp.iter(f'{{{NSMAP["a"]}}}t'):
                        if t_elem.text:
                            t_elem.text = tab_name
                            break

    # --- 2. Highlight active tab (bold + coral) ---
    active_tab_idx = slide_data.get("active_tab")
    for tab_id in [9, 10, 11, 12, 13, 14]:
        for sp in root.iter(f'{{{NSMAP["p"]}}}sp'):
            nv_pr = sp.find(f'{{{NSMAP["p"]}}}nvSpPr')
            if nv_pr is not None:
                cnv_pr = nv_pr.find(f'{{{NSMAP["p"]}}}cNvPr')
                if cnv_pr is not None and cnv_pr.get('id') == str(tab_id):
                    is_active = (active_tab_idx is not None and tab_id == 9 + active_tab_idx)
                    for rpr in sp.iter(f'{{{NSMAP["a"]}}}rPr'):
                        if is_active:
                            rpr.set('b', '1')
                            latin = rpr.find(f'{{{NSMAP["a"]}}}latin')
                            if latin is not None:
                                latin.set('typeface', 'Signika Bold')
                            ea = rpr.find(f'{{{NSMAP["a"]}}}ea')
                            if ea is not None:
                                ea.set('typeface', 'Signika Bold')
                            fill = rpr.find(f'{{{NSMAP["a"]}}}solidFill')
                            if fill is not None:
                                srgb = fill.find(f'{{{NSMAP["a"]}}}srgbClr')
                                if srgb is not None:
                                    srgb.set('val', 'F96167')
                        else:
                            if 'b' in rpr.attrib:
                                del rpr.attrib['b']
                            latin = rpr.find(f'{{{NSMAP["a"]}}}latin')
                            if latin is not None:
                                latin.set('typeface', 'Signika')
                            ea = rpr.find(f'{{{NSMAP["a"]}}}ea')
                            if ea is not None:
                                ea.set('typeface', 'Signika')
                            fill = rpr.find(f'{{{NSMAP["a"]}}}solidFill')
                            if fill is not None:
                                srgb = fill.find(f'{{{NSMAP["a"]}}}srgbClr')
                                if srgb is not None:
                                    srgb.set('val', 'FFFFFF')
                    break

    # --- 3. For cover slide (slide 1), remove Freeform 8 and adjust ---
    if slide_data.get("background_title"):
        # Keep as-is (cover slide with minimal changes)
        pass

    # --- 4. Add title text box ---
    title = slide_data.get("title", "")
    if title:
        title_xml_str = f'''<p:sp xmlns:p="{NSMAP['p']}" xmlns:a="{NSMAP['a']}">
  <p:nvSpPr>
    <p:cNvPr id="100" name="SlideTitle"/>
    <p:cNvSpPr txBox="true"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="457200" y="800000"/><a:ext cx="16800000" cy="600000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="none" rtlCol="false"><a:spAutoFit/></a:bodyPr>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r><a:rPr lang="en-US" sz="2400" b="1" caps="none"><a:solidFill><a:srgbClr val="1E2761"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>{self_escape_xml(title)}</a:t></a:r>
    </a:p>
  </p:txBody>
</p:sp>'''
        title_elem = etree.fromstring(title_xml_str.encode())
        sp_tree.append(title_elem)

    # --- 5. Add subtitle if cover ---
    if slide_data.get("subtitle"):
        sub_xml_str = f'''<p:sp xmlns:p="{NSMAP['p']}" xmlns:a="{NSMAP['a']}">
  <p:nvSpPr>
    <p:cNvPr id="101" name="SlideSubtitle"/>
    <p:cNvSpPr txBox="true"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="457200" y="1350000"/><a:ext cx="16800000" cy="400000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="none" rtlCol="false"><a:spAutoFit/></a:bodyPr>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r><a:rPr lang="en-US" sz="1800" b="0"><a:solidFill><a:srgbClr val="2F67A3"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>{self_escape_xml(slide_data["subtitle"])}</a:t></a:r>
    </a:p>
  </p:txBody>
</p:sp>'''
        subtitle_elem = etree.fromstring(sub_xml_str.encode())
        sp_tree.append(subtitle_elem)

    # Add description for cover
    if slide_data.get("description"):
        desc_xml_str = f'''<p:sp xmlns:p="{NSMAP['p']}" xmlns:a="{NSMAP['a']}">
  <p:nvSpPr>
    <p:cNvPr id="102" name="SlideDesc"/>
    <p:cNvSpPr txBox="true"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="457200" y="1700000"/><a:ext cx="16800000" cy="350000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="none" rtlCol="false"><a:spAutoFit/></a:bodyPr>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r><a:rPr lang="en-US" sz="1400" b="0"><a:solidFill><a:srgbClr val="5CE2E7"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>{self_escape_xml(slide_data["description"])}</a:t></a:r>
    </a:p>
  </p:txBody>
</p:sp>'''
        desc_elem = etree.fromstring(desc_xml_str.encode())
        sp_tree.append(desc_elem)

    # --- 6. Add bullets ---
    bullets = slide_data.get("bullets", [])
    if bullets:
        bullet_y_start = 1500000
        bullet_spacing = 500000

        for i, (bold_text, normal_text) in enumerate(bullets):
            y_pos = bullet_y_start + i * bullet_spacing
            # Use narrower width for bullets when chart is present
            has_chart = len(slide_data.get("charts", [])) > 0
            bullet_width = "7600000" if has_chart else "11000000"
            bullet_xml = f'''<p:sp xmlns:p="{NSMAP['p']}" xmlns:a="{NSMAP['a']}">
  <p:nvSpPr>
    <p:cNvPr id="{200 + i}" name="Bullet{i+1}"/>
    <p:cNvSpPr txBox="true"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="457200" y="{y_pos}"/><a:ext cx="{bullet_width}" cy="400000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="none" rtlCol="false"><a:spAutoFit/></a:bodyPr>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l" rtl="0"><a:lnSpc><a:spcPts val="2400"/></a:lnSpc></a:pPr>
      <a:r><a:rPr lang="en-US" sz="1400" b="1"><a:solidFill><a:srgbClr val="1E2761"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>{self_escape_xml(bold_text)}</a:t></a:r>
      <a:r><a:rPr lang="en-US" sz="1400" b="0"><a:solidFill><a:srgbClr val="334155"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t> — {self_escape_xml(normal_text)}</a:t></a:r>
    </a:p>
  </p:txBody>
</p:sp>'''
            bullet_elem = etree.fromstring(bullet_xml.encode())
            sp_tree.append(bullet_elem)

    # --- 7. Add chart images ---
    chart_names = slide_data.get("charts", [])
    for c_idx, chart_name in enumerate(chart_names):
        rid = embed_image(slide_num, chart_name)
        if rid:
            if len(chart_names) == 1:
                cx, x_start = "9200000", "8500000"
                # Determine proper height based on image aspect ratio
                if chart_name == "q31_u_shape_heatmap.png":
                    cy = "3770000"  # 9200000 / 2.44 ≈ 3.77M
                else:
                    cy = "5200000"
            elif len(chart_names) == 2:
                cx, x_start = "4400000", ["8500000", "13100000"][c_idx]
                cy = "5200000"
            else:
                cx, x_start = "9200000", "8500000"
                cy = "5200000"
            chart_img_xml = f'''<p:pic xmlns:p="{NSMAP['p']}" xmlns:a="{NSMAP['a']}" xmlns:r="{NSMAP['r']}">
  <p:nvPicPr>
    <p:cNvPr id="{300 + slide_num * 10 + c_idx}" name="Chart{slide_num}_{c_idx}"/>
    <p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
    <p:nvPr/>
  </p:nvPicPr>
  <p:blipFill>
    <a:blip r:embed="{rid}"/>
    <a:stretch><a:fillRect/></a:stretch>
  </p:blipFill>
  <p:spPr>
    <a:xfrm><a:off x="{x_start}" y="1000000"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
  </p:spPr>
</p:pic>'''
            chart_elem = etree.fromstring(chart_img_xml.encode())
            sp_tree.append(chart_elem)

        # Add chart caption
        caption = slide_data.get("chart_caption", "")
        if caption:
            caption_xml = f'''<p:sp xmlns:p="{NSMAP['p']}" xmlns:a="{NSMAP['a']}">
  <p:nvSpPr>
    <p:cNvPr id="{350 + slide_num}" name="ChartCaption{slide_num}"/>
    <p:cNvSpPr txBox="true"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="8500000" y="6200000"/><a:ext cx="9200000" cy="300000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="none" rtlCol="false"><a:spAutoFit/></a:bodyPr>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r><a:rPr lang="en-US" sz="1000" b="0" italic="1"><a:solidFill><a:srgbClr val="64748B"/></a:solidFill><a:latin typeface="Calibri"/></a:rPr><a:t>{self_escape_xml(caption)}</a:t></a:r>
    </a:p>
  </p:txBody>
</p:sp>'''
            caption_elem = etree.fromstring(caption_xml.encode())
            sp_tree.append(caption_elem)

    # --- 8. Add flowchart (full-width on dedicated slide, preserve aspect ratio) ---
    flowchart = slide_data.get("flowchart")
    if flowchart:
        rid = embed_image(slide_num, flowchart)
        if rid:
            # Flowchart is square (1635x1635). Fit within slide with margins.
            # Slide usable width after margins: ~17700000, usable height after title: ~8000000
            # Constrain by height for a square: 7700000 x 7700000, centered
            fc_size = "7700000"
            fc_x = str(int((18288000 - 7700000) / 2))
            fc_y = "1600000"
            fc_xml = f'''<p:pic xmlns:p="{NSMAP['p']}" xmlns:a="{NSMAP['a']}" xmlns:r="{NSMAP['r']}">
  <p:nvPicPr>
    <p:cNvPr id="{400 + slide_num}" name="Flowchart{slide_num}"/>
    <p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
    <p:nvPr/>
  </p:nvPicPr>
  <p:blipFill>
    <a:blip r:embed="{rid}"/>
    <a:stretch><a:fillRect/></a:stretch>
  </p:blipFill>
  <p:spPr>
    <a:xfrm><a:off x="{fc_x}" y="{fc_y}"/><a:ext cx="{fc_size}" cy="{fc_size}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
  </p:spPr>
</p:pic>'''
            fc_elem = etree.fromstring(fc_xml.encode())
            sp_tree.append(fc_elem)

    # Write modified slide back
    tree.write(str(slide_path), xml_declaration=True, encoding="utf-8", standalone=True)
    print(f"  Edited slide{slide_num}.xml")


def self_escape_xml(text):
    """Escape XML special characters."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text


def main():
    print("=== Step 1: Create slides 2-8 ===")
    create_slides()

    print("\n=== Step 2: Edit all 8 slides ===")
    for i, slide_data in enumerate(SLIDES):
        slide_num = i + 1
        print(f"  Slide {slide_num}...")
        edit_slide(slide_num, slide_data)

    print("\n=== All slides built! ===")
    print("Next: Run clean and pack scripts")
    print(f"  python {os.path.join(os.path.dirname(os.path.abspath(__file__)), '.agents/skills/pptx/scripts/clean.py')} unpacked/")
    print(f"  python {os.path.join(os.path.dirname(os.path.abspath(__file__)), '.agents/skills/pptx/scripts/office/pack.py')} unpacked/ outputs/LOGage2026_Round2_Submission.pptx --original slides/Red Modern Logistic Presentation.pptx")


if __name__ == "__main__":
    main()
