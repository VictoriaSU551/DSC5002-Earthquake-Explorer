"""Publishable offline animation: only the three case subsets, no full catalogue."""
from pathlib import Path
import json,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plotly.offline import get_plotlyjs
from earthquake_explorer.dashboard import safe_json
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'outputs/final/dashboard.html').read_text(encoding='utf-8')
d=json.loads(re.search(r'<script id="catalogue" type="application/json">(.*?)</script>',html,re.S).group(1))
indices=sorted({i for c in d['cases'] for i in c['indices']});lookup={old:new for new,old in enumerate(indices)}
d['rows']=[d['rows'][i] for i in indices]
for c in d['cases']:c['indices']=[lookup[i] for i in c['indices']]
d={k:d[k] for k in ['rows','cases','coast','boundaries','depth_names']}
js=(ROOT/'web/dashboard.js').read_text(encoding='utf-8')
helpers=js[:js.index('async function plot')]
anim=js[js.index('let animData='):js.index('async function update()')]
shell='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Inside the Earth | Recorded earthquake sequences</title>
<style>body{margin:0;background:#f1f5f7;color:#16364b;font:16px 'Segoe UI',sans-serif}main{max-width:1400px;margin:auto;padding:28px}h1{margin:0 0 8px;font-size:34px}h3{font-size:20px;margin:6px 0}.controls{display:flex;gap:18px;align-items:center;flex-wrap:wrap}button,select{font:inherit;border:1px solid #bbcdd6;border-radius:5px;background:white;padding:7px 14px;color:#16364b}button{cursor:pointer}#anim-slider{flex:1;min-width:180px}#anim-time-label{min-width:100px;font-weight:bold}.frames{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;background:white;padding:15px;margin-top:15px;border-radius:8px}.chart{height:290px}.stat{font-size:14px;min-height:35px}#anim-histogram{height:260px;background:white;margin-top:18px}.note{font-size:14px;line-height:1.5}.blue{color:#2166ac}.gold{color:#cc8b19}.purple{color:#8e4b98}a{color:#167d8d}#keyframe{background:white;padding:12px}#keyframe-title{margin-bottom:10px;font-size:22px;font-weight:bold}@media(max-width:850px){.frames{grid-template-columns:1fr}h1{font-size:26px}}</style>
<main><h1>Three major events, one relative timeline</h1><p>Recorded M ≥ 5 earthquakes within 500 km; [−30,0) and [0,30) days. Anchors excluded.</p>
<div class="controls"><button id="anim-play">Play</button><button id="anim-reset">Reset</button><label>Speed <select id="anim-speed"><option value="1">1 day/s</option><option value="2" selected>2 days/s</option><option value="4">4 days/s</option><option value="8">8 days/s</option></select></label><label>Mode <select id="anim-mode"><option value="cumulative">Cumulative</option><option value="sliding">Trailing 7 days</option></select></label></div>
<p class="controls"><span id="anim-time-label"></span><input id="anim-slider" aria-label="Animation time" type="range" min="-30" max="30" step=".25" value="-30"></p>
<div id="keyframe"><div id="keyframe-title">Cumulative sequence at t = −30 days</div><div class="frames">'''
for i in range(3):shell+=f'<article><h3 id="anim-title-{i}"></h3><div class="chart" id="anim-map-{i}"></div><div class="stat" id="anim-stat-{i}"></div></article>'
shell+='''</div><p class="note"><span class="blue">● Shallow &lt;70 km</span> · <span class="gold">● Intermediate 70–&lt;300 km</span> · <span class="purple">● Deep ≥300 km</span> · ★ Anchor location (reference at every frame). Marker size indicates magnitude.</p></div><h3>Daily activity: complete window with current-time cursor</h3><div id="anim-histogram"></div><p class="note">The histogram always shows the full window, including days beyond the cursor. These are selected observational sequences, not a causal aftershock classification. The M5 threshold omits smaller events; this is not a hazard or prediction tool. Source: USGS frozen project catalogue, 46,463 earthquake events, 2000–2025. Geography: PB2002 (Bird 2003; ODC-By), Natural Earth (public domain). Case view adapts the supplied RQ5 contribution.</p><p><a href="poster.pdf">Academic poster (searchable PDF)</a> · <a href="https://github.com/VictoriaSU551/DSC5002-Earthquake-Explorer">Code, methods and results</a></p></main>'''
anim=anim.replace("const t=animT,mode=$('anim-mode').value;","const t=animT,mode=$('anim-mode').value; $('keyframe-title').textContent=(mode==='cumulative'?'Cumulative sequence':'Trailing 7-day sequence')+' at t = '+(t>=0?'+':'')+t.toFixed(1)+' days';")
extra="initAnim(); window.animationAudit={setTime:t=>{setAnimPlaying(false);animT=t;renderAnimFrame();},counts:()=>animData.map(d=>animVisible(d,animT,$('anim-mode').value).length),data:()=>animData,playing:()=>animPlaying};"
shell+='<script>'+get_plotlyjs()+'</script><script id="catalogue" type="application/json">'+safe_json(d)+'</script><script>'+helpers+anim+extra+'</script></html>'
target=ROOT/'outputs/final/animation.html';target.write_text(shell,encoding='utf-8')
print(f'Animation built with {len(d["rows"])} case observations; standalone offline file.')
