import os
import re
from xml.dom import minidom

def verify_presentation(unpacked_dir):
    slides_dir = os.path.join(unpacked_dir, "ppt", "slides")
    
    # 1. Slide count verification
    slide_files = [f for f in os.listdir(slides_dir) if f.startswith("slide") and f.endswith(".xml")]
    slide_count = len(slide_files)
    print(f"Slide count: {slide_count} slides found.")
    assert slide_count == 11, f"Expected exactly 11 slides, found {slide_count}"
    
    # Bounding box limits (EMUs)
    SLIDE_WIDTH = 18288000
    SLIDE_HEIGHT = 10287000
    NAV_LOGO_BOTTOM = 1509664  # Y coordinate of logo bottom is 442632 + 1067032 = 1509664
    
    # For each slide
    for n in range(1, 12):
        slide_path = os.path.join(slides_dir, f"slide{n}.xml")
        doc = minidom.parse(slide_path)
        spTree = doc.getElementsByTagName("p:spTree")[0]
        
        print(f"\n--- Verifying Slide {n} ---")
        
        # 2. Navigation bar & Logo checks
        shapes = spTree.childNodes
        nav_part1 = False
        nav_part2 = False
        nav_part3 = False
        logo_found = False
        
        content_shapes = []
        
        for child in shapes:
            if child.nodeType != minidom.Node.ELEMENT_NODE:
                continue
                
            nvPr_tags = child.getElementsByTagName("p:cNvPr")
            if not nvPr_tags:
                continue
                
            shp_id = int(nvPr_tags[0].getAttribute("id"))
            shp_name = nvPr_tags[0].getAttribute("name")
            
            # Extract coordinates if they exist
            off_tags = child.getElementsByTagName("a:off")
            ext_tags = child.getElementsByTagName("a:ext")
            x, y, cx, cy = None, None, None, None
            if off_tags and ext_tags:
                x = int(off_tags[0].getAttribute("x"))
                y = int(off_tags[0].getAttribute("y"))
                cx = int(ext_tags[0].getAttribute("cx"))
                cy = int(ext_tags[0].getAttribute("cy"))
            
            if shp_id == 8: # Logo
                logo_found = True
                print(f"Logo found: x={x}, y={y}, cx={cx}, cy={cy}")
                assert x == 17029142, f"Logo X is {x}, expected 17029142"
                assert y == 442632, f"Logo Y is {y}, expected 442632"
                assert cx == 1258858, f"Logo CX is {cx}, expected 1258858"
                assert cy == 1067032, f"Logo CY is {cy}, expected 1067032"
                
            elif shp_id == 9: # Part 1
                nav_part1 = True
                tx = child.getElementsByTagName("a:t")[0].firstChild.data
                print(f"Nav Part 1 text: '{tx}'")
                assert tx == "Part 1", f"Nav Part 1 text is '{tx}', expected 'Part 1'"
                
            elif shp_id == 10: # Part 2
                nav_part2 = True
                tx = child.getElementsByTagName("a:t")[0].firstChild.data
                print(f"Nav Part 2 text: '{tx}'")
                assert tx == "Part 2", f"Nav Part 2 text is '{tx}', expected 'Part 2'"
                
            elif shp_id == 11: # Part 3
                nav_part3 = True
                tx = child.getElementsByTagName("a:t")[0].firstChild.data
                print(f"Nav Part 3 text: '{tx}'")
                assert tx == "Part 3", f"Nav Part 3 text is '{tx}', expected 'Part 3'"
                
            elif shp_id in [12, 13, 14]:
                raise AssertionError(f"Unexpected placeholder nav bar item (id {shp_id}) found on slide {n}!")
                
            elif shp_id >= 100:
                # Content shape
                content_shapes.append({
                    "id": shp_id,
                    "name": shp_name,
                    "x": x, "y": y, "cx": cx, "cy": cy
                })
                
        assert logo_found, f"Logo not found on slide {n}!"
        assert nav_part1 and nav_part2 and nav_part3, f"Navigation bar parts missing on slide {n}!"
        
        # 3. Content overlap & boundary checks
        print(f"Verifying {len(content_shapes)} content shapes...")
        for s in content_shapes:
            x, y, cx, cy = s["x"], s["y"], s["cx"], s["cy"]
            print(f"Shape {s['id']} ({s['name']}): x={x}, y={y}, cx={cx}, cy={cy}")
            
            # Check slide boundaries
            assert x >= 0, f"Shape {s['id']} goes off-screen left (x={x})"
            assert y >= 0, f"Shape {s['id']} goes off-screen top (y={y})"
            assert x + cx <= SLIDE_WIDTH, f"Shape {s['id']} goes off-screen right (x+cx={x+cx})"
            assert y + cy <= SLIDE_HEIGHT, f"Shape {s['id']} goes off-screen bottom (y+cy={y+cy})"
            
            # Check overlap with nav bar & logo
            # All content shapes must be strictly below the nav bar and logo area (Y > NAV_LOGO_BOTTOM)
            assert y >= NAV_LOGO_BOTTOM, f"Shape {s['id']} overlaps with navigation bar/logo space (y={y} < {NAV_LOGO_BOTTOM})"
            
        # 4. Check for placeholder text (lorem, ipsum, xxxx) in all text nodes
        text_nodes = doc.getElementsByTagName("a:t")
        for node in text_nodes:
            if node.firstChild:
                text = node.firstChild.data.lower()
                assert "lorem" not in text, f"Placeholder 'lorem' found on slide {n}!"
                assert "ipsum" not in text, f"Placeholder 'ipsum' found on slide {n}!"
                assert "xxxx" not in text, f"Placeholder 'xxxx' found on slide {n}!"
                
        # 5. Overlap between columns and charts
        # Check pairwise intersections of content shapes
        for i in range(len(content_shapes)):
            for j in range(i + 1, len(content_shapes)):
                s1 = content_shapes[i]
                s2 = content_shapes[j]
                
                # Check for rectangle intersection
                overlap_x = max(0, min(s1["x"] + s1["cx"], s2["x"] + s2["cx"]) - max(s1["x"], s2["x"]))
                overlap_y = max(0, min(s1["y"] + s1["cy"], s2["y"] + s2["cy"]) - max(s1["y"], s2["y"]))
                
                if overlap_x > 0 and overlap_y > 0:
                    # Overlap detected!
                    # Note: We allow titles (y=1800000, cy=1000000) and columns (y=3000000) not to overlap.
                    # Let's make sure columns and charts do not overlap.
                    raise AssertionError(f"Overlap detected between Shape {s1['id']} ({s1['name']}) and Shape {s2['id']} ({s2['name']})!")

    print("\nALL DETERMINISTIC LAYOUT AND CONTENT CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    import sys
    unpacked_dir = sys.argv[1] if len(sys.argv) > 1 else "/Users/bunnypro/teamwork_projects/logage_slides/unpacked"
    verify_presentation(unpacked_dir)
