"""Searchable A0 poster: five columns, narrative, six data tables, five figures.

Run after run_final.py, member3_analysis.py, expand_analysis.py and
build_poster_charts.py. Requires ReportLab, pypdf and Pillow, not pandas.
"""
from pathlib import Path
from io import BytesIO
import csv,json
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,SimpleDocTemplate,Spacer,KeepTogether,Table,TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from pypdf import PdfReader,PdfWriter,Transformation

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/final';DEL=ROOT/'deliverables';DEL.mkdir(exist_ok=True)
FONT=Path('C:/Windows/Fonts')
if (FONT/'arial.ttf').exists():
    pdfmetrics.registerFont(TTFont('Body',str(FONT/'arial.ttf')))
    pdfmetrics.registerFont(TTFont('Body-Bold',str(FONT/'arialbd.ttf')))
else:
    from reportlab.pdfbase.pdfmetrics import Font
    pdfmetrics.registerFont(Font('Body','Helvetica','WinAnsiEncoding'))
    pdfmetrics.registerFont(Font('Body-Bold','Helvetica-Bold','WinAnsiEncoding'))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body',boldItalic='Body-Bold')
W,H=1189*mm,841*mm;CW=217;COLS=[22,254,486,718,950]
NAVY='#123346';MUTED='#506875';TEAL='#197c9e';CORAL='#bb6258';PURPLE='#8056a2';GOLD='#a8781e'
REPO='https://github.com/VictoriaSU551/DSC5002-Earthquake-Explorer'
charts=[];boxes=[];tables=[]
buf=BytesIO();c=canvas.Canvas(buf,pagesize=(W,H))
c.setTitle('Inside the Earth | Evidence across space, time and depth');c.setAuthor('DSC5002 Project Team')

def rect(x,y,w,h,color):
    c.setFillColor(HexColor(color));c.rect(x*mm,H-(y+h)*mm,w*mm,h*mm,fill=1,stroke=0)

def text(s,x,y,size=25,color=NAVY,bold=False):
    c.setFillColor(HexColor(color));c.setFont('Body-Bold' if bold else 'Body',size)
    assert pdfmetrics.stringWidth(s,'Body-Bold' if bold else 'Body',size)<=(1189-x)*mm,s
    c.drawString(x*mm,H-y*mm,s)

def para(s,x,y,w,h,size=22,color=NAVY):
    style=ParagraphStyle('p',fontName='Body',fontSize=size,leading=size*1.25,textColor=HexColor(color))
    p=Paragraph(s,style);pw,ph=p.wrap(w*mm,h*mm)
    if ph>h*mm+.1:raise ValueError(f'Text overflow: {s[:65]} {ph/mm:.1f}>{h}')
    p.drawOn(c,x*mm,H-y*mm-ph);boxes.append({'text':s,'x_mm':x,'y_mm':y,'width_mm':w,'height_mm':ph/mm,'allocation_mm':h,'font_pt':size})

def heading(s,x,y,size=25):
    assert pdfmetrics.stringWidth(s,'Body-Bold',size)<=CW*mm,s
    text(s,x,y,size,NAVY,True)

def body(s,x,y,h,size=22):para(s,x,y,CW,h,size)

def figure(name,x,y,h):charts.append((name,x,y,CW,h))

def callout(title,s,x,y,h,color,tint):
    rect(x,y,CW,h,tint);rect(x,y,2,h,color)
    para('<b>'+title+'</b>',x+6,y+5,CW-12,13,22,color)
    para(s,x+6,y+19,CW-12,h-23,20)

def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))

