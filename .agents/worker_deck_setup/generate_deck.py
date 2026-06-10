import os
import shutil
import re
from xml.dom import minidom

def html_escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

def setup_structural_slides(unpacked_dir):
    slides_dir = os.path.join(unpacked_dir, "ppt", "slides")
    rels_dir = os.path.join(slides_dir, "_rels")
    
    # Slide to layout mapping (1-indexed)
    layout_map = {
        1: "slideLayout1.xml",
        2: "slideLayout4.xml",
        3: "slideLayout4.xml",
        4: "slideLayout4.xml",
        5: "slideLayout4.xml",
        6: "slideLayout5.xml",
        7: "slideLayout4.xml",
        8: "slideLayout4.xml",
        9: "slideLayout4.xml",
        10: "slideLayout5.xml",
        11: "slideLayout2.xml"
    }
    
    slide1_path = os.path.join(slides_dir, "slide1.xml")
    slide1_rels_path = os.path.join(rels_dir, "slide1.xml.rels")
    
    # For slide 1: update its rels to point to slideLayout1.xml
    with open(slide1_rels_path, "r", encoding="utf-8") as f:
        slide1_rels_content = f.read()
    
    slide1_rels_updated = re.sub(
        r'Target="[^"]*slideLayout\d+\.xml"',
        'Target="../slideLayouts/slideLayout1.xml"',
        slide1_rels_content
    )
    with open(slide1_rels_path, "w", encoding="utf-8") as f:
        f.write(slide1_rels_updated)
        
    # Copy slide1 to slide2-slide11 and write their rels
    for n in range(2, 12):
        dest_slide = os.path.join(slides_dir, f"slide{n}.xml")
        dest_rels = os.path.join(rels_dir, f"slide{n}.xml.rels")
        
        # Copy slide1.xml
        shutil.copy2(slide1_path, dest_slide)
        
        # Write rels for slide n pointing to the correct layout
        layout_file = layout_map[n]
        with open(slide1_rels_path, "r", encoding="utf-8") as f:
            rels_content = f.read()
            
        rels_updated = re.sub(
            r'Target="[^"]*slideLayout\d+\.xml"',
            f'Target="../slideLayouts/{layout_file}"',
            rels_content
        )
        
        with open(dest_rels, "w", encoding="utf-8") as f:
            f.write(rels_updated)
            
    # Update [Content_Types].xml
    content_types_path = os.path.join(unpacked_dir, "[Content_Types].xml")
    with open(content_types_path, "r", encoding="utf-8") as f:
        ct_content = f.read()
        
    for n in range(2, 12):
        override_str = f'<Override PartName="/ppt/slides/slide{n}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        if f"/ppt/slides/slide{n}.xml" not in ct_content:
            ct_content = ct_content.replace("</Types>", f"  {override_str}\n</Types>")
            
    with open(content_types_path, "w", encoding="utf-8") as f:
        f.write(ct_content)
        
    # Update ppt/_rels/presentation.xml.rels
    pres_rels_path = os.path.join(unpacked_dir, "ppt", "_rels", "presentation.xml.rels")
    with open(pres_rels_path, "r", encoding="utf-8") as f:
        pres_rels_content = f.read()
        
    rids = [int(m) for m in re.findall(r'Id="rId(\d+)"', pres_rels_content)]
    next_rid = max(rids) + 1 if rids else 9
    
    slide_rids = {}
    for n in range(2, 12):
        rid_str = f"rId{next_rid}"
        slide_rids[n] = rid_str
        new_rel = f'<Relationship Id="{rid_str}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{n}.xml"/>'
        if f"slides/slide{n}.xml" not in pres_rels_content:
            pres_rels_content = pres_rels_content.replace("</Relationships>", f"  {new_rel}\n</Relationships>")
            next_rid += 1
            
    with open(pres_rels_path, "w", encoding="utf-8") as f:
        f.write(pres_rels_content)
        
    # Update ppt/presentation.xml
    pres_path = os.path.join(unpacked_dir, "ppt", "presentation.xml")
    with open(pres_path, "r", encoding="utf-8") as f:
        pres_content = f.read()
        
    slide_ids = [int(m) for m in re.findall(r'<p:sldId[^>]*id="(\d+)"', pres_content)]
    next_slide_id = max(slide_ids) + 1 if slide_ids else 257
    
    sldIdLst_match = re.search(r'<p:sldIdLst>.*?</p:sldIdLst>', pres_content, re.DOTALL)
    if sldIdLst_match:
        sldIdLst_content = sldIdLst_match.group(0)
        new_sldIdLst_content = sldIdLst_content
        for n in range(2, 12):
            rid_str = slide_rids[n]
            if f'r:id="{rid_str}"' not in new_sldIdLst_content:
                new_sldId = f'<p:sldId id="{next_slide_id}" r:id="{rid_str}"/>'
                new_sldIdLst_content = new_sldIdLst_content.replace("</p:sldIdLst>", f"  {new_sldId}\n</p:sldIdLst>")
                next_slide_id += 1
        pres_content = pres_content.replace(sldIdLst_content, new_sldIdLst_content)
        
    with open(pres_path, "w", encoding="utf-8") as f:
        f.write(pres_content)


