"""Reopen authored PDFs and verify searchability, page geometry and links."""
from pathlib import Path
import json
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
poster=PdfReader(ROOT/'deliverables/DSC5002_Academic_Poster.pdf')
p=poster.pages[0];text=p.extract_text()
assert len(poster.pages)==1
assert abs(float(p.mediabox.width)*25.4/72-1189)<.01
assert abs(float(p.mediabox.height)*25.4/72-841)<.01
for phrase in ['INSIDE THE EARTH','ABSTRACT','CONCLUSION','46,463','70.15%','9.42%','10.50%','7.45','83.20%','6.63%','15.42%','11.76','21/351','186/640','60.1','70.9','71.21%','STUDY DESIGN','SPACE & REFERENCE','TIME & COMPARABILITY','DEPTH & ASSOCIATIONS','MAGNITUDE & SEQUENCES','24,030','22,433','42,589','3,487']:
    assert phrase in text,phrase
assert '\ufffd' not in text
for number in range(1,6):assert f'Fig. {number}.' in text
for number in range(1,7):assert f'Table {number}.' in text
assert 'Fig. 6.' not in text
layout=json.loads((ROOT/'outputs/final/poster_layout_checks.json').read_text())
assert layout['columns']==5 and len(layout['tables'])==6 and len(layout['charts'])==5
for table in layout['tables']:
    for row in table['rows']:
        for value in row:assert str(value).replace('\n',' ') in text.replace('\n',' '),value
# Text, chart and table allocations may not overlap in the same column.
blocks=layout['text_boxes']+layout['charts']+layout['tables']
for i,a in enumerate(blocks):
    assert 0<=a['x_mm'] and 0<=a['y_mm'] and a['x_mm']+a['width_mm']<=1189 and a['y_mm']+a['height_mm']<=841
    for b in blocks[i+1:]:
        dx=min(a['x_mm']+a['width_mm'],b['x_mm']+b['width_mm'])-max(a['x_mm'],b['x_mm'])
        dy=min(a['y_mm']+a['height_mm'],b['y_mm']+b['height_mm'])-max(a['y_mm'],b['y_mm'])
        assert dx<.1 or dy<.1,('Overlapping allocated blocks',a,b)
urls=[a.get_object()['/A']['/URI'] for a in p['/Annots'] if a.get_object().get('/A',{}).get('/S')=='/URI']
assert len(urls)==5 and not any('animation' in u or 'github.io' in u for u in urls)
for a in p['/Annots']:
    x0,y0,x1,y1=map(float,a.get_object()['/Rect']);assert 0<=x0<x1<=float(p.mediabox.width) and 0<=y0<y1<=float(p.mediabox.height)
script=PdfReader(ROOT/'deliverables/DSC5002_Presentation_Script.pdf')
assert all(len(page.extract_text())>200 for page in script.pages)
assert 'Thank you for your attention' in ' '.join((' '.join(page.extract_text() for page in script.pages)).split())
receipt={'status':'PASS','poster_pages':1,'page_mm':[1189,841],'columns':5,'searchable_text_characters':len(text),'figures':5,'tables':6,'table_values_extractable':True,'allocated_blocks_no_overlap':True,'uri_annotations':urls,'animation_links':0,'script_pages':len(script.pages),'visual_check':'Separate manual Poppler render inspection documented in FINAL_VALIDATION.md.'}
(ROOT/'outputs/final/pdf_verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