def data_table(number,headers,rows,widths,x,y,maxheight,color=NAVY):
    cells=[]
    for i,row in enumerate([headers]+rows):
        line=[]
        for j,value in enumerate(row):
            style=ParagraphStyle('cell',fontName='Body-Bold' if i==0 else 'Body',fontSize=18 if i==0 else 19,
                leading=23,textColor=HexColor('#ffffff' if i==0 else NAVY),alignment=0 if j==0 or number==1 else 2)
            line.append(Paragraph(escape(str(value)).replace('\n','<br/>'),style))
        cells.append(line)
    t=Table(cells,colWidths=[v*mm for v in widths],hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor(color)),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),3*mm),('RIGHTPADDING',(0,0),(-1,-1),3*mm),
        ('TOPPADDING',(0,0),(-1,-1),3*mm),('BOTTOMPADDING',(0,0),(-1,-1),3*mm),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#eef3f5'),HexColor('#ffffff')]),
        ('LINEBELOW',(0,-1),(-1,-1),.65,HexColor('#a8bbc5'))]))
    tw,th=t.wrap(CW*mm,maxheight*mm)
    assert abs(tw/mm-CW)<.01 and th/mm<=maxheight,(number,th/mm,maxheight)
    t.drawOn(c,x*mm,H-y*mm-th)
    tables.append({'number':number,'headers':headers,'rows':rows,'x_mm':x,'y_mm':y,'width_mm':CW,'height_mm':th/mm})

expanded=json.loads((OUT/'expanded_facts.json').read_text());facts=json.loads((OUT/'poster_facts.json').read_text())
refs=read_csv(OUT/'tables/spatial_reference_summary.csv');r100=next(r for r in refs if r['radius_km']=='100')
regions=read_csv(OUT/'tables/regional_summary.csv');depth=read_csv(OUT/'tables/member3_region_summary.csv')
period=next(r for r in read_csv(ROOT/'docs/temporal_regional_v2/tables/equal_period_comparison.csv') if r['region']=='All' and float(r['threshold'])==5)
bands=read_csv(OUT/'rq4/tables/magnitude_band_summary.csv');cases=read_csv(OUT/'tables/case_comparison.csv')

# Editorial hierarchy: abstract, five evidence columns, shared conclusion.
rect(0,0,1189,841,'#ffffff')
colors=[NAVY,TEAL,CORAL,PURPLE,GOLD]
for i,col in enumerate(colors):rect(i*237.8,0,237.8,5,col)
text('INSIDE THE EARTH',22,41,86,NAVY,True)
text('Interpreting earthquake patterns through geography, time, depth and magnitude',23,63,32,MUTED)
text('DSC5002 Project Team  |  City University of Hong Kong  |  USGS catalogue, 2000–2025',23,81,24,MUTED)
rect(22,94,1145,38,'#eef3f5')
para('<b>ABSTRACT</b>  We examine 46,463 M ≥ 5 earthquakes using geographic reference points, equal-duration time comparisons and local depth sections. Events concentrate near mapped plate boundaries, but period differences also coincide with changes in catalogue composition. Regional depth tails and selected event sequences reveal structure that pooled summaries conceal. Our results describe a fixed catalogue; they do not estimate future hazard.',29,99,1131,28,24)
headers=['01  STUDY DESIGN','02  SPACE & REFERENCE','03  TIME & COMPARABILITY','04  DEPTH & ASSOCIATIONS','05  MAGNITUDE & SEQUENCES']
for x,title,col in zip(COLS,headers,colors):
    rect(x,145,CW,17,col);text(title,x+5,156,22,'#ffffff',True)
for x in [246.5,478.5,710.5,942.5]:rect(x,174,.35,614,'#dfe7ea')

# Column 1: narrative motivation + design table + a map.
x=COLS[0]
heading('Why combine these views?',x,180)
body('Earthquakes vary in location, depth, magnitude and timing. A map identifies clusters, yet it cannot explain whether they reflect geography, a few large sequences or changes in reporting. We connect these views to ask where recorded activity concentrates, how it varies over time, and which regional structures survive beyond global averages.',x,190,72)
heading('Table 1. Common analysis design',x,283,23)
data_table(1,['Element','Definition'],[
    ['Window','2000–2025 UTC'],['Selection','Earthquake; preferred M ≥ 5'],['Observations','46,463 unique event IDs'],
    ['Regions','6 ordered boxes + Other'],['Distance','PB2002 spherical arcs'],['Depth classes','Shallow <70; intermediate 70–<300; deep ≥300 km']], [70,147],x,294,132)
