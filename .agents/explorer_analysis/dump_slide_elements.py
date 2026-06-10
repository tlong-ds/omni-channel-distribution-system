import zipfile
import xml.dom.minidom
import os

def dump_slide_elements(pptx_path):
    with zipfile.ZipFile(pptx_path, 'r') as zf:
        slide_xml = zf.read('ppt/slides/slide1.xml').decode('utf-8')
        dom = xml.dom.minidom.parseString(slide_xml)
        
        # Helper to extract text from a node
        def get_text(node):
            text_runs = []
            for t in node.getElementsByTagName('a:t'):
                if t.firstChild and t.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                    text_runs.append(t.firstChild.data)
            return "".join(text_runs)
            
        print("=== shapes ===")
        for sp in dom.getElementsByTagName('p:sp'):
            name = sp.getElementsByTagName('p:nvSpPr')[0].getElementsByTagName('p:cNvPr')[0].getAttribute('name')
            tx = get_text(sp)
            print(f"Shape name: '{name}', Text: '{tx}'")
            
        print("\n=== picture shapes ===")
        for pic in dom.getElementsByTagName('p:pic'):
            name = pic.getElementsByTagName('p:nvPicPr')[0].getElementsByTagName('p:cNvPr')[0].getAttribute('name')
            print(f"Picture name: '{name}'")
            
        print("\n=== graphic frame shapes (like tables, smartart, charts) ===")
        for gf in dom.getElementsByTagName('p:graphicFrame'):
            name = gf.getElementsByTagName('p:nvGraphicFramePr')[0].getElementsByTagName('p:cNvPr')[0].getAttribute('name')
            print(f"GraphicFrame name: '{name}'")

if __name__ == "__main__":
    pptx_file = "/Users/bunnypro/Projects/LOGage2026/Red Modern Logistic Presentation.pptx"
    dump_slide_elements(pptx_file)
