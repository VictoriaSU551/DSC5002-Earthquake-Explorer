"""Build searchable A0 poster and presentation notes with ReportLab + pypdf.

Run with a Python environment containing reportlab, pypdf and Pillow, after
run_final.py, build_poster_charts.py and final_browser_smoke.cjs.
"""
from pathlib import Path
from io import BytesIO
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor,white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,SimpleDocTemplate,Spacer,KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from pypdf import PdfReader,PdfWriter,Transformation
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/final'
DEL=ROOT/'deliverables';DEL.mkdir(exist_ok=True)
FONT=Path('C:/Windows/Fonts')
if (FONT/'arial.ttf').exists():
    pdfmetrics.registerFont(TTFont('Body',str(FONT/'arial.ttf')))
    pdfmetrics.registerFont(TTFont('Body-Bold',str(FONT/'arialbd.ttf')))
else:
    from reportlab.pdfbase.pdfmetrics import Font
    pdfmetrics.registerFont(Font('Body','Helvetica','WinAnsiEncoding'))
    pdfmetrics.registerFont(Font('Body-Bold','Helvetica-Bold','WinAnsiEncoding'))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body',boldItalic='Body-Bold')
W,H=1189*mm,841*mm
NAVY='#16364b';TEAL='#167d8d';BLUE='#2166ac';MUTED='#516979';GOLD='#cc8b19'
SITE='https://VictoriaSU551.github.io/DSC5002-Earthquake-Explorer/'
REPO='https://github.com/VictoriaSU551/DSC5002-Earthquake-Explorer'
charts=[];boxes=[]
buf=BytesIO();c=canvas.Canvas(buf,pagesize=(W,H));c.setTitle('Inside the Earth: Global earthquake patterns in space, time and depth');c.setAuthor('DSC5002 Project Team');c.setSubject('USGS 2000-2025 M >= 5; integrated research poster')
def rect(x,y,w,h,color):
    c.setFillColor(HexColor(color));c.rect(x*mm,H-(y+h)*mm,w*mm,h*mm,fill=1,stroke=0)
def text(s,x,y,size=26,color=NAVY,bold=False):
    c.setFillColor(HexColor(color));c.setFont('Body-Bold' if bold else 'Body',size);c.drawString(x*mm,H-y*mm,s)
def para(s,x,y,w,h,size=25,color=NAVY,bold=False):
    style=ParagraphStyle('p',fontName='Body-Bold' if bold else 'Body',fontSize=size,leading=size*1.25,textColor=HexColor(color),spaceAfter=0)
    p=Paragraph(s,style);pw,ph=p.wrap(w*mm,h*mm)
    if ph>h*mm+.1:raise ValueError(f'Text overflow: {s[:80]} {ph/mm:.1f}>{h}')
    p.drawOn(c,x*mm,H-y*mm-ph);boxes.append({'text':s[:80],'height_mm':ph/mm,'allocation_mm':h})
def section(number,title,x,y,w):
    rect(x,y-8,10,10,TEAL);text(number,x+2,y-.7,20,'#ffffff',True);text(title,x+15,y,32,NAVY,True)
    rect(x,y+4,w,.6,'#dbe5ea')
def chart(name,x,y,w,h):
    charts.append((name,x,y,w,h))
def link(label,url,x,y,w,size=22):
    text(label,x,y,size,TEAL,True);c.linkURL(url,(x*mm,H-(y+2)*mm,(x+w)*mm,H-(y-9)*mm),relative=0,thickness=0)

rect(0,0,1189,841,'#ffffff');rect(0,0,1189,116,NAVY)
text('INSIDE THE EARTH',24,45,88,'#ffffff',True)
text('Global earthquake patterns in space, time and depth',25,70,43,'#e2f1f5')
text('DSC5002 Project Team  |  City University of Hong Kong  |  Exploratory Data Analysis and Visualization',25,94,24,'#c7dce5')
rect(964,23,201,68,'#254d62')
text('2000–2025',977,46,45,'#ffffff',True)
text('M ≥ 5  •  UTC  •  Earthquakes only',977,64,22,'#d9edf2')
text('One frozen catalogue across all panels',977,79,20,'#d9edf2')

rect(24,126,1141,57,'#eff5f7')
metrics=[('46,463','unique earthquake records'),('70.15%','within 100 km of a PB2002 boundary'),('83.20%','shallow events (<70 km)')]
for x,(a,b) in zip([37,423,809],metrics):
    text(a,x,151,51,TEAL,True);text(b,x,169,25,NAVY)