heading('Processing and data quality',x,448)
body('Coordinates, magnitude and depth are present for every record. Four negative reported depths are retained. Event IDs are deduplicated and non-earthquake types are excluded. A complete download does not prove complete earthquake detection, nor does a preferred magnitude represent one homogeneous scale.',x,458,72)
heading('The spatial setting',x,553)
figure('global_map',x,563,113)
body('<b>Fig. 1.</b> All epicentres on an equal-area Mollweide map; colours denote depth classes and grey lines PB2002 boundaries. Overlapping points are not area-normalized density.',x,682,37,19)
callout('Analytical strategy','Use one frozen sample, explicit denominators and sensitivity checks. Compare recorded patterns while keeping geological interpretation and measurement limitations separate.',x,735,54,NAVY,'#eef3f5')

# Column 2: reference chart and numerical reference table, then interpretation.
x=COLS[1]
heading('A reference for concentration',x,180)
body('Boundary proximity needs a geographic denominator. We compare earthquake distances with points uniformly distributed over Earth’s surface, including oceans. A second reference keeps the observed latitude distribution and varies longitude.',x,190,59)
figure('boundary_cdf',x,260,106)
body('<b>Fig. 2.</b> Cumulative distance distributions use the same PB2002 arcs and spherical geometry (R = 6,371.0088 km) for events and both references.',x,372,30,19)
heading('Table 2. Within-distance shares (%)',x,426,23)
data_table(2,['Radius\n(km)','Events','Equal\narea','Latitude\ncontrol'],[
    [r['radius_km'],f"{float(r['observed_pct']):.2f}",f"{float(r['equal_area_pct']):.2f}",f"{float(r['latitude_matched_pct']):.2f}"] for r in refs],
    [48,54,55,60],x,438,110,TEAL)
heading('How to interpret the contrast',x,572)
body('<b>70.15%</b> of events lie within 100 km, compared with <b>9.42%</b> of equal-area points and <b>10.50%</b> of latitude-controlled points. The observed-to-area share ratio is <b>7.45</b>. Thus, concentration remains clear under two geographic references; the ratio is not a risk multiplier or a causal effect.',x,582,96)
callout('Numerical and geological limits','Four independent 16,384-point designs give 9.38–9.53% within 100 km. This is numerical sensitivity, not a confidence interval. PB2002 is a simplified boundary layer, not a complete map of active faults.',x,707,82,TEAL,'#eaf4f5')

# Column 3: a time plot, a comparison table and explanatory narrative.
x=COLS[2]
heading('Time and threshold both matter',x,180)
body('Annual M ≥ 5 counts fluctuate substantially, peaking at <b>2,701 in 2011</b>. Comparing equal 13-year periods gives a different summary from fitting a trend across the whole record.',x,190,49)
figure('annual',x,251,109)
body('<b>Fig. 3.</b> Annual counts and period means (dashed). Rate comparisons allow for 4,749 days in 2000–2012 and 4,748 days in 2013–2025.',x,366,31,19)
heading('Table 3. Catalogue comparability',x,422,23)
data_table(3,['Indicator','2000–\n2012','2013–\n2025'],[
    ['M ≥ 5 records',f"{int(period['early_count']):,}",f"{int(period['late_count']):,}"],
    ['Annual mean',f"{float(period['early_annual_mean']):.1f}",f"{float(period['late_annual_mean']):.1f}"],
    ['Mw-family share','73.45%','55.05%'],['Horizontal-error\navailability','0.28%','86.80%']], [99,59,59],x,434,131,CORAL)
heading('A change in records is not enough',x,593,24)
body('The later-period record rate is <b>6.63% lower at M ≥ 5</b> and <b>15.42% lower at M ≥ 6</b>. Yet the full-period M5 Sen slope is positive. Magnitude-type composition and error-field availability also change, so these contrasts alone cannot establish a change in physical seismic activity.',x,603,90)
callout('Regional and window sensitivity','M5 rate changes differ: Indonesia/Philippines −25.58%; Mediterranean/Himalaya +8.82%. Removing 30-day / 500-km windows around 28 M ≥ 8 events changes the global contrast to −3.37%. This is window sensitivity, not declustering.',x,708,81,CORAL,'#faf0ed')

