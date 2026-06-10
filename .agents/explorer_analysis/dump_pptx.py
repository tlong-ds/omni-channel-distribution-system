import zipfile
import xml.dom.minidom
import os
import re

def clean_xml_namespaces(xml_string):
    return re.sub(r'\sxmlns[^=]*="[^"]*"', '', xml_string)

def extract_text_from_node(node):
    text_runs = []
    for t_node in node.getElementsByTagName('a:t'):
        if t_node.firstChild and t_node.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
            text_runs.append(t_node.firstChild.data)
    return "".join(text_runs)

def dump_layouts_and_slides(pptx_path):
    with zipfile.ZipFile(pptx_path, 'r') as zf:
        # Check all files in the zip
        namelist = zf.namelist()
        
        # 1. Print instantiated slides
        print("=== INSTANTIATED SLIDES ===")
        pres_xml = zf.read('ppt/presentation.xml').decode('utf-8')
        pres_dom = xml.dom.minidom.parseString(pres_xml)
        
        rels_xml = zf.read('ppt/_rels/presentation.xml.rels').decode('utf-8')
        rels_dom = xml.dom.minidom.parseString(rels_xml)
        
        rid_to_target = {}
        for rel in rels_dom.getElementsByTagName('Relationship'):
            rid = rel.getAttribute('Id')
            target = rel.getAttribute('Target')
            rid_to_target[rid] = target

        sld_ids = pres_dom.getElementsByTagName('p:sldId')
        slide_paths = []
        for sld_id in sld_ids:
            rid = sld_id.getAttribute('r:id')
            target = rid_to_target.get(rid, '')
            if target.startswith('slides/'):
                slide_paths.append('ppt/' + target)
            else:
                slide_paths.append('ppt/slides/' + target)
                
        for idx, slide_path in enumerate(slide_paths, 1):
            print(f"Slide {idx}: {slide_path}")
            try:
                slide_xml = zf.read(slide_path).decode('utf-8')
                slide_dom = xml.dom.minidom.parseString(slide_xml)
                shapes = slide_dom.getElementsByTagName('p:sp')
                text_blocks = []
                for shape in shapes:
                    txBody = shape.getElementsByTagName('p:txBody')
                    if txBody:
                        paragraphs = txBody[0].getElementsByTagName('a:p')
                        for p in paragraphs:
                            text = extract_text_from_node(p)
                            if text.strip():
                                text_blocks.append(text.strip())
                print(f"  Text: {text_blocks}")
            except Exception as e:
                print(f"  Error: {e}")
                
        # 2. Print slide layouts
        print("\n=== SLIDE LAYOUTS ===")
        layout_files = [f for f in namelist if f.startswith('ppt/slideLayouts/') and f.endswith('.xml')]
        layout_files.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else x)
        
        for layout_file in layout_files:
            try:
                layout_xml = zf.read(layout_file).decode('utf-8')
                layout_dom = xml.dom.minidom.parseString(layout_xml)
                csld = layout_dom.getElementsByTagName('p:cSld')[0]
                layout_name = csld.getAttribute('name')
                
                # Check for place holders in the layout
                ph_types = []
                for ph in layout_dom.getElementsByTagName('p:ph'):
                    ph_type = ph.getAttribute('type')
                    ph_idx = ph.getAttribute('idx')
                    ph_types.append(f"{ph_type or 'body'}(idx={ph_idx})")
                
                # Check for text in the layout itself
                shapes = layout_dom.getElementsByTagName('p:sp')
                text_blocks = []
                for shape in shapes:
                    txBody = shape.getElementsByTagName('p:txBody')
                    if txBody:
                        paragraphs = txBody[0].getElementsByTagName('a:p')
                        for p in paragraphs:
                            text = extract_text_from_node(p)
                            if text.strip():
                                text_blocks.append(text.strip())
                                
                print(f"{layout_file} - Name: '{layout_name}'")
                print(f"  Placeholders: {', '.join(ph_types)}")
                if text_blocks:
                    print(f"  Static Text: {text_blocks}")
            except Exception as e:
                print(f"Error reading layout {layout_file}: {e}")

if __name__ == "__main__":
    pptx_file = "/Users/bunnypro/Projects/LOGage2026/Red Modern Logistic Presentation.pptx"
    dump_layouts_and_slides(pptx_file)
