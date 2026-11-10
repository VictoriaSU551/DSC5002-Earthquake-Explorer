"""Searchable A0 poster: tightly flowing evidence, tables and selected figures.

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
W,H=1189*mm,841*mm;CW=221;COLS=[22,253,484,715,946]
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
    style=ParagraphStyle('p',fontName='Body',fontSize=size,leading=size*1.18,textColor=HexColor(color))
    p=Paragraph(s,style);pw,ph=p.wrap(w*mm,h*mm)
    if ph>h*mm+.1:raise ValueError(f'Text overflow: {s[:65]} {ph/mm:.1f}>{h}')
    p.drawOn(c,x*mm,H-y*mm-ph);boxes.append({'text':s,'x_mm':x,'y_mm':y,'width_mm':w,'height_mm':ph/mm,'allocation_mm':h,'font_pt':size})
    return ph/mm

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
    t=Table(cells,colWidths=[v/sum(widths)*CW*mm for v in widths],hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor(color)),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),3*mm),('RIGHTPADDING',(0,0),(-1,-1),3*mm),
        ('TOPPADDING',(0,0),(-1,-1),2.3*mm),('BOTTOMPADDING',(0,0),(-1,-1),2.3*mm),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#eef3f5'),HexColor('#ffffff')]),
        ('LINEBELOW',(0,-1),(-1,-1),.65,HexColor('#a8bbc5'))]))
    tw,th=t.wrap(CW*mm,maxheight*mm)
    assert abs(tw/mm-CW)<.01 and th/mm<=maxheight,(number,th/mm,maxheight)
    t.drawOn(c,x*mm,H-y*mm-th)
    tables.append({'number':number,'headers':headers,'rows':rows,'x_mm':x,'y_mm':y,'width_mm':CW,'height_mm':th/mm})
    return th/mm

expanded=json.loads((OUT/'expanded_facts.json').read_text());facts=json.loads((OUT/'poster_facts.json').read_text())
refs=read_csv(OUT/'tables/spatial_reference_summary.csv');r100=next(r for r in refs if r['radius_km']=='100')
regions=read_csv(OUT/'tables/regional_summary.csv');depth=read_csv(OUT/'tables/member3_region_summary.csv')
period=next(r for r in read_csv(ROOT/'docs/temporal_regional_v2/tables/equal_period_comparison.csv') if r['region']=='All' and float(r['threshold'])==5)
bands=read_csv(OUT/'rq4/tables/magnitude_band_summary.csv');cases=read_csv(OUT/'tables/case_comparison.csv')

# Flow layout: each block follows the measured end of the previous block.
class Column:
    def __init__(self,index):self.x=COLS[index];self.y=133.;self.index=index;self.blocks=[]
    def gap(self,v=2.6):self.y+=v
    def heading(self,value):
        h=para('<b>'+value+'</b>',self.x,self.y,CW,60,24);self.blocks.append(h);self.y+=h+2.4
    def paragraph(self,value,size=22):
        h=para(value,self.x,self.y,CW,250,size);self.blocks.append(h);self.y+=h+2.6
    def table(self,title,number,headers,rows,widths):
        self.heading(title);h=data_table(number,headers,rows,widths,self.x,self.y,250,colors[self.index]);self.blocks.append(h);self.y+=h+3
    def figure(self,name,caption):
        page=PdfReader(OUT/'poster_charts'/(name+'.pdf')).pages[0]
        h=CW*float(page.mediabox.height)/float(page.mediabox.width)
        figure(name,self.x,self.y,h);self.blocks.append(h);self.y+=h+2.2
        self.paragraph(caption,19)
    def note(self,title,value):
        style=ParagraphStyle('measure',fontName='Body',fontSize=20,leading=23.6)
        ph=Paragraph(value,style).wrap((CW-12)*mm,250*mm)[1]/mm
        h=ph+22
        rect(self.x,self.y,CW,h,tints[self.index]);rect(self.x,self.y,1.5,h,colors[self.index])
        para('<b>'+title+'</b>',self.x+6,self.y+3,CW-12,12,21,colors[self.index])
        para(value,self.x+6,self.y+16,CW-12,ph+.1,20)
        self.blocks.append(h);self.y+=h+3

rect(0,0,1189,841,'#ffffff');colors=[NAVY,TEAL,CORAL,PURPLE,GOLD];tints=['#eef3f5','#eaf4f5','#faf0ed','#f2edf7','#faf4e6']
for i,col in enumerate(colors):rect(i*237.8,0,237.8,4,col)
text('INSIDE THE EARTH',22,32,74,NAVY,True)
text('Interpreting earthquake patterns through geography, time, depth and magnitude',23,50,29,MUTED)
text('DSC5002 Project Team  |  City University of Hong Kong  |  USGS catalogue, 2000–2025',23,66,22,MUTED)
text('46,463 EARTHQUAKES',946,28,27,NAVY,True)
text('M ≥ 5  |  26 years  |  5 questions',946,43,22,MUTED)
text('One frozen UTC catalogue',946,57,21,MUTED)
rect(22,77,1145,28,'#eef3f5')
para('<b>ABSTRACT</b>  Geographic references show strong boundary concentration, while regional depth tails and event windows expose structure hidden by pooled summaries. Time contrasts depend on the magnitude threshold and coincide with shifts in catalogue composition. We connect maps, exact comparisons and sensitivity checks to distinguish descriptive evidence from unsupported claims about causes or future hazard.',28,81,1133,22,23)
headers=['01  STUDY DESIGN','02  SPACE & REFERENCE','03  TIME & COMPARABILITY','04  DEPTH & ASSOCIATIONS','05  MAGNITUDE & SEQUENCES']
for x,title,col in zip(COLS,headers,colors):rect(x,111,CW,16,col);text(title,x+4,122,22,'#ffffff',True)
for x in [248,479,710,941]:rect(x,133,.35,657,'#dfe7ea')
columns=[Column(i) for i in range(5)]

q=columns[0]
q.heading('What can one catalogue show?')
q.paragraph('Earthquakes vary in location, depth, magnitude and timing. A map identifies clusters, but does not separate geographic concentration, large event sequences and changes in reporting. We ask where recorded activity concentrates, how its time pattern changes, and which regional structures disappear when observations are pooled.')
q.table('Table 1. Shared analytical scope',1,['Element','Definition'],[
    ['Window','2000–2025 UTC'],['Selection','Earthquake; preferred M ≥ 5'],['Observations','46,463 unique event IDs'],
    ['Regions','6 ordered boxes + Other'],['Distance','PB2002 spherical arcs'],['Depth bands','Shallow <70; intermediate 70–<300; deep ≥300 km']], [70,147])
q.heading('From question to comparison')
q.paragraph('<b>Space:</b> compare boundary distances with equal-area and latitude-controlled reference points. <b>Time:</b> compare equal 13-year periods and inspect reporting changes. <b>Depth:</b> contrast regional distributions and local sections. <b>Magnitude and cases:</b> separate frequency, a relative proxy and time-window concentration.')
q.figure('global_map','<b>Fig. 1.</b> All 46,463 epicentres; equal-area Mollweide projection. Colours denote depth bands; grey lines show PB2002 boundaries. Overlapping points are not an area-normalized density.')
q.heading('Data checks and statistical choices')
q.paragraph('Coordinates, magnitude and depth are present for every record. Event IDs are deduplicated and non-earthquake types excluded. Four negative reported depths are retained. A complete download is not proof of complete detection; preferred magnitudes are not a homogeneous measurement scale.')
q.paragraph('Medians summarize typical values, tail shares retain rare deep events, and rank correlations describe monotonic association. Counts use all eligible records. We avoid independent-event p-values because clustered sequences do not supply independent observations.')
q.heading('Why the event-type filter matters')
q.paragraph('An all-type companion extract has 46,523 records: 55 volcanic eruptions, four nuclear explosions and one landslide must be excluded. The remaining 46,463 earthquake IDs and principal measurements match the analysis catalogue. Treating the 60-record difference as a catalogue revision would misstate the sample.')
q.note('Reading the evidence','Each column moves from a defined comparison to a result and its interpretation. Unequal region areas, selected routes, catalogue composition and window definitions remain visible rather than being absorbed into a single global conclusion.')

q=columns[1]
q.heading('Concentrated relative to what?')
q.paragraph('Boundary proximity needs a geographic denominator. We compare event distances with equal-area points over the whole globe, including oceans. A second reference preserves the observed latitude distribution while varying longitude.')
q.figure('boundary_cdf','<b>Fig. 2.</b> Cumulative shares under identical PB2002 minor great-circle arc geometry, R = 6,371.0088 km. The reference curves answer a geographic comparison, not a seismicity null hypothesis.')
q.table('Table 2. Within-distance shares (%)',2,['Radius\n(km)','Events','Equal\narea','Latitude\ncontrol'],[
    [r['radius_km'],f"{float(r['observed_pct']):.2f}",f"{float(r['equal_area_pct']):.2f}",f"{float(r['latitude_matched_pct']):.2f}"] for r in refs],[48,54,55,60])
q.paragraph('At 100 km, <b>70.15%</b> of events versus <b>9.42%</b> of equal-area points gives an observed-to-area share ratio of <b>7.45</b>. Latitude control gives <b>10.50%</b>. At 500 km the ratio narrows to 2.70: the threshold changes the contrast.')
q.heading('Does every region behave alike?')
q.figure('regional_proximity','<b>Fig. 3.</b> Within-region percentages inside 100 km. Each region uses its own earthquake denominator; these are not area-normalized hazard rates.')
q.paragraph('Tonga/Fiji has a 76.0% nearby share, versus 39.6% in Mediterranean/Himalaya. The high 84.8% share in Other belongs to a heterogeneous residual group; it is not one coherent tectonic region.')
threshold_rows=read_csv(OUT/'tables/boundary_threshold_sensitivity.csv')
q.table('Table 3. Magnitude-threshold check',3,['Cutoff','N','≤100 km\n(%)','Median\n(km)'],[
    ['M ≥ '+r['min_magnitude'],f"{int(r['n']):,}",f"{float(r['within_100km_pct']):.2f}",f"{float(r['median_boundary_distance_km']):.1f}"] for r in threshold_rows],[45,53,60,59])
q.paragraph('The within-100-km share falls to <b>63.57%</b> at M ≥ 7. Broad boundary concentration does not imply the same proximity distribution at every magnitude threshold.',20)
q.note('Reference sensitivity','Four 16,384-point equal-area designs give 9.38–9.53% within 100 km. This is numerical sensitivity, not a confidence interval. The 7.45 ratio is descriptive; simplified PB2002 proximity does not quantify fault uncertainty or future risk.')

q=columns[2]
q.heading('A fluctuating recorded history')
q.paragraph('Annual M ≥ 5 counts peak at <b>2,701 in 2011</b>. Equal-period means, a whole-period slope and regional changes answer different questions, so no single summary is treated as the trend.')
q.figure('annual','<b>Fig. 4.</b> Annual counts and 13-year means (dashed). Comparisons account for 4,749 early-period days and 4,748 late-period days.')
q.table('Table 4. Catalogue comparability',4,['Indicator','2000–\n2012','2013–\n2025'],[
    ['M ≥ 5 records',f"{int(period['early_count']):,}",f"{int(period['late_count']):,}"],
    ['Annual mean',f"{float(period['early_annual_mean']):.1f}",f"{float(period['late_annual_mean']):.1f}"],
    ['Mw-family share','73.45%','55.05%'],['Horizontal-error\navailability','0.28%','86.80%']],[99,59,59])
q.figure('magnitude_mix','<b>Fig. 5.</b> Annual Mw-family composition exposes changes concealed by the two period averages. Selecting Mw alone does not make measurement homogeneous.')
q.paragraph('Later-period rates are <b>6.63% lower at M ≥ 5</b> and <b>15.42% lower at M ≥ 6</b>, yet the full-period M5 Sen slope is positive. Changing magnitude composition and error reporting limit interpretation as changing physical activity. Missing error does not mean zero error.')
q.heading('The direction depends on region')
q.figure('regional_change','<b>Fig. 6.</b> Exposure-adjusted M5 rate changes, 2013–2025 versus 2000–2012. Shared periods support within-region comparison; unequal box areas prevent direct hazard ranking.')
q.paragraph('Indonesia/Philippines falls by <b>25.58%</b>; Mediterranean/Himalaya rises by <b>8.82%</b>. Aggregation conceals that contrast. Selecting only Mw-family records also changes the sample and does not homogenize the catalogue.')
q.note('Large-event window check','Removing the union of 30-day / 500-km windows around 28 M ≥ 8 anchors removes 3,090 records and changes the M5 contrast to −3.37%. Anchors are included in this removal. This is sensitivity analysis, not declustering.')

q=columns[3]
q.heading('Similar medians, different tails')
q.paragraph('Globally <b>83.20%</b> of events are shallow. Japan/Kuril and Tonga/Fiji both have median depth 33 km, but deep-event shares differ by more than twofold. A centre alone hides that tail contrast.')
reg={r['region']:r for r in regions};all_depth=next(r for r in depth if r['region']=='All groups')
depth_rows=[['Global','46,463','23.7',f"{int(all_depth['deep_n'])/int(all_depth['known_depth_n'])*100:.2f}"]]
for key,label in [('Japan and Kuril','Japan / Kuril'),('Tonga Kermadec Fiji','Tonga / Fiji'),('Andes','Andes')]:
    r=reg[key];depth_rows.append([label,f"{int(r['count']):,}",f"{float(r['median_depth_km']):.1f}",f"{float(r['deep_pct_known_depth']):.2f}"])
q.table('Table 5. Regional depth summaries',5,['Region','N','Median\n(km)','Deep\n(%)'],depth_rows,[74,49,47,47])
q.figure('cross_sections','<b>Fig. 7.</b> Gold trench; blue route and ±100 km swath; star at 0 km. A → B spans −200 to +1,200 km. Depth and distance use equal kilometre scales. Routes were chosen after exploration.')
q.paragraph('Selected-section deep counts are <b>21/351</b> in northern Tohoku and <b>186/640</b> in central Tonga. These local swaths are subsets, so their shares differ from Table 5. Tonga’s selected 29.1% deep share versus 11.76% regionally illustrates why a section cannot represent its entire parent region.')
q.heading('Does the pooled association hold?')
q.figure('correlations','<b>Fig. 8.</b> Spearman ρ for all records and each region. Common −1 to +1 scale; descriptive associations, without independent-event significance tests.')
q.paragraph('Depth–boundary-distance ρ is <b>+0.39 globally</b> and <b>+0.56 in Japan/Kuril</b>, but only +0.07 in Mediterranean/Himalaya. Magnitude associations are weak overall. Pooled coefficients do not imply identical regional relationships.')
q.note('Geological interpretation','Depth tails and local sections reveal structure consistent with regional differences. Selected routes, simplified boundaries and observational associations do not independently identify the physical mechanism or prove causality.')

q=columns[4]
q.heading('Frequency and scale are different')
q.paragraph('An event-count distribution describes how often magnitudes occur. A summed magnitude-based proxy gives much greater weight to rare, large events; the two shares should be compared explicitly.')
q.table('Table 6. Counts and relative proxy',6,['M band','N','Events\n(%)','Proxy\n(%)'],[
    [label,f"{int(r['n']):,}",f"{float(r['count_percent']):.2f}",f"{float(r['proxy_percent']):.2f}"] for label,r in zip(['5–<6','6–<7','7–<8','≥8'],bands)],[45,49,61,62])
q.paragraph('Using R(M)=10<super>1.5(M−5)</super>, one magnitude unit multiplies the proxy by 31.6. Only <b>28 events at M ≥ 8</b> supply <b>71.21%</b> of its sum. Mixed preferred scales make this illustrative, not measured joules, damage or risk.')
q.heading('Tail counts and completeness')
q.paragraph('Inclusive N(M ≥ m) is <b>3,874 at M ≥ 6</b>, <b>387 at M ≥ 7</b> and <b>28 at M ≥ 8</b>. The M5 extraction threshold does not establish completeness, so no predictive b-value is fitted.')
q.heading('Counts first; timing second')
q.paragraph('Cases use radius ≤500 km and UTC windows [−30,0) and [0,30) days relative to the exact anchor time. Anchors are excluded. All windows are fully observed.')
q.table('Table 7. Fixed-window case counts',7,['Case','Before','After','First 3d\n(% after)'],[
    [label,str(int(r['before_count'])),str(int(r['after_count'])),f"{float(r['first3_days_share_pct']):.1f}"] for label,r in zip(['Sumatra 2004','Maule 2010','Tohoku 2011'],cases)],[73,42,42,60])
q.figure('case_cumulative','<b>Fig. 9.</b> Each curve divides by its own 30-day post-window count. Day d includes [0,d). Normalization separates the timing pattern from unequal totals.')
q.paragraph('The first three days contain <b>60.1%, 60.9% and 70.9%</b> of the post-window records. Early concentration coexists with a longer tail; changing duration changes the total being summarized.')
sens=read_csv(OUT/'tables/case_window_sensitivity.csv')
window_rows=[]
for label,case in zip(['Sumatra 2004','Maule 2010','Tohoku 2011'],cases):
    subset=[r for r in sens if r['name']==case['name'] and float(r['radius_km'])==500]
    window_rows.append([label]+[str(int(next(r['after_count'] for r in subset if int(r['days_each_side'])==d))) for d in [7,30,90]])
q.table('Table 8. Duration sensitivity at 500 km',8,['Case','7 days','30 days','90 days'],window_rows,[73,48,48,48])
q.paragraph('Post-window counts use the same radius and anchor exclusion. These are nested samples, not independent replicates. The full supplement also varies radius from 250 to 1,000 km.',19)
q.note('What the cases establish','The selected sequences show concentrated recorded activity after major events. Time-and-distance membership alone does not establish causal aftershock status or a universal sequence law.')

column_metrics=[]
for i,q in enumerate(columns):
    metric={'column':i+1,'start_y_mm':133,'end_y_mm':q.y,'content_height_mm':sum(q.blocks),'used_height_mm':q.y-133}
    column_metrics.append(metric);print('Column layout',metric)
    assert q.y<=791,f'Column {i+1} exceeds body: {q.y:.1f} mm'
rect(22,799,1145,27,NAVY)
para('<b>CONCLUSION</b>  Geographic references establish a strong descriptive concentration near mapped boundaries. Depth tails and regional associations reveal structure that global summaries conceal; event curves separate timing from totals. Time contrasts require catalogue-comparability checks, and window choices materially change case counts. These are reproducible comparisons of recorded patterns, not forecasts of future hazard.',28,802,1133,21,22,'#ffffff')
para('[1] <link href="https://earthquake.usgs.gov/fdsnws/event/1/">USGS FDSN</link>  ·  [2] <link href="https://doi.org/10.1029/2001GC000252">Bird (2003), PB2002</link>; GeoJSON (ODC-By)  ·  [3] <link href="https://www.naturalearthdata.com/">Natural Earth 110m</link> (public domain)  ·  [4] <link href="https://www.usgs.gov/programs/earthquake-hazards/earthquake-magnitude-energy-release-and-shaking-intensity">USGS magnitude–energy guidance</link>.  Full methods, all figures and sensitivity results: <link href="'+REPO+'">project repository</link>.',22,831,1145,8,16,MUTED)
c.showPage();c.save();buf.seek(0);page=PdfReader(buf).pages[0]
for name,x,y,w,h in charts:
    source=PdfReader(OUT/'poster_charts'/(name+'.pdf')).pages[0];sw,sh=float(source.mediabox.width),float(source.mediabox.height)
    scale=min(w*mm/sw,h*mm/sh);xx=x*mm+(w*mm-sw*scale)/2;yy=H-(y+h)*mm+(h*mm-sh*scale)/2
    page.merge_transformed_page(source,Transformation().scale(scale).translate(xx,yy))
writer=PdfWriter();writer.add_page(page);writer.add_metadata({'/Title':'Inside the Earth | DSC5002 Academic Poster','/Author':'DSC5002 Project Team','/Subject':'Searchable A0 landscape; five flowing evidence columns, eight data tables and nine scientific figures'})
with (DEL/'DSC5002_Academic_Poster.pdf').open('wb') as stream:writer.write(stream)
(OUT/'poster_layout_checks.json').write_text(json.dumps({'text_boxes':boxes,'charts':[{'name':n,'x_mm':x,'y_mm':y,'width_mm':w,'height_mm':h} for n,x,y,w,h in charts],'tables':tables,'page_mm':[1189,841],'animation_link':None,'columns':5,'column_metrics':column_metrics,'flow_gap_mm':2.6},indent=2),encoding='utf-8')
print('Created compact five-column poster: 9 evidence figures, 8 data tables and continuous narrative.')

# Presentation notes follow the current physical reading order.
script=[
('Opening | one connected evidence chain', 'Hello. We are the DSC5002 project team at City University of Hong Kong. Inside the Earth asks how earthquake patterns change when we examine geography, time, depth and magnitude together. Please read the five columns from left to right. Each moves from a question, through its evidence, to an interpretation and a limitation. We describe recorded patterns in one fixed catalogue; we do not predict future earthquakes.'),
('Column 1 | scope and choices', 'Table 1 defines the common sample: 46,463 unique USGS earthquakes from 2000 to 2025, all with preferred magnitude at least five. We retain four negative reported depths and exclude non-earthquake types. This matters: a companion all-type extract contains sixty volcanic, nuclear-explosion or landslide records that do not belong in this earthquake sample. Figure 1 establishes the global setting. Medians, tail shares and rank correlations capture different features. Download completeness does not establish complete detection, and clustered observations are not independent events for significance testing.'),
('Column 2 | concentration and sensitivity', 'Figure 2 and Table 2 compare boundary distances against equal-area and latitude-controlled reference points. Within one hundred kilometres, the event share is 70.15 percent, versus 9.42 percent for equal-area locations and 10.50 percent for the latitude control. The observed-to-area ratio is 7.45. Figure 3 shows that proximity also varies by region. Table 3 adds a magnitude-threshold check: the nearby share falls to 63.57 percent among events of magnitude seven or more. Broad concentration therefore does not mean identical proximity at every magnitude. These geographic references are not realistic earthquake-occurrence models, and the numerical replicate range is not a confidence interval.'),
('Column 3 | time and measurement comparability', 'Figure 4 shows fluctuating annual counts, with the peak in 2011. Later-period rates are 6.63 percent lower at magnitude five and 15.42 percent lower at magnitude six, yet the whole-period M5 Sen slope is positive. Table 4 and Figure 5 show why recording composition matters: Mw-family share and horizontal-error availability change substantially. Figure 6 adds the regional contrast: Indonesia and the Philippines decrease, while the Mediterranean and Himalaya group increases. Removing fixed windows around all twenty-eight magnitude-eight-or-larger events reduces the global M5 contrast to minus 3.37 percent. This is a sensitivity check, not declustering or proof of changing physical activity.'),
('Column 4 | regional and local depth structure', 'Table 5 shows identical thirty-three-kilometre medians for Japan and Kuril and Tonga, Kermadec and Fiji, but deep-event shares of 5.01 and 11.76 percent. Figure 7 pairs route maps with equal-kilometre sections. The local Tonga swath has 186 deep events out of 640, about 29.1 percent, so it cannot represent the complete region. Figure 8 then shows that the depth-distance association varies across regions: about 0.56 in Japan and Kuril but only 0.07 in the Mediterranean and Himalaya group. These selected sections and descriptive associations reveal structure without identifying a causal mechanism.'),
('Column 5 | magnitude, timing and window choice', 'Table 6 separates event frequency from an illustrative magnitude-based proxy. The twenty-eight events at magnitude eight or more contribute 71.21 percent of the summed proxy, although they are only 0.06 percent of records. Mixed magnitude scales prevent treating this as measured energy or damage. Table 7 compares three cases under identical five-hundred-kilometre and thirty-day windows, excluding anchors. Figure 9 divides by each case’s own post-window total: about sixty to seventy-one percent appear in the first three days. Table 8 keeps the radius fixed and varies duration. Counts continue to rise between thirty and ninety days, showing why the window belongs in the result definition. These are nested samples, and time-and-distance membership does not prove causal aftershock status.'),
('Closing | what remains supported', 'The evidence supports strong descriptive boundary concentration, regional differences in depth, and early concentration within selected sequences. It also shows that magnitude thresholds, reporting composition and event windows affect the comparison. Our contribution is to make this chain of evidence visible and reproducible while keeping its limits clear. Thank you for your attention. We would be happy to discuss a particular sensitivity check.')]
styles={'title':ParagraphStyle('title',fontName='Body-Bold',fontSize=21,leading=26,textColor=HexColor(NAVY)),
    'head':ParagraphStyle('head',fontName='Body-Bold',fontSize=12,leading=16,textColor=HexColor(TEAL),spaceBefore=10,spaceAfter=4),
    'body':ParagraphStyle('body',fontName='Body',fontSize=11,leading=14.5,textColor=HexColor(NAVY))}
story=[Paragraph('Inside the Earth | Poster presentation script',styles['title']),Spacer(1,10),Paragraph('Suggested delivery: about 7–8 minutes including pauses to point to the tables and figures. This is a rehearsal estimate, not a course rule. Follow the five columns from left to right.',styles['body'])]
for title,content in script:story.append(KeepTogether([Paragraph(title,styles['head']),Paragraph(content,styles['body'])]))
story.extend([Paragraph('Discussion prompts',styles['head']),Paragraph('<b>Why compare several thresholds and windows?</b> They define different eligible samples. Reporting their effects makes interpretation depend on explicit choices rather than a single convenient setting.<br/><br/><b>Why not fit a predictive b-value?</b> An M5 extraction threshold does not establish completeness, and preferred magnitude scales are mixed.<br/><br/><b>Are the references a statistical null model?</b> No. They control geometric area and latitude, not the tectonic processes governing earthquake occurrence.',styles['body']),Paragraph('Presentation reference',styles['head']),Paragraph('CityU Language Centre: <link href="https://www.cityu.edu.hk/lc/app/poster-script-samples1.html" color="#197c9e">poster script sample</link>. The opening, signposting, methods, findings and closing structure follow the sample; the research content and wording are original.',styles['body'])])
doc=SimpleDocTemplate(str(DEL/'DSC5002_Presentation_Script.pdf'),pagesize=(210*mm,297*mm),rightMargin=22*mm,leftMargin=22*mm,topMargin=20*mm,bottomMargin=20*mm)
doc.build(story);(DEL/'Presentation_Script.txt').write_text('\n\n'.join(h+'\n'+b for h,b in script),encoding='utf-8')
print('Created presentation script aligned with the five-column narrative.')
