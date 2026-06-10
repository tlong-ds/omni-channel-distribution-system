# PPTX Skill Copy

Instructions for handling .pptx files in this environment.

## Reading Content
- Text extraction: `python -m markitdown presentation.pptx`
- Visual overview: `python scripts/thumbnail.py presentation.pptx`
- Raw XML: `python scripts/office/unpack.py presentation.pptx unpacked/`

## QA (Required)
Check for missing content, typos, wrong order, and placeholder text:
`python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"`
Convert slides to images:
`python scripts/office/soffice.py --headless --convert-to pdf output.pptx`
`pdftoppm -jpeg -r 150 output.pdf slide`
And inspect visually.
