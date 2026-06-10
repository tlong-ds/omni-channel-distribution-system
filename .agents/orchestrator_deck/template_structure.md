# Template Presentation Structure Report

This document outlines the internal structure, slide listing, relationship IDs, and layout configurations for the template presentation (`Red Modern Logistic Presentation.pptx`).

---

## 1. Slide List (`<p:sldIdLst>`)
The `ppt/presentation.xml` file specifies the active slides in the presentation. There is **1 slide** in this template:

```xml
<p:sldIdLst>
  <p:sldId id="256" r:id="rId6"/>
</p:sldIdLst>
```

---

## 2. Presentation Relationships (`ppt/_rels/presentation.xml.rels`)
The relationship ID `rId6` points to the following slide file:
* **rId6**: `slides/slide1.xml`

Other key relationships in the presentation:
* **rId1**: `slideMasters/slideMaster1.xml`
* **rId2**: `presProps.xml`
* **rId3**: `viewProps.xml`
* **rId4**: `theme/theme1.xml`
* **rId5**: `tableStyles.xml`
* **rId7**: `fonts/font7.fntdata`
* **rId8**: `fonts/font8.fntdata`

---

## 3. Slide Layout Mapping
In `ppt/slides/_rels/slide1.xml.rels`, we mapped `slide1.xml` to its layout:
* **slide1.xml** uses `rId1` pointing to `../slideLayouts/slideLayout7.xml`.
* **Layout Name**: `Blank`

---

## 4. Unpacked Layout Files (`ppt/slideLayouts/`)
The presentation contains **11 layout files**. Below is the mapping of filenames to their internal layout names (from the `<p:cSld name="...">` attribute):

| Layout File | Layout Name (cSld) | Description / Primary Elements |
|---|---|---|
| `slideLayout1.xml` | `Title Slide` | Title, Subtitle, Date, Footer, Slide Number placeholders |
| `slideLayout2.xml` | `Title and Content` | Title, Content, Date, Footer, Slide Number placeholders |
| `slideLayout3.xml` | `Section Header` | Title, Text, Date, Footer, Slide Number placeholders |
| `slideLayout4.xml` | `Two Content` | Title, Content (x2), Date, Footer, Slide Number placeholders |
| `slideLayout5.xml` | `Comparison` | Title, Text (x2), Content (x2), Date, Footer, Slide Number |
| `slideLayout6.xml` | `Title Only` | Title, Date, Footer, Slide Number placeholders |
| `slideLayout7.xml` | `Blank` | Date, Footer, Slide Number placeholders (Used by Slide 1) |
| `slideLayout8.xml` | `Content with Caption` | Title, Content, Text, Date, Footer, Slide Number placeholders |
| `slideLayout9.xml` | `Picture with Caption` | Title, Picture, Text, Date, Footer, Slide Number placeholders |
| `slideLayout10.xml` | `Title and Vertical Text` | Title, Vertical Text, Date, Footer, Slide Number placeholders |
| `slideLayout11.xml` | `Vertical Title and Text` | Vertical Title, Vertical Text, Date, Footer, Slide Number |

---

## 5. Unpacked Slide Files (`ppt/slides/`)
* `/ppt/slides/slide1.xml` (the only slide in the template)