x1,x2,x3=24,411,798;cw=367
section('1','INTRODUCTION & METHODS',x1,205,cw)
para('A global map alone hides variation through time and below the surface. We connect five questions: <b>where and when, boundary proximity, depth, magnitude frequency, and major-event sequences.</b>',x1,217,cw,40,25)
para('<b>Data:</b> USGS earthquake-only catalogue [1], 1 Jan 2000 to 31 Dec 2025; preferred M ≥ 5. Event IDs are unique; four negative reported depths are retained. PB2002 [2] supplies 241 boundary features; Natural Earth [3] supplies map context.',x1,261,cw,43,24)
para('<b>Methods:</b> shortest spherical distance to boundary arcs (R = 6,371.0088 km); six geographic boxes plus Other; full-sample statistics; equal 13-year comparisons adjusted for 4,749 versus 4,748 days. No prediction model.',x1,308,cw,40,24)

section('2','WHERE ARE THE EVENTS?  ·  RQ1–2',x1,365,cw)
chart('global_map',x1,377,cw,177)
para('<b>Figure 1.</b> All 46,463 epicentres; points coloured by depth. Grey lines show PB2002 boundaries. The circum-Pacific pattern is prominent. Overplotting indicates concentration, not an area-normalized risk estimate.',x1,557,cw,36,22)
section('3','HOW CLOSE TO BOUNDARIES?  ·  RQ2',x1,611,cw)
chart('boundary_cdf',x1,623,cw,134)
para('<b>Figure 2.</b> Median distance = <b>59.68 km</b>; 70.15% lie within 100 km. These are distances to a simplified, dated map layer, not to every active fault. No spatial null model was fitted.',x1,759,cw,31,22)

section('4','RECORDED ACTIVITY OVER TIME  ·  RQ1',x2,205,cw)
chart('annual',x2,218,cw,124)
para('<b>Figure 3.</b> Annual M ≥ 5 counts; dashed lines are period means. The maximum is 2,701 in 2011. Later-period recorded rate: <b>−6.63% at M ≥ 5</b>, <b>−15.42% at M ≥ 6</b>. These are descriptive comparisons, not a monotonic trend.',x2,345,cw,40,23)

section('5','REGIONAL CHANGES  ·  RQ1',x2,404,cw)
chart('regional_change',x2,417,cw,140)
para('<b>Figure 4.</b> 2013–2025 versus 2000–2012, M ≥ 5; equal exposure rates. Indonesia/Philippines decreases 25.58%; Mediterranean/Himalaya increases 8.82%. Boxes differ in area and do not define tectonic plates.',x2,561,cw,36,22)

section('6','DEPTH DIFFERS BY REGION  ·  RQ3',x2,616,cw)
chart('depth_shares',x2,630,cw,118)
para('<b>Figure 5.</b> Shallow &lt;70, intermediate 70–&lt;300, deep ≥300 km. Tonga/Kermadec/Fiji has <b>11.76% deep</b> events versus Japan/Kuril 5.01%; Andes has 26.19% intermediate. Each row uses its own known-depth denominator.',x2,752,cw,36,22)

section('7','MAGNITUDE & FREQUENCY  ·  RQ4',x3,205,cw)
chart('magnitude',x3,216,cw,85)
para('<b>Figure 6.</b> Histogram and inclusive cumulative counts (log axis): M ≥ 6: <b>3,874</b>; M ≥ 7: <b>387</b>; M ≥ 8: <b>28</b>. Mixed magnitude types are not homogenized; M5 completeness is not established.',x3,304,cw,31,22)

section('8','LOCAL DEPTH SECTIONS  ·  RQ3',x3,352,cw)
chart('cross_sections',x3,363,cw,85)
para('<b>Figure 7.</b> ±100 km finite swaths; zero at the mapped trench. Equal kilometre scales, depth positive downward. Deep events: Tohoku <b>21/351</b>, Tonga <b>186/640</b>. Routes were explored and selected; profiles are illustrative.',x3,451,cw,31,22)

section('9','MAJOR-EVENT SEQUENCES  ·  RQ5',x3,499,cw)
chart('case_timelines',x3,510,cw,93)
para('<b>Figure 8.</b> Fixed 500 km, ±30-day windows; anchors excluded. First 3 post-event days contain <b>60.1%, 60.9%, 70.9%</b> of post-window counts. Shared y-scale; blue = before, gold = after.',x3,606,cw,28,22)