# Column 4: distribution table + route maps/sections + associations in prose.
x=COLS[3]
heading('Similar medians, different tails',x,180)
body('Globally, <b>83.20%</b> are shallow. Japan/Kuril and Tonga/Fiji share a 33 km median, but their deep-event shares differ by more than twofold.',x,190,43)
heading('Table 4. Regional depth summaries',x,248,23)
reg={r['region']:r for r in regions};all_depth=next(r for r in depth if r['region']=='All groups')
depth_rows=[['Global','46,463','23.7',f"{int(all_depth['deep_n'])/int(all_depth['known_depth_n'])*100:.2f}"]]
for key,label in [('Japan and Kuril','Japan / Kuril'),('Tonga Kermadec Fiji','Tonga / Fiji'),('Andes','Andes')]:
    r=reg[key];depth_rows.append([label,f"{int(r['count']):,}",f"{float(r['median_depth_km']):.1f}",f"{float(r['deep_pct_known_depth']):.2f}"])
data_table(4,['Region','N','Median\n(km)','Deep\n(%)'],depth_rows,[74,49,47,47],x,260,111,PURPLE)
heading('Local sections reveal structure',x,398,24)
figure('cross_sections',x,409,177)
body('<b>Fig. 4.</b> Maps: gold trench, blue route/swath, star at 0 km. A → B spans −200 to +1,200 km; swath ±100 km. Depth and distance use equal kilometre scales. Routes were selected after exploration.',x,592,48,19)
heading('Associations and interpretation',x,665,24)
body('Selected-section deep counts are <b>21/351</b> in northern Tohoku and <b>186/640</b> in central Tonga. Across the full regions, depth–boundary-distance Spearman ρ is <b>+0.39 globally</b> and <b>+0.56 in Japan/Kuril</b>. Magnitude associations are weak overall. These relationships describe patterns; pooled coefficients and illustrative sections do not identify a causal mechanism.',x,676,113)

# Column 5: frequency/proxy and case tables, with only one timing figure.
x=COLS[4]
heading('Rare events, large proxy share',x,180)
body('Event frequency and a magnitude-based energy proxy answer different questions. Their shares are compared directly below.',x,190,35)
heading('Table 5. Counts and relative proxy',x,242,23)
data_table(5,['M band','N','Events\n(%)','Proxy\n(%)'],[
    [label,f"{int(r['n']):,}",f"{float(r['count_percent']):.2f}",f"{float(r['proxy_percent']):.2f}"]
    for label,r in zip(['5–<6','6–<7','7–<8','≥8'],bands)], [45,49,61,62],x,254,104,GOLD)
body('The <b>28 events at M ≥ 8</b> contribute <b>71.21%</b> of the summed proxy, R(M)=10<super>1.5(M−5)</super>. One magnitude unit multiplies R by 31.6. Mixed preferred scales mean that this is illustrative, not measured joules, damage or risk.',x,376,68)
heading('Table 6. Fixed-window case counts',x,472,23)
data_table(6,['Case','Before','After','First 3d\n(% after)'],[
    [label,str(int(r['before_count'])),str(int(r['after_count'])),f"{float(r['first3_days_share_pct']):.1f}"]
    for label,r in zip(['Sumatra 2004','Maule 2010','Tohoku 2011'],cases)], [73,42,42,60],x,484,91,GOLD)
body('Radius ≤500 km; UTC windows [−30,0) and [0,30) days from the exact anchor time. Anchors are excluded; all windows are fully observed.',x,584,35,19)
figure('case_cumulative',x,634,92)
body('<b>Fig. 5.</b> Each curve uses its own 30-day post-window total. Day d counts events in [0,d), separating timing from total counts.',x,731,31,19)
body('<b>Scope:</b> These selections do not prove causal aftershock membership or a universal sequence law.',x,771,19,19)