def copy_chart_images(unpacked_dir, charts_src_dir):
    media_dir = os.path.join(unpacked_dir, "ppt", "media")
    os.makedirs(media_dir, exist_ok=True)
    
    required_charts = [
        "q11_abc_xyz_matrix_frequency.png",
        "q11_abc_quantity_distribution.png",
        "q12_warehouse_imbalance.png",
        "q12_geography_coverage_map.png",
        "q12_region_quantity_orders.png",
        "q12_province_distance_correlation.png",
        "q13_order_profile_comparison.png",
        "q13_packaging_mix.png",
        "q21_channel_flow_profile.png",
        "q21_network_coverage.png",
        "q21_hcm_district_volume.png",
        "q22_lead_time_sensitivity.png",
        "q22_inventory_pooling.png",
        "q31_slotting_analysis.png",
        "q32_pick_pack_flowchart.png"
    ]
    
    for chart_name in required_charts:
        src_path = os.path.join(charts_src_dir, chart_name)
        dest_path = os.path.join(media_dir, chart_name)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dest_path)
            print(f"Copied {chart_name} to media directory.")
        else:
            print(f"Warning: Chart {chart_name} not found in {charts_src_dir}")


def update_nav_text_box(sp_node, new_text, is_bold):
    txBody = sp_node.getElementsByTagName("p:txBody")[0]
    
    # Remove existing paragraphs
    for p in list(txBody.getElementsByTagName("a:p")):
        txBody.removeChild(p)
        
    doc = sp_node.ownerDocument
    p_el = doc.createElement("a:p")
    pPr_el = doc.createElement("a:pPr")
    pPr_el.setAttribute("algn", "ctr")
    
    lnSpc_el = doc.createElement("a:lnSpc")
    spcPts_el = doc.createElement("a:spcPts")
    spcPts_el.setAttribute("val", "2800")
    lnSpc_el.appendChild(spcPts_el)
    pPr_el.appendChild(lnSpc_el)
    
    spcBef_el = doc.createElement("a:spcBef")
    spcPct_el = doc.createElement("a:spcPct")
    spcPct_el.setAttribute("val", "0")
    spcBef_el.appendChild(spcPct_el)
    pPr_el.appendChild(spcBef_el)
    
    p_el.appendChild(pPr_el)
    
    r_el = doc.createElement("a:r")
    rPr_el = doc.createElement("a:rPr")
    rPr_el.setAttribute("lang", "en-US")
    rPr_el.setAttribute("sz", "2000")
    if is_bold:
        rPr_el.setAttribute("b", "true")
        font_name = "Signika Bold"
    else:
        font_name = "Signika"
        
    for tag in ["a:latin", "a:ea", "a:cs", "a:sym"]:
        font_el = doc.createElement(tag)
        font_el.setAttribute("typeface", font_name)
        rPr_el.appendChild(font_el)
        
    color_el = doc.createElement("a:solidFill")
    srgb_el = doc.createElement("a:srgbClr")
    srgb_el.setAttribute("val", "FFFFFF")
    color_el.appendChild(srgb_el)
    rPr_el.appendChild(color_el)
    
    r_el.appendChild(rPr_el)
    
    t_el = doc.createElement("a:t")
    t_el.appendChild(doc.createTextNode(new_text))
    r_el.appendChild(t_el)
    
    p_el.appendChild(r_el)
    txBody.appendChild(p_el)

def add_slide_title(spTree, title_text):
    doc = spTree.ownerDocument
    sp = doc.createElement("p:sp")
    
    nvSpPr = doc.createElement("p:nvSpPr")
    cNvPr = doc.createElement("p:cNvPr")
    cNvPr.setAttribute("id", "100")
    cNvPr.setAttribute("name", "Slide Title")
    cNvPr.appendChild(doc.createElement("p:nvPr"))
    nvSpPr.appendChild(cNvPr)
    nvSpPr.appendChild(doc.createElement("p:cNvSpPr"))
    sp.appendChild(nvSpPr)
    
    spPr = doc.createElement("p:spPr")
    xfrm = doc.createElement("a:xfrm")
    off = doc.createElement("a:off")
    off.setAttribute("x", "1000000")
    off.setAttribute("y", "1800000")
    ext = doc.createElement("a:ext")
    ext.setAttribute("cx", "15000000")
    ext.setAttribute("cy", "1000000")
    xfrm.appendChild(off)
    xfrm.appendChild(ext)
    spPr.appendChild(xfrm)
    
    prstGeom = doc.createElement("a:prstGeom")
    prstGeom.setAttribute("prst", "rect")
    prstGeom.appendChild(doc.createElement("a:avLst"))
    spPr.appendChild(prstGeom)
    sp.appendChild(spPr)
    
    txBody = doc.createElement("p:txBody")
    bodyPr = doc.createElement("a:bodyPr")
    bodyPr.setAttribute("anchor", "t")
    bodyPr.setAttribute("rtlCol", "false")
    bodyPr.setAttribute("tIns", "0")
    bodyPr.setAttribute("lIns", "0")
    bodyPr.setAttribute("bIns", "0")
    bodyPr.setAttribute("rIns", "0")
    bodyPr.appendChild(doc.createElement("a:spAutoFit"))
    txBody.appendChild(bodyPr)
    txBody.appendChild(doc.createElement("a:lstStyle"))
    
    p = doc.createElement("a:p")
    pPr = doc.createElement("a:pPr")
    pPr.setAttribute("algn", "l")
    p.appendChild(pPr)
    
    r = doc.createElement("a:r")
    rPr = doc.createElement("a:rPr")
    rPr.setAttribute("lang", "en-US")
    rPr.setAttribute("b", "true")
    rPr.setAttribute("sz", "3600")
    
    color_el = doc.createElement("a:solidFill")
    srgb_el = doc.createElement("a:srgbClr")
    srgb_el.setAttribute("val", "FFFFFF")
    color_el.appendChild(srgb_el)
    rPr.appendChild(color_el)
    
    for tag in ["a:latin", "a:ea", "a:cs", "a:sym"]:
        font = doc.createElement(tag)
        font.setAttribute("typeface", "Signika Bold")
        rPr.appendChild(font)
        
    r.appendChild(rPr)
    t = doc.createElement("a:t")
    t.appendChild(doc.createTextNode(title_text))
    r.appendChild(t)
    p.appendChild(r)
    txBody.appendChild(p)
    sp.appendChild(txBody)
    spTree.appendChild(sp)

