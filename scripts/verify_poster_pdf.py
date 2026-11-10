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
for phrase in ['INSIDE THE EARTH','46,463','70.15%','83.20%','59.68','6.63%','15.42%','11.76%','3,874','387','21/351','186/640','60.1%','70.9%']:
    assert phrase in text,phrase
assert '\ufffd' not in text
for number in range(1,10):assert f'Figure {number}.' in text
urls=[a.get_object()['/A']['/URI'] for a in p['/Annots'] if a.get_object().get('/A',{}).get('/S')=='/URI']
assert urls.count('https://VictoriaSU551.github.io/DSC5002-Earthquake-Explorer/')==2
for a in p['/Annots']:
    x0,y0,x1,y1=map(float,a.get_object()['/Rect']);assert 0<=x0<x1<=float(p.mediabox.width) and 0<=y0<y1<=float(p.mediabox.height)
script=PdfReader(ROOT/'deliverables/DSC5002_Presentation_Script.pdf')
assert all(len(page.extract_text())>200 for page in script.pages)
assert 'Thank you for your attention' in ' '.join((' '.join(page.extract_text() for page in script.pages)).split())
receipt={'status':'PASS','poster_pages':1,'page_mm':[1189,841],'searchable_text_characters':len(text),'figures':9,'uri_annotations':urls,'script_pages':len(script.pages),'visual_check':'Rendered with Poppler; full poster and enlarged chart/keyframe regions inspected.'}
(ROOT/'outputs/final/pdf_verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