rect(22,803,1145,23,NAVY)
para('<b>CONCLUSION</b>  Geography, regional depth tails and clustered sequences give a coherent descriptive picture. Time contrasts require catalogue-comparability checks; reference choices and window definitions remain central to interpretation. The strongest result is a transparent comparison of recorded patterns, not a forecast of future hazard.',29,805,1131,20,22,'#ffffff')
para('[1] <link href="https://earthquake.usgs.gov/fdsnws/event/1/">USGS FDSN</link>  ·  [2] <link href="https://doi.org/10.1029/2001GC000252">Bird (2003), PB2002</link>; GeoJSON (ODC-By)  ·  [3] <link href="https://www.naturalearthdata.com/">Natural Earth 110m</link> (public domain)  ·  [4] <link href="https://www.usgs.gov/programs/earthquake-hazards/earthquake-magnitude-energy-release-and-shaking-intensity">USGS magnitude–energy guidance</link>.  Reproducible methods, all figures and sensitivity results: <link href="'+REPO+'">project repository</link>.',22,831,1145,8,16,MUTED)
c.showPage();c.save();buf.seek(0);page=PdfReader(buf).pages[0]
for name,x,y,w,h in charts:
    source=PdfReader(OUT/'poster_charts'/(name+'.pdf')).pages[0];sw,sh=float(source.mediabox.width),float(source.mediabox.height)
    scale=min(w*mm/sw,h*mm/sh);xx=x*mm+(w*mm-sw*scale)/2;yy=H-(y+h)*mm+(h*mm-sh*scale)/2
    page.merge_transformed_page(source,Transformation().scale(scale).translate(xx,yy))
writer=PdfWriter();writer.add_page(page);writer.add_metadata({'/Title':'Inside the Earth | DSC5002 Academic Poster','/Author':'DSC5002 Project Team','/Subject':'Searchable A0 landscape; five columns, narrative, six data tables and five scientific figures'})
with (DEL/'DSC5002_Academic_Poster.pdf').open('wb') as stream:writer.write(stream)
(OUT/'poster_layout_checks.json').write_text(json.dumps({'text_boxes':boxes,'charts':[{'name':n,'x_mm':x,'y_mm':y,'width_mm':w,'height_mm':h} for n,x,y,w,h in charts],'tables':tables,'page_mm':[1189,841],'animation_link':None,'columns':5},indent=2),encoding='utf-8')
print('Created five-column poster: 5 figures, 6 searchable data tables and explanatory prose.')