def add_title_slide_content(spTree, title, subtitle):
    doc = spTree.ownerDocument
    sp = doc.createElement("p:sp")
    
    nvSpPr = doc.createElement("p:nvSpPr")
    cNvPr = doc.createElement("p:cNvPr")
    cNvPr.setAttribute("id", "100")
    cNvPr.setAttribute("name", "Title Text")
    cNvPr.appendChild(doc.createElement("p:nvPr"))
    nvSpPr.appendChild(cNvPr)
    nvSpPr.appendChild(doc.createElement("p:cNvSpPr"))
    sp.appendChild(nvSpPr)
    
    spPr = doc.createElement("p:spPr")
    xfrm = doc.createElement("a:xfrm")
    off = doc.createElement("a:off")
    off.setAttribute("x", "1000000")
    off.setAttribute("y", "3800000")
    ext = doc.createElement("a:ext")
    ext.setAttribute("cx", "18000000")
    ext.setAttribute("cy", "2000000")
    xfrm.appendChild(off)
    xfrm.appendChild(ext)
    spPr.appendChild(xfrm)
    
    prstGeom = doc.createElement("a:prstGeom")
    prstGeom.setAttribute("prst", "rect")
    prstGeom.appendChild(doc.createElement("a:avLst"))
    spPr.appendChild(prstGeom)
    sp.appendChild(spPr)
    
    txBody = doc.createElement("p:txBody")
    bodyPr = doc.createElement("a:bodyPr")
    bodyPr.setAttribute("anchor", "t")
    bodyPr.setAttribute("rtlCol", "false")
    bodyPr.setAttribute("tIns", "0")
    bodyPr.setAttribute("lIns", "0")
    bodyPr.setAttribute("bIns", "0")
    bodyPr.setAttribute("rIns", "0")
    bodyPr.appendChild(doc.createElement("a:spAutoFit"))
    txBody.appendChild(bodyPr)
    txBody.appendChild(doc.createElement("a:lstStyle"))
    
    p_title = doc.createElement("a:p")
    pPr_title = doc.createElement("a:pPr")
    pPr_title.setAttribute("algn", "l")
    p_title.appendChild(pPr_title)
    
    r_title = doc.createElement("a:r")
    rPr_title = doc.createElement("a:rPr")
    rPr_title.setAttribute("lang", "en-US")
    rPr_title.setAttribute("b", "true")
    rPr_title.setAttribute("sz", "4800")
    
    color_title = doc.createElement("a:solidFill")
    srgb_title = doc.createElement("a:srgbClr")
    srgb_title.setAttribute("val", "FFFFFF")
    color_title.appendChild(srgb_title)
    rPr_title.appendChild(color_title)
    
    for tag in ["a:latin", "a:ea", "a:cs", "a:sym"]:
        font = doc.createElement(tag)
        font.setAttribute("typeface", "Signika Bold")
        rPr_title.appendChild(font)
        
    r_title.appendChild(rPr_title)
    t_title = doc.createElement("a:t")
    t_title.appendChild(doc.createTextNode(title))
    r_title.appendChild(t_title)
    p_title.appendChild(r_title)
    txBody.appendChild(p_title)
    
    p_sub = doc.createElement("a:p")
    pPr_sub = doc.createElement("a:pPr")
    pPr_sub.setAttribute("algn", "l")
    spcBef = doc.createElement("a:spcBef")
    spcPts = doc.createElement("a:spcPts")
    spcPts.setAttribute("val", "3000")
    spcBef.appendChild(spcPts)
    pPr_sub.appendChild(spcBef)
    p_sub.appendChild(pPr_sub)
    
    r_sub = doc.createElement("a:r")
    rPr_sub = doc.createElement("a:rPr")
    rPr_sub.setAttribute("lang", "en-US")
    rPr_sub.setAttribute("sz", "2200")
    
    color_sub = doc.createElement("a:solidFill")
    srgb_sub = doc.createElement("a:srgbClr")
    srgb_sub.setAttribute("val", "CADCFC")
    color_sub.appendChild(srgb_sub)
    rPr_sub.appendChild(color_sub)
    
    for tag in ["a:latin", "a:ea", "a:cs", "a:sym"]:
        font = doc.createElement(tag)
        font.setAttribute("typeface", "Signika")
        rPr_sub.appendChild(font)
        
    r_sub.appendChild(rPr_sub)
    t_sub = doc.createElement("a:t")
    t_sub.appendChild(doc.createTextNode(subtitle))
    r_sub.appendChild(t_sub)
    p_sub.appendChild(r_sub)
    txBody.appendChild(p_sub)
    
    sp.appendChild(txBody)
    spTree.appendChild(sp)