link('PLAY THE ANIMATION  >  (click here or the image)',SITE,x3,651,cw,23)
text('VictoriaSU551.github.io/DSC5002-Earthquake-Explorer/',x3,663,18,TEAL)
im=OUT/'animation_poster_keyframe.png'
iw,ih=Image.open(im).size
imgw=cw;imgh=min(111,cw*ih/iw);actualw=imgh*iw/ih
ix=x3+(cw-actualw)/2
c.drawImage(str(im),ix*mm,H-(667+imgh)*mm,width=actualw*mm,height=imgh*mm,preserveAspectRatio=True)
c.linkURL(SITE,(ix*mm,H-(667+imgh)*mm,(ix+actualw)*mm,H-667*mm),relative=0,thickness=0)
para('<b>Figure 9.</b> Actual animation keyframe at +3 days, cumulative mode. Full interactive companion includes play, time slider and 7-day trailing windows.',x3,781,cw,17,19)

rect(24,802,1141,21,NAVY)
para('<b>CONCLUSION & LIMITS</b>  Boundary proximity and depth structure are clear catalogue patterns. Cross-period counts need caution: Mw-family share changes from 73.45% to 55.05%, and reporting fields change. These results do not establish causality, completeness or future hazard.',31,805,1127,16,23,'#ffffff')
para('[1] USGS FDSN Event Web Service: earthquake.usgs.gov/fdsnws/event/1/  ·  [2] Bird (2003), doi:10.1029/2001GC000252; PB2002 GeoJSON, ODC-By  ·  [3] Natural Earth 110m, public domain.',24,828,1141,8,16,MUTED)
for a,b,url in [(24,390,'https://earthquake.usgs.gov/fdsnws/event/1/'),(416,850,'https://doi.org/10.1029/2001GC000252'),(886,1165,'https://www.naturalearthdata.com/')]:c.linkURL(url,(a*mm,3*mm,b*mm,13*mm),relative=0,thickness=0)
c.showPage();c.save();buf.seek(0)
reader=PdfReader(buf);page=reader.pages[0]
for name,x,y,w,h in charts:
    source=PdfReader(OUT/'poster_charts'/(name+'.pdf')).pages[0]
    sw,sh=float(source.mediabox.width),float(source.mediabox.height)
    scale=min(w*mm/sw,h*mm/sh)
    xx=x*mm+(w*mm-sw*scale)/2;yy=H-(y+h)*mm+(h*mm-sh*scale)/2
    page.merge_transformed_page(source,Transformation().scale(scale).translate(xx,yy))
writer=PdfWriter();writer.add_page(page);writer.add_metadata({'/Title':'Inside the Earth | DSC5002 Academic Poster','/Author':'DSC5002 Project Team','/Subject':'Searchable A0 landscape; source-backed charts and linked animation'})
with (DEL/'DSC5002_Academic_Poster.pdf').open('wb') as f:writer.write(f)
(OUT/'poster_layout_checks.json').write_text(json.dumps({'text_boxes':boxes,'charts':len(charts),'page_mm':[1189,841],'animation_link':SITE},indent=2),encoding='utf-8')
print('Created searchable A0 poster with eight vector charts and an actual animation screenshot.')