# Presentation notes follow the current physical reading order.
script=[
('Opening | five columns, one catalogue', 'Hello. We are the DSC5002 project team at City University of Hong Kong. Inside the Earth studies earthquake patterns through space, time, depth and magnitude. The poster reads from left to right through five columns. Its tables give precise comparisons, while five selected figures show geography, variation and structure. We describe a fixed catalogue; we do not predict future earthquakes.'),
('Column 1 | study design', 'The first column explains the motivation and common design. A map can show a cluster, but it cannot establish whether that pattern comes from geography, a large sequence or a change in reporting. Table 1 defines our sample: 46,463 unique USGS earthquakes from 2000 to 2025, all with preferred magnitude at least five. All records have coordinates, magnitude and depth. We retain four negative reported depths and exclude non-earthquake event types. The world map then supplies the spatial setting. Completeness of the downloaded files is not proof of complete detection.'),
('Column 2 | space and reference', 'Figure 2 and Table 2 ask: concentrated relative to what? We compare observed boundary distances with 65,536 equal-area reference locations over the whole globe, including oceans. A second reference preserves the observed latitude distribution while varying longitude. Within one hundred kilometres, 70.15 percent of events are included, compared with 9.42 percent of equal-area points and 10.50 percent of latitude-controlled points. The observed-to-area share ratio is 7.45. These are geographic comparisons, not a realistic earthquake-occurrence model. The range across four reference designs measures numerical sensitivity; it is not a confidence interval or a hazard multiplier.'),
('Column 3 | time and comparability', 'The third column places the annual trend beside Table 3, which documents measurement comparability. Counts peak in 2011. The later thirteen-year period has a 6.63 percent lower record rate at magnitude five and a 15.42 percent lower rate at magnitude six. Yet the whole-period M5 Sen slope is positive, so the chosen summary matters. Mw-family share changes from 73.45 to 55.05 percent, while horizontal-error availability rises sharply. Regional contrasts also differ in direction. Removing fixed windows around the twenty-eight largest events reduces the global M5 contrast to minus 3.37 percent. This is a sensitivity check, not declustering.'),
('Column 4 | depth and associations', 'Table 4 shows why medians are insufficient. Japan and Kuril and Tonga, Kermadec and Fiji have the same thirty-three-kilometre median, yet deep-event shares are 5.01 and 11.76 percent. Figure 4 pairs local route maps with sections. The star is the mapped trench origin; A to B gives increasing section distance, and horizontal and vertical kilometres use equal scales. The selected Tonga section contains 186 deep events out of 640; northern Tohoku contains 21 out of 351. The routes were chosen after exploration. Regional depth-distance associations support a structured descriptive pattern, but do not establish a causal mechanism.'),
('Column 5 | magnitude and event sequences', 'The last column uses two compact tables. Table 5 compares event-count shares with an illustrative magnitude-based proxy. The twenty-eight magnitude-eight-or-larger events are only 0.06 percent of records but contribute 71.21 percent of the summed proxy. Because preferred magnitude scales are mixed, this is not measured energy or damage. Table 6 then compares three events using the same five-hundred-kilometre radius and thirty-day before and after windows, excluding each anchor. Figure 5 normalizes the post-window counts to compare timing. About sixty to seventy-one percent appear in the first three days. Membership in a time-and-distance window does not prove that an event is a causal aftershock.'),
('Closing | what the evidence supports', 'The combined evidence shows concentration near mapped boundaries, contrasting regional depth tails and clustered selected sequences. Our interpretation depends on reference geography, catalogue composition and window definition. The contribution is to make those choices visible through explanatory text, inspectable tables and focused figures. Thank you for your attention. We would be happy to discuss the reference design or the supplementary sensitivity results.')]
styles={'title':ParagraphStyle('title',fontName='Body-Bold',fontSize=21,leading=26,textColor=HexColor(NAVY)),
    'head':ParagraphStyle('head',fontName='Body-Bold',fontSize=12,leading=16,textColor=HexColor(TEAL),spaceBefore=10,spaceAfter=4),
    'body':ParagraphStyle('body',fontName='Body',fontSize=11,leading=14.5,textColor=HexColor(NAVY))}
story=[Paragraph('Inside the Earth | Poster presentation script',styles['title']),Spacer(1,10),Paragraph('Suggested delivery: about 6–7 minutes including pauses to point to the tables and figures. This is a rehearsal estimate, not a course rule. Follow the five columns from left to right.',styles['body'])]
for title,content in script:story.append(KeepTogether([Paragraph(title,styles['head']),Paragraph(content,styles['body'])]))
story.extend([Paragraph('Discussion prompts',styles['head']),Paragraph('<b>Why not use every plot?</b> The poster selects five figures that add information to the narrative; precise comparisons are shown in six tables. All fourteen analytical figures remain in the report.<br/><br/><b>Why not fit a predictive b-value?</b> An M5 extraction threshold does not establish completeness, and preferred magnitude scales are mixed.<br/><br/><b>Are the references a statistical null model?</b> No. They control geometric area and latitude, not the tectonic processes governing earthquake occurrence.',styles['body']),Paragraph('Presentation reference',styles['head']),Paragraph('CityU Language Centre: <link href="https://www.cityu.edu.hk/lc/app/poster-script-samples1.html" color="#197c9e">poster script sample</link>. The opening, signposting, methods, findings and closing structure follow the sample; the research content and wording are original.',styles['body'])])
doc=SimpleDocTemplate(str(DEL/'DSC5002_Presentation_Script.pdf'),pagesize=(210*mm,297*mm),rightMargin=22*mm,leftMargin=22*mm,topMargin=20*mm,bottomMargin=20*mm)
doc.build(story);(DEL/'Presentation_Script.txt').write_text('\n\n'.join(h+'\n'+b for h,b in script),encoding='utf-8')
print('Created presentation script aligned with the five-column narrative.')