def add_text_column(spTree, x, y, cx, cy, bullets, col_id):
    doc = spTree.ownerDocument
    sp = doc.createElement("p:sp")
    
    nvSpPr = doc.createElement("p:nvSpPr")
    cNvPr = doc.createElement("p:cNvPr")
    cNvPr.setAttribute("id", str(101 + col_id))
    cNvPr.setAttribute("name", f"Text Column {col_id}")
    cNvPr.appendChild(doc.createElement("p:nvPr"))
    nvSpPr.appendChild(cNvPr)
    nvSpPr.appendChild(doc.createElement("p:cNvSpPr"))
    sp.appendChild(nvSpPr)
    
    spPr = doc.createElement("p:spPr")
    xfrm = doc.createElement("a:xfrm")
    off = doc.createElement("a:off")
    off.setAttribute("x", str(x))
    off.setAttribute("y", str(y))
    ext = doc.createElement("a:ext")
    ext.setAttribute("cx", str(cx))
    ext.setAttribute("cy", str(cy))
    xfrm.appendChild(off)
    xfrm.appendChild(ext)
    spPr.appendChild(xfrm)
    
    prstGeom = doc.createElement("a:prstGeom")
    prstGeom.setAttribute("prst", "rect")
    prstGeom.appendChild(doc.createElement("a:avLst"))
    spPr.appendChild(prstGeom)
    sp.appendChild(spPr)
    
    txBody = doc.createElement("p:txBody")
    bodyPr = doc.createElement("a:bodyPr")
    bodyPr.setAttribute("anchor", "t")
    bodyPr.setAttribute("rtlCol", "false")
    bodyPr.setAttribute("tIns", "0")
    bodyPr.setAttribute("lIns", "0")
    bodyPr.setAttribute("bIns", "0")
    bodyPr.setAttribute("rIns", "0")
    bodyPr.appendChild(doc.createElement("a:spAutoFit"))
    txBody.appendChild(bodyPr)
    txBody.appendChild(doc.createElement("a:lstStyle"))
    
    for bullet in bullets:
        level = 1
        clean_bullet = bullet
        if bullet.startswith("  "):
            level = 2
            clean_bullet = bullet.strip()
            
        marL = 457200 * level
        indent = -457200
        bullet_char = "•" if level == 1 else "–"
        
        p = doc.createElement("a:p")
        pPr = doc.createElement("a:pPr")
        pPr.setAttribute("marL", str(marL))
        pPr.setAttribute("indent", str(indent))
        pPr.setAttribute("algn", "l")
        
        buChar = doc.createElement("a:buChar")
        buChar.setAttribute("char", bullet_char)
        pPr.appendChild(buChar)
        
        lnSpc = doc.createElement("a:lnSpc")
        spcPts = doc.createElement("a:spcPts")
        spcPts.setAttribute("val", "1500")
        lnSpc.appendChild(spcPts)
        pPr.appendChild(lnSpc)
        p.appendChild(pPr)
        
        m = re.match(r"^\*\*([^*]+)\*\*(.*)$", clean_bullet)
        if not m:
            m = re.match(r"^\*([^*]+)\*(.*)$", clean_bullet)
            
        if m:
            bold_part = m.group(1)
            reg_part = m.group(2)
            
            r_bold = doc.createElement("a:r")
            rPr_bold = doc.createElement("a:rPr")
            rPr_bold.setAttribute("lang", "en-US")
            rPr_bold.setAttribute("b", "true")
            rPr_bold.setAttribute("sz", "1500")
            
            color_el = doc.createElement("a:solidFill")
            srgb_el = doc.createElement("a:srgbClr")
            srgb_el.setAttribute("val", "FFFFFF")
            color_el.appendChild(srgb_el)
            rPr_bold.appendChild(color_el)
            
            for tag in ["a:latin", "a:ea", "a:cs", "a:sym"]:
                font = doc.createElement(tag)
                font.setAttribute("typeface", "Signika Bold")
                rPr_bold.appendChild(font)
                
            r_bold.appendChild(rPr_bold)
            t_bold = doc.createElement("a:t")
            t_bold.appendChild(doc.createTextNode(bold_part))
            r_bold.appendChild(t_bold)
            p.appendChild(r_bold)
            
            if reg_part:
                r_reg = doc.createElement("a:r")
                rPr_reg = doc.createElement("a:rPr")
                rPr_reg.setAttribute("lang", "en-US")
                rPr_reg.setAttribute("sz", "1400")
                
                color_el = doc.createElement("a:solidFill")
                srgb_el = doc.createElement("a:srgbClr")
                srgb_el.setAttribute("val", "E0E0E0")
                color_el.appendChild(srgb_el)
                rPr_reg.appendChild(color_el)
                
                for tag in ["a:latin", "a:ea", "a:cs", "a:sym"]:
                    font = doc.createElement(tag)
                    font.setAttribute("typeface", "Signika")
                    rPr_reg.appendChild(font)
                    
                r_reg.appendChild(rPr_reg)
                t_reg = doc.createElement("a:t")
                t_reg.appendChild(doc.createTextNode(reg_part))
                r_reg.appendChild(t_reg)
                p.appendChild(r_reg)
        else:
            r_reg = doc.createElement("a:r")
            rPr_reg = doc.createElement("a:rPr")
            rPr_reg.setAttribute("lang", "en-US")
            rPr_reg.setAttribute("sz", "1400")
            
            color_el = doc.createElement("a:solidFill")
            srgb_el = doc.createElement("a:srgbClr")
            srgb_el.setAttribute("val", "E0E0E0")
            color_el.appendChild(srgb_el)
            rPr_reg.appendChild(color_el)
            
            for tag in ["a:latin", "a:ea", "a:cs", "a:sym"]:
                font = doc.createElement(tag)
                font.setAttribute("typeface", "Signika")
                rPr_reg.appendChild(font)
                
            r_reg.appendChild(rPr_reg)
            t_reg = doc.createElement("a:t")
            t_reg.appendChild(doc.createTextNode(clean_bullet))
            r_reg.appendChild(t_reg)
            p.appendChild(r_reg)
            
        txBody.appendChild(p)
    sp.appendChild(txBody)
    spTree.appendChild(sp)