# Presentation script: source-informed signposting without copying the sample's story.
script=[
('Opening | introduce the research',"Hello, and thank you for stopping by. We are the DSC5002 project team at City University of Hong Kong. Our project is called Inside the Earth. When we see a cluster of earthquakes on a world map, what can that map tell us, and what is still hidden? We combined time, location, magnitude and depth to make those patterns easier to explore. Our goal is to describe the recorded catalogue, not to predict the next earthquake."),
('Methods | point to section 1',"First, we used a fixed USGS snapshot containing 46,463 unique earthquake records, from 2000 through 2025, with preferred magnitude at least five. All final analyses use the same records. We checked a teammate's larger extract and identified 60 non-earthquake events, so those were not part of our earthquake sample. We calculated spherical distances to PB2002 boundary arcs and used clearly specified regional boxes. For comparisons across time, we allowed for the one-day difference between the two thirteen-year periods."),
('Spatial results | point to sections 2 and 3',"The map on the left shows the familiar concentration around the Pacific and other mapped boundaries. The distance curve makes this more precise: 70.15 percent of the records lie within one hundred kilometres of a PB2002 boundary, and the median distance is 59.68 kilometres. This is a description of proximity to our selected map. It is not a test against a spatial null model, and PB2002 does not represent every active fault."),
('Time and regions | point to sections 4 and 5',"Next, the middle column shows how recorded counts vary through time. The annual maximum is 2,701 in 2011. Comparing 2013 to 2025 with 2000 to 2012, the exposure-adjusted rate is 6.63 percent lower at magnitude five or above, and 15.42 percent lower at magnitude six or above. Regional changes differ: Indonesia and the Philippines decrease by 25.58 percent, while the Mediterranean and Himalaya group increases by 8.82 percent. These are changes in catalogue counts. They should not be read as changes in hazard, especially because the regions differ in area."),
('Depth and magnitude | point to sections 6, 7 and 8',"Depth adds another dimension. Globally, 83.20 percent of the records are shallow. Yet the deep-event share is 11.76 percent in Tonga, Kermadec and Fiji, compared with 5.01 percent in Japan and Kuril. The two local profiles use the same distance and depth scales, with zero at the mapped trench. The Tonga profile contains 186 deep events out of 640, while the northern Tohoku profile contains 21 out of 351. These are selected local swaths, not representative samples of entire regions. The magnitude charts show that larger events are much less frequent: 387 records reach magnitude seven, and only 28 reach magnitude eight. We did not assume that the threshold proves catalogue completeness."),
('Sequences and animation | point to sections 9 and the linked frame',"Finally, we compared three major-event windows using the same five-hundred-kilometre radius and thirty days on each side, excluding the anchor itself. The after-window counts are 143 for Sumatra, 302 for Maule and 563 for Tohoku. Around sixty to seventy-one percent of those post-window records fall in the first three days. The linked animation lets us inspect their timing and geography together. This screenshot shows the actual cumulative frame at day three. The full-window histogram is displayed throughout, and the star marks the anchor's reference location even before time zero."),
('Conclusion | point to the bottom strip',"To conclude, the project makes boundary proximity, regional depth contrasts and event sequences visible within one consistent catalogue. The main caution is comparability. The composition of preferred magnitude types and the availability of reporting fields change over time, so a count difference alone cannot identify a physical change in earthquake activity. Our contribution is a reproducible, interactive description with those limits made explicit. Thank you for your attention. We would be happy to discuss the figures or demonstrate the animation.")]
styles={'title':ParagraphStyle('title',fontName='Body-Bold',fontSize=21,leading=26,textColor=HexColor(NAVY)),
'head':ParagraphStyle('head',fontName='Body-Bold',fontSize=12,leading=16,textColor=HexColor(TEAL),spaceBefore=12,spaceAfter=5),
'body':ParagraphStyle('body',fontName='Body',fontSize=11,leading=16,textColor=HexColor(NAVY))}
story=[Paragraph('Inside the Earth | Poster presentation script',styles['title']),Spacer(1,10),Paragraph('Suggested delivery: approximately 6–7 minutes at 115–130 words/minute. This is a rehearsal estimate, not a CityU course rule. Use the numbered poster panels as cues; the sample pages do not prescribe a duration.',styles['body'])]
for heading,body in script:story.append(KeepTogether([Paragraph(heading,styles['head']),Paragraph(body,styles['body'])]))
story.extend([Paragraph('Likely questions',styles['head']),Paragraph('<b>Why not 46,523?</b> The supplied all-type extract includes 60 non-earthquake records. The final catalogue is earthquake-only.<br/><br/><b>Why not fit a predictive b-value?</b> A lower extraction threshold does not establish completeness, and magnitude scales are mixed.<br/><br/><b>Are the post-window events proven aftershocks?</b> No. Membership is determined only by the stated time and epicentral-distance windows.<br/><br/><b>What does the colour mean?</b> For location and depth charts: blue shallow, gold intermediate, purple deep. In the timeline only: blue before, gold after; this encoding is stated beside that figure.',styles['body']),Paragraph('Presentation reference',styles['head']),Paragraph('CityU Language Centre: <link href="https://www.cityu.edu.hk/lc/app/poster-script-samples1.html" color="#167d8d">poster script sample</link>. We follow its introduction, signposting, methods, findings and closing structure; the research content and wording here are original.',styles['body'])])
doc=SimpleDocTemplate(str(DEL/'DSC5002_Presentation_Script.pdf'),pagesize=(210*mm,297*mm),rightMargin=22*mm,leftMargin=22*mm,topMargin=20*mm,bottomMargin=20*mm)
doc.build(story)
(DEL/'Presentation_Script.txt').write_text('\n\n'.join(h+'\n'+b for h,b in script),encoding='utf-8')
print('Created searchable presentation notes.')
