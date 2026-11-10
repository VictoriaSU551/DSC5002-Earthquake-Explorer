"""Build searchable A0 poster and presentation notes with ReportLab + pypdf.

Run with a Python environment containing reportlab, pypdf and Pillow, after
run_final.py, member3_analysis.py, expand_analysis.py and build_poster_charts.py.
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

# Current design: four aligned evidence columns, with no animation link.
expanded=json.loads((OUT/'expanded_facts.json').read_text())
r100=next(v for v in expanded['thresholds'] if v['radius_km']==100)
rect(0,0,1189,841,'#ffffff')
for x,col in zip([0,297.25,594.5,891.75],['#197c9e','#c95d54','#8254a6','#d58c27']):rect(x,0,297.25,5,col)
text('INSIDE THE EARTH',22,42,86,NAVY,True)
text('Reading global earthquakes through space, time, depth and magnitude',23,64,35,MUTED)
text('DSC5002 Project Team  |  City University of Hong Kong  |  USGS 2000–2025, preferred M ≥ 5',23,82,24,MUTED)
# Four compact findings replace the former oversized header.
metrics=[('46,463','unique earthquake records'),(f"{r100['observed_to_area_ratio']:.2f}×",'100-km share / equal-area reference'),('11.76%','deep events in Tonga / Kermadec / Fiji'),('28','events with magnitude ≥ 8')]
for x,(value,label),col in zip([22,312,602,892],metrics,['#197c9e','#c95d54','#8254a6','#b57919']):
 rect(x,94,275,43,'#f1f5f6');text(value,x+8,116,42,col,True);text(label,x+8,129,20,NAVY)
cols=[22,312,602,892];cw=275
for x,title,col in zip(cols,['01  SPACE & REFERENCE','02  TIME & COMPARABILITY','03  DEPTH & RELATIONSHIPS','04  MAGNITUDE & SEQUENCES'],['#197c9e','#c95d54','#8254a6','#b57919']):
 rect(x,146,cw,17,col);text(title,x+6,157,25,'#ffffff',True)
def heading(title,x,y):
 text(title,x,y,28,NAVY,True)
def cap(value,x,y,h=32):para(value,x,y,cw,h,22)
x=cols[0]
heading('Question, data and approach',x,180)
cap('Where are earthquakes concentrated, and what changes when we examine time and depth? We connect five research questions using one frozen, earthquake-only catalogue.',x,187,35)
cap('<b>Methods.</b> Unique IDs; UTC 2000–2025; M ≥ 5. Six geographic boxes plus Other. Distances to PB2002 minor great-circle arcs (R = 6,371 km); no automatic removal of extreme or negative depths.',x,225,42)
heading('Global geography',x,283)
chart('global_map',x,291,cw,116)
cap('<b>Fig. 1.</b> All 46,463 epicentres on an equal-area Mollweide map. Colours: shallow, intermediate and deep; grey lines: PB2002. Clusters follow the circum-Pacific belts; overlapping points are not an area-normalized density.',x,408,39)
heading('Concentrated relative to what?',x,463)
chart('boundary_cdf',x,470,cw,104)
cap(f"<b>Fig. 2.</b> Within 100 km: <b>70.15%</b> of events versus <b>{r100['equal_area_pct']:.2f}%</b> of equal-area globe points; latitude control <b>{r100['latitude_matched_pct']:.2f}%</b>. Four 16,384-point designs give {r100['replicate_min_pct']:.2f}–{r100['replicate_max_pct']:.2f}% (numerical sensitivity, not a CI).",x,577,46)
heading('Regional proximity is uneven',x,642)
chart('regional_proximity',x,650,cw,105)
cap('<b>Fig. 3.</b> Each region has its own denominator. Other is a heterogeneous residual category. Reference points cover land and ocean; this is a descriptive geographic baseline, not a seismicity null model.',x,758,39)

x=cols[1]
heading('A fluctuating recorded history',x,180)
chart('annual',x,188,cw,111)
cap('<b>Fig. 4.</b> Annual counts; dashed lines are 13-year means. The 2011 peak is <b>2,701</b>. Later-period rates are <b>6.63% lower at M ≥ 5</b> and <b>15.42% lower at M ≥ 6</b>, after allowing for 4,749 versus 4,748 days.',x,302,45)
heading('The direction depends on region',x,365)
chart('regional_change',x,373,cw,117)
cap('<b>Fig. 5.</b> 2013–2025 versus 2000–2012: Indonesia/Philippines <b>−25.58%</b>, Mediterranean/Himalaya <b>+8.82%</b>. Region boxes differ in area; these are within-region changes, not comparisons of hazard.',x,493,41)
heading('Can the periods be compared?',x,553)
chart('magnitude_mix',x,561,cw,104)
cap('<b>Fig. 6.</b> Mw-family share shifts from <b>73.45% to 55.05%</b> between periods. Preferred magnitude scales are mixed; selecting Mw records alone does not homogenize the catalogue.',x,668,37)
rect(x,718,cw,77,'#f8f0ee')
para('<b>Reporting and sensitivity</b><br/>Horizontal-error availability: <b>0.28% → 86.80%</b>. Missing does not mean zero error.<br/>Removing 30-day / 500-km windows around 28 M ≥ 8 events changes the M5 contrast to <b>−3.37%</b>. This is a window sensitivity, not declustering.',x+7,724,cw-14,65,22)

x=cols[2]
heading('Similar medians, different tails',x,180)
chart('depth_shares',x,188,cw,112)
cap('<b>Fig. 7.</b> Globally <b>83.20%</b> are shallow (&lt;70 km). Japan/Kuril and Tonga/Fiji both have median depth 33 km, but deep-event shares are <b>5.01% and 11.76%</b>. Andes has <b>26.19%</b> intermediate events.',x,303,42)
heading('Local sections reveal structure',x,363)
chart('cross_sections',x,371,cw,182)
cap('<b>Fig. 8.</b> Maps: gold trench, blue route/swath, star at 0 km. A → B: −200 to +1,200 km; ±100 km swaths, equal kilometre scales. Deep events: <b>21/351</b> in northern Tohoku; <b>186/640</b> in central Tonga. Routes were selected after exploration.',x,556,50)
heading('Pooled and regional associations',x,626)
chart('correlations',x,634,cw,126)
cap('<b>Fig. 9.</b> Pairwise Spearman ρ, all eligible records. Depth–distance association is +0.39 overall and +0.56 in Japan/Kuril; magnitude associations are weak. Correlation does not identify causality.',x,763,37)

x=cols[3]
heading('Large events are much rarer',x,180)
chart('magnitude',x,188,cw,103)
cap('<b>Fig. 10.</b> Inclusive N(M ≥ m), log count axis: <b>3,874</b> records ≥6; <b>387</b> ≥7; <b>28</b> ≥8. The M5 extraction threshold does not establish catalogue completeness; no predictive b-value is fitted.',x,294,39)
heading('Counts are not an energy scale',x,352)
chart('energy_scale',x,360,cw,103)
cap('<b>Fig. 11.</b> M ≥ 8 accounts for <b>0.06%</b> of events but <b>71.21%</b> of the summed illustrative proxy, R(M)=10<super>1.5(M−5)</super>. A unit increase multiplies R by 31.6. Mixed scales: not measured joules, damage or risk.',x,466,43)
heading('Sequences through a fixed window',x,527)
chart('case_timelines',x,535,cw,115)
cap('<b>Figs. 12–13.</b> Within 500 km and ±30 days; anchors excluded. Gold: post-event; blue: pre-event. First three days contain <b>60.1%, 60.9%, 70.9%</b> of post-window counts. Each cumulative curve uses its own 30-day total as denominator.',x,653,44)
chart('case_cumulative',x,701,cw,95)

rect(22,808,1145,17,NAVY)
para('<b>CONCLUSION</b>  Strong boundary concentration, contrasting depth tails and clustered sequences emerge. Their interpretation depends on the geographic reference, catalogue composition and window definition; none estimates future hazard.',28,811,1133,13,21,'#ffffff')
para('[1] <link href="https://earthquake.usgs.gov/fdsnws/event/1/">USGS FDSN Event Service</link>  ·  [2] <link href="https://doi.org/10.1029/2001GC000252">Bird (2003), PB2002</link>; GeoJSON (ODC-By)  ·  [3] <link href="https://www.naturalearthdata.com/">Natural Earth 110m</link> (public domain)  ·  [4] <link href="https://www.usgs.gov/programs/earthquake-hazards/earthquake-magnitude-energy-release-and-shaking-intensity">USGS magnitude–energy guidance</link>.  Full methods and sensitivity results: <link href="'+REPO+'">project repository</link>.',22,831,1145,8,17,MUTED)
c.showPage();c.save();buf.seek(0)
reader=PdfReader(buf);page=reader.pages[0]
for name,x,y,w,h in charts:
    source=PdfReader(OUT/'poster_charts'/(name+'.pdf')).pages[0]
    sw,sh=float(source.mediabox.width),float(source.mediabox.height)
    scale=min(w*mm/sw,h*mm/sh)
    xx=x*mm+(w*mm-sw*scale)/2;yy=H-(y+h)*mm+(h*mm-sh*scale)/2
    page.merge_transformed_page(source,Transformation().scale(scale).translate(xx,yy))
writer=PdfWriter();writer.add_page(page);writer.add_metadata({'/Title':'Inside the Earth | DSC5002 Academic Poster','/Author':'DSC5002 Project Team','/Subject':'Searchable A0 landscape; four columns, 13 evidence figures and geographic controls'})
with (DEL/'DSC5002_Academic_Poster.pdf').open('wb') as f:writer.write(f)
(OUT/'poster_layout_checks.json').write_text(json.dumps({'text_boxes':boxes,'charts':len(charts),'page_mm':[1189,841],'animation_link':None,'columns':4},indent=2),encoding='utf-8')
print('Created current four-column A0 poster; 13 static evidence figures, no animation link.')

# Presentation script: source-informed signposting without copying the sample's story.
script=[
('Opening | four connected views',"Hello. We are the DSC5002 project team at City University of Hong Kong. Inside the Earth asks how earthquake patterns change when we look at space, time, depth and magnitude together. Please read the four columns from left to right. We use 46,463 unique USGS earthquake records from 2000 to 2025, all with preferred magnitude at least five. We aim to describe recorded patterns with explicit reference points, not to predict future earthquakes."),
('Column 1 | space and reference',f"The equal-area world map shows geographic concentration. But a map alone does not say how unusual proximity to boundaries is relative to available surface area. We therefore generated 65,536 equal-area reference locations on the whole globe, including oceans, and calculated the same spherical distance to PB2002 boundaries. Within one hundred kilometres, the observed share is 70.15 percent, compared with {r100['equal_area_pct']:.2f} percent for the geographic reference. Their ratio is {r100['observed_to_area_ratio']:.2f}. A second reference preserves the observed latitude distribution while randomizing longitude; its share is {r100['latitude_matched_pct']:.2f} percent. These controls help interpret concentration, but neither is a realistic model of earthquake occurrence. We make no causal or significance claim from the ratio."),
('Column 2 | time and comparability',"The second column combines trends with reasons for caution. Recorded activity fluctuates, with 2,701 events in 2011. Comparing the later thirteen years with the earlier thirteen years, the exposure-adjusted rate is 6.63 percent lower at magnitude five and 15.42 percent lower at magnitude six. The regional chart shows that the direction differs: Indonesia and the Philippines decrease by 25.58 percent, whereas the Mediterranean and Himalaya group increases by 8.82 percent. The next chart shows why those numbers should not stand alone. Mw-family composition changes from 73.45 to 55.05 percent. Horizontal-error availability changes sharply too. Removing fixed windows around the largest events reduces the M5 contrast to minus 3.37 percent; this is a sensitivity exercise, not declustering."),
('Column 3 | depth and relationships',"The third column moves below the surface. Most events are shallow, but similar medians hide different tails. Japan and Kuril and Tonga, Kermadec and Fiji both have median depth thirty-three kilometres, yet their deep shares differ, at 5.01 and 11.76 percent. The local cross sections use equal kilometre scales, a fixed swath and zero at the mapped trench. Tonga has 186 deep events out of 640 in the selected swath, compared with 21 out of 351 in northern Tohoku. The correlation heatmap then connects depth to boundary distance across the complete regions. The overall rank correlation is about 0.39 and is stronger in Japan and Kuril. Magnitude correlations are generally weak. These are observational relationships, not causal mechanisms identified by this analysis."),
('Column 4 | magnitude and event sequences',"The last column separates event frequency from an illustrative energy scale. There are only twenty-eight events of magnitude eight or more. They represent 0.06 percent of records but about 71.21 percent of a summed magnitude-based proxy. That proxy increases by about thirty-two for each unit of magnitude. Because preferred magnitude scales are mixed, it is not measured energy in joules and it does not measure damage. Finally, the daily timelines and cumulative curves compare three events within the same five-hundred-kilometre and thirty-day windows. Anchors are excluded. Roughly sixty to seventy-one percent of each post-window sample appears in the first three days. Static aligned panels communicate both the total counts and the timing directly, so an animation link is unnecessary on this poster. The supplementary sensitivity grid shows how counts change when we change the radius and duration."),
('Conclusion | what the evidence supports',"Together, the four columns show strong concentration near mapped boundaries, regional differences in depth, rare high magnitudes and clustered event sequences. They also show how conclusions depend on the reference geography, catalogue composition and selected windows. Our contribution is to make those comparisons visible and reproducible while keeping their limitations explicit. Thank you for your attention. We would be happy to discuss the geographic reference or demonstrate the companion interactive analysis.")]
styles={'title':ParagraphStyle('title',fontName='Body-Bold',fontSize=21,leading=26,textColor=HexColor(NAVY)),
'head':ParagraphStyle('head',fontName='Body-Bold',fontSize=12,leading=16,textColor=HexColor(TEAL),spaceBefore=10,spaceAfter=4),
'body':ParagraphStyle('body',fontName='Body',fontSize=11,leading=14.5,textColor=HexColor(NAVY))}
story=[Paragraph('Inside the Earth | Poster presentation script',styles['title']),Spacer(1,10),Paragraph('Suggested delivery: approximately 6–7 minutes including pauses to point to the figures. This is a rehearsal estimate, not a CityU course rule. Use the numbered poster panels as cues; the sample pages do not prescribe a duration.',styles['body'])]
for heading,body in script:story.append(KeepTogether([Paragraph(heading,styles['head']),Paragraph(body,styles['body'])]))
story.extend([Paragraph('Likely questions',styles['head']),Paragraph('<b>Why not 46,523?</b> The supplied all-type extract includes 60 non-earthquake records. The final catalogue is earthquake-only.<br/><br/><b>Why not fit a predictive b-value?</b> A lower extraction threshold does not establish completeness, and magnitude scales are mixed.<br/><br/><b>Are the post-window events proven aftershocks?</b> No. Membership is determined only by the stated time and epicentral-distance windows.<br/><br/><b>What does the colour mean?</b> For location and depth charts: blue shallow, gold intermediate, purple deep. In the timeline only: blue before, gold after; this encoding is stated beside that figure.',styles['body']),Paragraph('Presentation reference',styles['head']),Paragraph('CityU Language Centre: <link href="https://www.cityu.edu.hk/lc/app/poster-script-samples1.html" color="#167d8d">poster script sample</link>. We follow its introduction, signposting, methods, findings and closing structure; the research content and wording here are original.',styles['body'])])
doc=SimpleDocTemplate(str(DEL/'DSC5002_Presentation_Script.pdf'),pagesize=(210*mm,297*mm),rightMargin=22*mm,leftMargin=22*mm,topMargin=20*mm,bottomMargin=20*mm)
doc.build(story)
(DEL/'Presentation_Script.txt').write_text('\n\n'.join(h+'\n'+b for h,b in script),encoding='utf-8')
print('Created searchable presentation notes.')