def add_chart_picture(spTree, rels_doc, x, y, cx, cy, chart_name, pic_id):
    rels = rels_doc.getElementsByTagName("Relationships")[0]
    existing_rels = rels.getElementsByTagName("Relationship")
    
    rids = []
    for r in existing_rels:
        m = re.match(r"rId(\d+)", r.getAttribute("Id"))
        if m:
            rids.append(int(m.group(1)))
            
    next_rid = max(rids) + 1 if rids else 10
    rid_str = f"rId{next_rid}"
    
    rel = rels_doc.createElement("Relationship")
    rel.setAttribute("Id", rid_str)
    rel.setAttribute("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
    rel.setAttribute("Target", f"../media/{chart_name}")
    rels.appendChild(rel)
    
    doc = spTree.ownerDocument
    pic = doc.createElement("p:pic")
    
    nvPicPr = doc.createElement("p:nvPicPr")
    cNvPr = doc.createElement("p:cNvPr")
    cNvPr.setAttribute("id", str(200 + pic_id))
    cNvPr.setAttribute("name", f"Chart {pic_id}")
    nvPicPr.appendChild(cNvPr)
    
    cNvPicPr = doc.createElement("p:cNvPicPr")
    picLocks = doc.createElement("a:picLocks")
    picLocks.setAttribute("noChangeAspect", "1")
    cNvPicPr.appendChild(picLocks)
    nvPicPr.appendChild(cNvPicPr)
    nvPicPr.appendChild(doc.createElement("p:nvPr"))
    pic.appendChild(nvPicPr)
    
    blipFill = doc.createElement("p:blipFill")
    blip = doc.createElement("a:blip")
    blip.setAttribute("r:embed", rid_str)
    blipFill.appendChild(blip)
    stretch = doc.createElement("a:stretch")
    stretch.appendChild(doc.createElement("a:fillRect"))
    blipFill.appendChild(stretch)
    pic.appendChild(blipFill)
    
    spPr = doc.createElement("p:spPr")
    xfrm = doc.createElement("a:xfrm")
    off = doc.createElement("a:off")
    off.setAttribute("x", str(x))
    off.setAttribute("y", str(y))
    ext = doc.createElement("a:ext")
    ext.setAttribute("cx", str(cx))
    ext.setAttribute("cy", str(cy))
    xfrm.appendChild(off)
    xfrm.appendChild(ext)
    spPr.appendChild(xfrm)
    
    prstGeom = doc.createElement("a:prstGeom")
    prstGeom.setAttribute("prst", "rect")
    prstGeom.appendChild(doc.createElement("a:avLst"))
    spPr.appendChild(prstGeom)
    pic.appendChild(spPr)
    
    spTree.appendChild(pic)

def customize_slides(unpacked_dir, slides_content):
    for n in range(1, 12):
        slide_path = os.path.join(unpacked_dir, "ppt", "slides", f"slide{n}.xml")
        rels_path = os.path.join(unpacked_dir, "ppt", "slides", "_rels", f"slide{n}.xml.rels")
        
        doc = minidom.parse(slide_path)
        rels_doc = minidom.parse(rels_path)
        
        spTree = doc.getElementsByTagName("p:spTree")[0]
        
        # Clean slide except base shapes (IDs 2, 5, 8, 9, 10, 11)
        children = list(spTree.childNodes)
        for child in children:
            if child.nodeType != minidom.Node.ELEMENT_NODE:
                continue
            tag = child.tagName
            if tag in ["p:nvGrpSpPr", "p:grpSpPr"]:
                continue
            
            nvPr_tags = child.getElementsByTagName("p:cNvPr")
            if not nvPr_tags:
                spTree.removeChild(child)
                continue
                
            shp_id = int(nvPr_tags[0].getAttribute("id"))
            if shp_id == 2:
                continue
            elif shp_id == 5:
                if n in range(3, 11):
                    # Update highlight position
                    grp5 = child
                    if n in [3, 4, 5, 6]: # Part 1
                        target_x = "0"
                        target_cx = "2579097"
                    elif n in [7, 8, 9]: # Part 2
                        target_x = "2036732"
                        target_cx = "4986612"
                    else: # Part 3
                        target_x = "6352096"
                        target_cx = "2398777"
                    
                    xfrms = grp5.getElementsByTagName("a:xfrm")
                    if xfrms:
                        xfrm = xfrms[0]
                        offs = xfrm.getElementsByTagName("a:off")
                        if offs:
                            offs[0].setAttribute("x", target_x)
                        exts = xfrm.getElementsByTagName("a:ext")
                        if exts:
                            exts[0].setAttribute("cx", target_cx)
                else:
                    spTree.removeChild(child)
            elif shp_id == 8:
                continue
            elif shp_id == 9:
                update_nav_text_box(child, "Part 1", n in [3, 4, 5, 6])
            elif shp_id == 10:
                update_nav_text_box(child, "Part 2", n in [7, 8, 9])
            elif shp_id == 11:
                update_nav_text_box(child, "Part 3", n == 10)
            else:
                spTree.removeChild(child)
                
        # Populate content
        data = slides_content[n]
        if n == 1:
            add_title_slide_content(spTree, data["title"], data["subtitle"])
        else:
            add_slide_title(spTree, data["title"])
            
            # Columns
            if "columns" in data:
                for col_id, col in enumerate(data["columns"]):
                    add_text_column(spTree, col["x"], col["y"], col["cx"], col["cy"], col["bullets"], col_id)
            
            # Charts
            if "charts" in data:
                for pic_id, chart in enumerate(data["charts"]):
                    add_chart_picture(spTree, rels_doc, chart["x"], chart["y"], chart["cx"], chart["cy"], chart["name"], pic_id)
                    
        # Save files
        with open(slide_path, "w", encoding="utf-8") as f:
            f.write(doc.toxml())
            
        with open(rels_path, "w", encoding="utf-8") as f:
            f.write(rels_doc.toxml())
        print(f"Slide {n} customized successfully.")

# Slide Content Data Mapping
slides_content = {
    1: {
        "title": "Omni-Channel Logistics & Supply Chain Strategy",
        "subtitle": "Data-Driven Optimization for Multi-Channel Operations, Inventory Control, and Warehouse Slotting"
    },
    2: {
        "title": "Executive Summary: Key Operational Insights",
        "columns": [
            {
                "x": 1000000, "y": 3000000, "cx": 8500000, "cy": 6500000,
                "bullets": [
                    "**Extreme SKU Concentration**: A tiny core of 19 \"Fast-Moving\" A-X SKUs (4.04% of assortment) drives 57.87% of outbound quantity and 25.88% of pick transactions.",
                    "**Centralized Invoicing Distortion**: Resolved data initially showed a 92.59% My Phuoc bias. Statistical scaling restored the true operational split: 93.02% My Phuoc vs. 6.98% Vinh Loc."
                ]
            },
            {
                "x": 10500000, "y": 3000000, "cx": 8500000, "cy": 6500000,
                "bullets": [
                    "**Distinct Segment Profiles**: Modern Trade orders are large, consolidated, and pallet-centric (75.25% pallet share). Traditional Trade orders are small, fragmented (48.54% carton, 9.77% loose), and spread across 60 provinces.",
                    "**Virtual Inventory Pooling**: Merging channel safety stocks under a mile-weighted lead time of 1.94 days yields a **61.8% inventory reduction** (12,168 units vs. 31,852 units).",
                    "**Ergonomic Slotting**: Model 2 (ABC + Ergonomics) achieves a **77.5% expected travel time reduction**, exceeding the 30% peak improvement target."
                ]
            }
        ]
    },
    3: {
        "title": "SKU Demand Pattern Classification (ABC-XYZ Analysis)",
        "columns": [
            {
                "x": 1000000, "y": 3000000, "cx": 8000000, "cy": 6500000,
                "bullets": [
                    "**Assortment Classification**: 470 unique SKUs evaluated across volume (ABC) and transaction frequency (XYZ) over 7 months.",
                    "**ABC Volume Concentration**: Class A (Top 70% quantity) includes 28 SKUs; Class B (Next 20%) includes 39 SKUs; Class C (Bottom 10%) includes 403 SKUs.",
                    "**XYZ Frequency Concentration**: Class X (Top 70% orders) includes 53 SKUs; Class Y (Next 20%) includes 88 SKUs; Class Z (Bottom 10%) includes 329 SKUs.",
                    "**The Fast-Moving Group (A-X)**: 19 SKUs (4.04%) drive **57.87% of outbound quantity** (163,014 units) and **25.88% of pick transactions** (5,381 orders).",
                    "**Operational Recommendations**: Dedicated replenishment and lower pick-face positioning (levels 1 and 2) must be reserved for the 19 A-X SKUs to minimize travel time.",
                    "  Rationalize or store in deep reserve the 329 C-Z slow-moving SKUs (70.0% of assortment)."
                ]
            }
        ],
        "charts": [
            {
                "x": 9500000, "y": 3000000, "cx": 7500000, "cy": 3000000,
                "name": "q11_abc_xyz_matrix_frequency.png"
            },
            {
                "x": 9500000, "y": 6500000, "cx": 7500000, "cy": 3000000,
                "name": "q11_abc_quantity_distribution.png"
            }
        ]
    },
    4: {
        "title": "Warehouse Throughput Analysis & Data Quality",
        "columns": [
            {
                "x": 1000000, "y": 3000000, "cx": 8000000, "cy": 6500000,
                "bullets": [
                    "**High Geocoding Resolution**: The data cleansing pipeline successfully resolved 97.12% of transaction rows and 94.15% of outbound quantities to specific coordinates.",
                    "**Database Gaps**: 617 rows were left unresolved due to 'unknown' Ship-to Customers in the source logs.",
                    "**Centralized Invoicing Distortion**: ERP invoicing initially attributes 92.59% of resolved volume to My Phuoc. Utilizing Statistical Scaling (Approach A), we restore the true 93.02% vs. 6.98% operational split.",
                    "**Throughput Realities**: My Phuoc processes 262,053 units (93.02% of quantity and 93.22% of CBM) over 16,142 rows. Vinh Loc processes 19,652 units (6.98% of quantity and 6.78% of CBM) over 5,258 rows.",
                    "**Operational Focus**: Planning and resource allocation must remain focused on My Phuoc as the high-volume core."
                ]
            }
        ],
        "charts": [
            {
                "x": 9500000, "y": 3000000, "cx": 7500000, "cy": 3000000,
                "name": "q12_warehouse_imbalance.png"
            },
            {
                "x": 9500000, "y": 6500000, "cx": 7500000, "cy": 3000000,
                "name": "q12_geography_coverage_map.png"
            }
        ]
    },
    5: {
        "title": "Geographic Demand Mapping & Regional Concentration",
        "columns": [
            {
                "x": 1000000, "y": 3000000, "cx": 8000000, "cy": 6500000,
                "bullets": [
                    "**Southeast Focus**: Đông Nam Bộ is the dominant demand region, accounting for **47.36% of resolved quantity** (125,617 units) and 49% of orders.",
                    "**Central & Mekong Hubs**: Bắc Trung Bộ & Duyên hải miền Trung represents **25.49% of volume** (67,606 units), and Đồng bằng sông Cửu Long drives **15.16%** (40,204 units).",
                    "**Top Provinces**: Hồ Chí Minh City leads with 32.95% of orders and 27.47% of quantity (65,527 units). Bình Dương follows with 15.53% of orders and 18.03% of quantity (43,012 units).",
                    "**Distance vs. Volume Correlation**: Delivery distance is negatively correlated with order size. Close-by urban centers (HCMC and surrounding areas) order in high density and frequency.",
                    "**Regional Logistics**: Transportation routes must be optimized for HCMC-Binh Duong milk runs to handle the dense local demand."
                ]
            }
        ],
        "charts": [
            {
                "x": 9500000, "y": 3000000, "cx": 7500000, "cy": 3000000,
                "name": "q12_region_quantity_orders.png"
            },
            {
                "x": 9500000, "y": 6500000, "cx": 7500000, "cy": 3000000,
                "name": "q12_province_distance_correlation.png"
            }
        ]
    },
    6: {
        "title": "Customer Segment Profiling: MT vs. TT",
        "columns": [
            {
                "x": 1000000, "y": 3000000, "cx": 4200000, "cy": 6500000,
                "bullets": [
                    "**Modern Trade (MT) Profile**:",
                    "  132 active customers, 1,564 orders.",
                    "  Orders are highly consolidated, averaging **80.19 pcs** and **5.16 m³**.",
                    "  Narrow SKU breadth (2.84 SKUs/order) and concentrated in 34 provinces.",
                    "  Highly pallet-centric (**75.25% of quantity** is shipped as full pallets). Carton picking is 22.52%, and loose picking is only 2.23%."
                ]
            },
            {
                "x": 5400000, "y": 3000000, "cx": 4200000, "cy": 6500000,
                "bullets": [
                    "**Traditional Trade (TT) Profile**:",
                    "  270 active customers, 3,782 orders.",
                    "  Orders are small and fragmented, averaging **41.33 pcs** and **2.13 m³**.",
                    "  Broad SKU breadth (4.33 SKUs/order) and dispersed across 60 provinces.",
                    "  Highly carton-centric (**48.54%**) and loose-picking reliant (**9.77%**).",
                    "**Synthesis**: MT requires high-volume pallet-loading bays; TT demands intensive piece-picking and carton-sorting zones."
                ]
            }
        ],
        "charts": [
            {
                "x": 9800000, "y": 3000000, "cx": 7200000, "cy": 3000000,
                "name": "q13_order_profile_comparison.png"
            },
            {
                "x": 9800000, "y": 6500000, "cx": 7200000, "cy": 3000000,
                "name": "q13_packaging_mix.png"
            }
        ]
    },
    7: {
        "title": "Network Model Assessment & Channel Flow Profile",
        "columns": [
            {
                "x": 1000000, "y": 3000000, "cx": 8000000, "cy": 6500000,
                "bullets": [
                    "**Two-RDC Footprint**: My Phuoc (Binh Duong) and Vinh Loc (HCMC). Both warehouses handle mixed B2B and B2C flows.",
                    "**Timeline Discrepancy**: My Phuoc operates over the full 6 months (Jun–Nov). Vinh Loc is a new facility, operational in December only (1 month).",
                    "**B2B Flow Dominance**: B2B represents **99.2% of CBM** at My Phuoc and **99.7% of CBM** at Vinh Loc.",
                    "**Year-End Surge**: On a normalized daily basis, Vinh Loc processed B2B orders at a daily rate of 48.7 orders/active day, exceeding My Phuoc's 25.5 orders/active day, indicating strong December peak demands.",
                    "**SLA Failure Modes**: Standard RDC locations are too far (>10 km) from central districts to support HCMC B2C e-commerce same-day 2–4 hour delivery SLAs."
                ]
            }
        ],
        "charts": [
            {
                "x": 9500000, "y": 3000000, "cx": 7500000, "cy": 6500000,
                "name": "q21_channel_flow_profile.png"
            }
        ]
    },
    8: {
        "title": "HCMC SLA Feasibility & Dark Store Nodes",
        "columns": [
            {
                "x": 1000000, "y": 3000000, "cx": 8000000, "cy": 6500000,
                "bullets": [
                    "**SLA Threshold**: Set at a 25 km radius from existing RDCs to secure a 2–4 hour delivery SLA across HCMC (assuming 25 km/h urban transit).",
                    "**Current Coverage**: All 21 districts of HCMC lie within 25 km of Vinh Loc or My Phuoc. However, heavy traffic makes inner-city SLA fulfillment from RDCs highly volatile.",
                    "**Node 1 (Bình Tân/Tân Phú Corridor)**: High-volume cluster (>50,000 units). Vinh Loc is situated 5–7 km away. Recommended to upgrade Vinh Loc's satellite capabilities.",
                    "**Node 2 (District 1/3/Phú Nhuận CBD)**: Distance to RDCs is 14+ km. Establish a small urban dark store (200–300 m²) stocked with top A-X SKUs.",
                    "**Order Split Logic**: If HCMC address is < 25 km from Vinh Loc, route to Vinh Loc. If < 35 km from My Phuoc, route to My Phuoc. Otherwise, route via urban dark store."
                ]
            }
        ],
        "charts": [
            {
                "x": 9500000, "y": 3000000, "cx": 7500000, "cy": 3000000,
                "name": "q21_network_coverage.png"
            },
            {
                "x": 9500000, "y": 6500000, "cx": 7500000, "cy": 3000000,
                "name": "q21_hcm_district_volume.png"
            }
        ]
    },
    9: {
        "title": "Lead Time and Class A Safety Stock Optimization",
        "columns": [
            {
                "x": 1000000, "y": 3000000, "cx": 8000000, "cy": 6500000,
                "bullets": [
                    "**Mile-Weighted Lead Time**: RDC serves 6 regions. Weighting regional standard lead times by order shares results in a **weighted average lead time of 1.94 days**.",
                    "**Regional Standards**: Southeast is 1 day (49% of orders); Central is 3 days (19.2% of orders); Mekong Delta is 2 days (15.0% of orders); North is 4 days (9.4% of orders).",
                    "**Safety Stock Model**: Demand-uncertainty formula over 7 months (Jun–Dec 2025) at a 95% service level (Z = 1.645):",
                    "  SS = Z * std_dev * sqrt(LT)",
                    "**Class A Results**: Total safety stock across all 28 Class A SKUs is **12,168 units** under a pooled model.",
                    "**Lead Time Sensitivity**: Safety stock grows sub-linearly (sqrt(LT)). Lowering average lead time from 1.94 days to 1.0 day yields a 28.2% safety stock reduction (to 8,736 units)."
                ]
            }
        ],
        "charts": [
            {
                "x": 9500000, "y": 3000000, "cx": 7500000, "cy": 6500000,
                "name": "q22_lead_time_sensitivity.png"
            }
        ]
    },
    10: {
        "title": "Inventory Pooling & Operational Control",
        "columns": [
            {
                "x": 1000000, "y": 3000000, "cx": 8000000, "cy": 6500000,
                "bullets": [
                    "**Virtual Pooling Model**: Merging B2B and B2C inventories into a single physical pool in WMS/OMS, rather than physically dedicating stock.",
                    "**Financial Impact**: Reduces total required safety stock by **61.8%** (12,168 units vs. 31,852 units), saving **19,684 units** of inventory.",
                    "**Operational Rules**: Enforce 6 controls: (R1) Common Pool; (R2) Per-channel ROP floors; (R3) Amber alert thresholds; (R4) Red conflict priority routing (MT first, TT last); (R5) SKU spike freezes; (R6) EOD rebalancing.",
                    "**Model 2 Ergonomic Slotting**: Sub-tiers Class A into A1 Pallet (pallet share > 40%), A2 Big-Face (carton share > 80% at waist-height), and A3 Mixed.",
                    "**Expected Travel Distance Reduction**: Model 2 yields a **77.5% expected travel-time reduction** (vs 51.6% for Model 1), driven by forklift aisle separation and waist-height picking for fast-movers.",
                    "**Pick-and-Pack Processes**: B2B utilizes total pallet picking and direct dock staging. B2C utilizes batch wave picking, trolley carts, and sort-consolidate QC."
                ]
            }
        ],
        "charts": [
            {
                "x": 9500000, "y": 3000000, "cx": 7500000, "cy": 3000000,
                "name": "q22_inventory_pooling.png"
            },
            {
                "x": 9500000, "y": 6500000, "cx": 7500000, "cy": 3000000,
                "name": "q31_slotting_analysis.png"
            }
        ]
    },
    11: {
        "title": "Strategic Recommendations & Execution Roadmap",
        "columns": [
            {
                "x": 1000000, "y": 3000000, "cx": 8000000, "cy": 6500000,
                "bullets": [
                    "**Deploy Virtual Inventory Pooling**: Transition to a single physical WMS pool and implement the 6 conflict control rules (R1-R6) to capture the 61.8% safety stock savings.",
                    "**Implement Model 2 Ergonomic Slotting**: Reconfigure My Phuoc's layout to separate forklift pallet lanes (A1) from manual carton pick-faces (A2) to secure the 77.5% travel time reduction.",
                    "**Establish HCMC Urban Fulfillment Network**: Upgrade Vinh Loc's satellite capabilities to launch a pilot dark store in the Bình Tân/Tân Phú corridor, securing same-day B2C SLAs.",
                    "**Resolve ERP Invoicing Bias**: Correct invoicing-location logic in the ERP to ensure physical dispatches from Vinh Loc are not mistakenly attributed to My Phuoc."
                ]
            }
        ],
        "charts": [
            {
                "x": 9500000, "y": 3000000, "cx": 7500000, "cy": 6500000,
                "name": "q32_pick_pack_flowchart.png"
            }
        ]
    }
}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python generate_deck.py <unpacked_dir> <charts_src_dir>")
        sys.exit(1)
        
    unpacked_dir = sys.argv[1]
    charts_src_dir = sys.argv[2]
    
    print("Setting up structural slides...")
    setup_structural_slides(unpacked_dir)
    
    print("Copying chart images...")
    copy_chart_images(unpacked_dir, charts_src_dir)
    
    print("Customizing slide contents...")
    customize_slides(unpacked_dir, slides_content)
    print("Slide customization completed successfully!")
