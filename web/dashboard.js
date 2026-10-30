'use strict';
const DATA = JSON.parse(document.getElementById('catalogue').textContent);
const ROWS = DATA.rows;
const COLORS = ['#2166ac','#cc8b19','#8e4b98','#777777'];
const REGION_COLORS = ['#2166ac','#b06816','#8e4b98','#57823b','#b14f76','#4b8793','#656565'];
const $ = id => document.getElementById(id);
const number = value => value.toLocaleString('en-US');
const escapeText = value => String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const median = values => { if (!values.length) return null; const a = values.slice().sort((x,y)=>x-y); const m=Math.floor(a.length/2); return a.length%2?a[m]:(a[m-1]+a[m])/2; };
const range = (start,end) => Array.from({length:end-start+1},(_,i)=>start+i);
const year = row => Number(row[1].slice(0,4));
const sample = (rows,cap=8000) => rows.length<=cap?rows:range(0,cap-1).map(i=>rows[Math.floor(i*rows.length/cap)]);
const groups = rows => DATA.depth_names.map((name,i)=>({name,rows:rows.filter(r=>r[8]===i),color:COLORS[i]}));
const chartConfig = {responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['select2d','lasso2d'],toImageButtonOptions:{format:'png',scale:2}};
const layout = extra => ({paper_bgcolor:'#fff',plot_bgcolor:'#fff',font:{family:'Segoe UI, sans-serif',size:12,color:'#263c4e'},
    margin:{l:62,r:25,t:26,b:65},hovermode:'closest',showlegend:false,
    xaxis:{gridcolor:'#e5ebef',zeroline:false,automargin:true},yaxis:{gridcolor:'#e5ebef',zeroline:false,automargin:true},...extra});
function plot(id,traces,extra={}) { return Plotly.react($(id),traces,layout(extra),chartConfig); }
function empty(id,message='No events match this selection') {
    return plot(id,[],{xaxis:{visible:false},yaxis:{visible:false},annotations:[{text:message,x:.5,y:.5,xref:'paper',yref:'paper',showarrow:false,font:{size:16,color:'#586b7c'}}]});
}
function flattenedLines(lines,transform=p=>p) {
    const x=[],y=[];
    for (const line of lines) {
        let previous=null;
        for (const point of line) {
            const p=transform(point);
            if (previous!==null && Math.abs(p[0]-previous)>180) { x.push(null); y.push(null); }
            x.push(p[0]);y.push(p[1]);previous=p[0];
        }
        x.push(null);y.push(null);
    }
    return {x,y};
}
const coastLines=flattenedLines(DATA.coast);
const boundaryLines=flattenedLines(DATA.boundaries);
const mapBase=()=>[
    {type:'scatter',mode:'lines',...flattenedLines(DATA.land),fill:'toself',fillcolor:'#edf0eb',line:{width:0,color:'#edf0eb'},hoverinfo:'skip',showlegend:false},
    {type:'scatter',mode:'lines',...coastLines,line:{color:'#8a9ca9',width:.65},hoverinfo:'skip',showlegend:false},
    {type:'scatter',mode:'lines',...boundaryLines,line:{color:'#687783',width:.8},hoverinfo:'skip',showlegend:false}
];
function eventTrace(rows,color,name) {
    return {type:'scattergl',mode:'markers',name,x:rows.map(r=>r[3]),y:rows.map(r=>r[2]),
        marker:{size:4,color,opacity:.65},customdata:rows.map(r=>[escapeText(r[0]),r[1],r[5],r[4]===null?'Missing':r[4]+' km',r[6].toFixed(1),escapeText(r[9])]),
        hovertemplate:'%{customdata[0]}<br>%{customdata[1]}<br>Longitude %{x:.3f}° · Latitude %{y:.3f}°<br>M %{customdata[2]} · Depth %{customdata[3]}<br>Boundary %{customdata[4]} km<br>%{customdata[5]}<extra>'+escapeText(name)+'</extra>'};
}
function histogram(values,low,width,bins) {
    const counts=Array(bins).fill(0);
    for(const v of values) { const i=Math.floor((v-low)/width+1e-9); if(i>=0&&i<bins)counts[i]++; }
    return {x:counts.map((_,i)=>low+(i+.5)*width),y:counts};
}
let currentTab='overview', selected=[], busy=false, pending=false, renderCount=0;
for(const y of range(DATA.config.start_year,DATA.config.end_year)) {
    $('year-start').add(new Option(y,y));$('year-end').add(new Option(y,y));
}
$('year-end').value=DATA.config.end_year;
DATA.regions.forEach((r,i)=>{ $('region').add(new Option(r,i));$('section-region').add(new Option(r,i)); });
DATA.cases.forEach((c,i)=>$('case-select').add(new Option(c.name,i)));
function filteredRows() {
    const lo=+$('year-start').value,hi=+$('year-end').value,min=+$('min-mag').value,reg=$('region').value,depth=$('depth-class').value;
    return ROWS.filter(r=>year(r)>=lo&&year(r)<=hi&&r[5]>=min&&(reg==='all'||r[7]===+reg)&&(depth==='all'||r[8]===+depth));
}
function updateMetrics(rows) {
    $('count').textContent=number(rows.length);
    const d=median(rows.filter(r=>r[4]!==null).map(r=>r[4]));
    const b=median(rows.map(r=>r[6]));
    $('median-depth').textContent=d===null?'—':d.toFixed(1)+' km';
    $('median-distance').textContent=b===null?'—':b.toFixed(1)+' km';
    $('near-boundary').textContent=rows.length?(100*rows.filter(r=>r[6]<=100).length/rows.length).toFixed(1)+'%':'—';
}
async function renderWorld(rows) {
    if(!rows.length) { $('world-note').textContent='The geographic background and other charts return when the filters include events.'; return empty('world'); }
    if($('world-view').value==='globe') return renderGlobe(rows);
    const traces=mapBase();
    for(const g of groups(rows))if(g.rows.length)traces.push(eventTrace(g.rows,g.color,g.name));
    $('world-note').textContent=number(rows.length)+' selected events are plotted. Grey lines show PB2002 boundaries; the coastline and land come from Natural Earth.';
    return plot('world',traces,{showlegend:true,legend:{orientation:'h',x:0,y:1.08},margin:{l:58,r:20,t:35,b:55},
        xaxis:{title:'Longitude (degrees)',range:[-180,180],constrain:'domain',dtick:60,gridcolor:'#e7edf2',zeroline:false},
        yaxis:{title:'Latitude (degrees)',range:[-90,90],constrain:'domain',dtick:30,scaleanchor:'x',scaleratio:1,gridcolor:'#e7edf2',zeroline:false},uirevision:'world-map'});
}
function xyz(lon,lat,radius=1) {
    const a=lon*Math.PI/180,b=lat*Math.PI/180;
    return [radius*Math.cos(b)*Math.cos(a),radius*Math.cos(b)*Math.sin(a),radius*Math.sin(b)];
}
function lines3d(lines,radius,color,width) {
    const x=[],y=[],z=[];
    for(const line of lines) { for(const point of line) {const p=xyz(point[0],point[1],radius);x.push(p[0]);y.push(p[1]);z.push(p[2]);} x.push(null);y.push(null);z.push(null); }
    return {type:'scatter3d',mode:'lines',x,y,z,line:{color,width},hoverinfo:'skip',showlegend:false};
}
async function renderGlobe(rows) {
    const x=[],y=[],z=[];
    for(let j=0;j<=60;j++) { const xx=[],yy=[],zz=[];for(let i=0;i<=120;i++) {const p=xyz(-180+3*i,-90+3*j);xx.push(p[0]);yy.push(p[1]);zz.push(p[2]);}x.push(xx);y.push(yy);z.push(zz); }
    const traces=[{type:'surface',x,y,z,surfacecolor:DATA.globe_land,colorscale:[[0,'#dcebf4'],[1,'#abbfb0']],cmin:0,cmax:1,showscale:false,hoverinfo:'skip',lighting:{ambient:.8,diffuse:.5},opacity:1},
        lines3d(DATA.coast,1.002,'#7b8d89',1),lines3d(DATA.boundaries,1.004,'#5d6f7c',2)];
    const shown=sample(rows);
    for(const g of groups(shown))if(g.rows.length) {
        const p=g.rows.map(r=>xyz(r[3],r[2],1.012));
        traces.push({type:'scatter3d',mode:'markers',name:g.name,x:p.map(v=>v[0]),y:p.map(v=>v[1]),z:p.map(v=>v[2]),
            marker:{size:2.2,color:g.color,opacity:.8},customdata:g.rows.map(r=>[escapeText(r[0]),r[1],r[5],r[4]===null?'Missing':r[4],r[2],r[3]]),
            hovertemplate:'%{customdata[0]}<br>%{customdata[1]}<br>Lat %{customdata[4]}° · Lon %{customdata[5]}°<br>M %{customdata[2]} · Depth %{customdata[3]} km<extra>'+escapeText(g.name)+'</extra>'});
    }
    $('world-note').textContent='Drag to rotate; scroll/trackpad to zoom. '+number(shown.length)+' of '+number(rows.length)+' selected events shown'+(shown.length<rows.length?' by deterministic time-order sampling for browser performance.':'.')+' Counts and summaries use every selected event. Points mark epicentres on the surface; depth is encoded by color.';
    return plot('world',traces,{showlegend:true,legend:{orientation:'h',y:1.05},margin:{l:0,r:0,b:0,t:25},scene:{
        xaxis:{visible:false,range:[-1.1,1.1]},yaxis:{visible:false,range:[-1.1,1.1]},zaxis:{visible:false,range:[-1.1,1.1]},
        aspectmode:'cube',camera:{eye:{x:-1.0,y:1.1,z:.5}},bgcolor:'#fff'},uirevision:'world-globe'});
}
async function renderOverview(rows) {
    const years=range(+$('year-start').value,+$('year-end').value),counts=years.map(y=>rows.filter(r=>year(r)===y).length);
    const regional=DATA.regions.map((_,i)=>rows.filter(r=>r[7]===i).length);
    await Promise.all([renderWorld(rows),
        plot('annual',[{type:'scatter',mode:'lines+markers',x:years,y:counts,line:{color:COLORS[0],width:2},marker:{size:5},hovertemplate:'%{x}: %{y:,} events<extra></extra>'}],
            {xaxis:{title:'Year (UTC)',dtick:5,range:[years[0]-.3,years.at(-1)+.3]},yaxis:{title:'Earthquake count',rangemode:'tozero'}}),
        plot('regional',[{type:'bar',orientation:'h',y:DATA.regions,x:regional,marker:{color:COLORS[0]},hovertemplate:'%{y}<br>%{x:,} events<extra></extra>'}],
            {margin:{l:195,r:25,t:20,b:55},xaxis:{title:'Earthquake count',rangemode:'tozero'},yaxis:{autorange:'reversed',automargin:true}})]);
}
async function renderBoundaries(rows) {
    if(!rows.length)return Promise.all([empty('distance-hist'),empty('distance-ecdf')]);
    const max=Math.max(...rows.map(r=>r[6])),width=Math.max(1,Math.ceil(max/45));
    const hist=histogram(rows.map(r=>r[6]),0,width,Math.ceil(max/width)+1);
    const ecdf=[];
    DATA.regions.forEach((name,i)=>{const v=rows.filter(r=>r[7]===i).map(r=>r[6]).sort((a,b)=>a-b);if(v.length)ecdf.push({
        type:'scatter',mode:'lines',name:name+' (n='+number(v.length)+')',x:v,y:v.map((_,j)=>(j+1)/v.length*100),line:{shape:'hv',color:REGION_COLORS[i],width:1.8},
        hovertemplate:'%{x:.1f} km: %{y:.1f}%<extra>'+escapeText(name)+'</extra>'});});
    await Promise.all([plot('distance-hist',[{type:'bar',...hist,width:width*.97,marker:{color:COLORS[0]},hovertemplate:'Bin centre %{x:.1f} km<br>%{y:,} events<extra></extra>'}],
        {xaxis:{title:'Nearest mapped boundary (km)'},yaxis:{title:'Earthquake count',rangemode:'tozero'},bargap:.02}),
        plot('distance-ecdf',ecdf,{showlegend:true,legend:{orientation:'h',y:-.3,font:{size:10}},margin:{l:60,r:20,t:20,b:145},
            xaxis:{title:'Nearest mapped boundary (km)'},yaxis:{title:'Events at or below distance (%)',range:[0,101]}})]);
}
async function renderSection(rows) {
    const index=+$('section-region').value;
    const part=rows.filter(r=>r[7]===index&&r[4]!==null),name=DATA.regions[index];
    $('section-note').textContent=name+' · '+number(part.length)+' events with known depth from the current filters. All latitudes in the box are projected together; this is not a narrow trench-normal section. Vertical scale is exaggerated.';
    if(!part.length)return empty('cross-section','No selected events in '+escapeText(name));
    const box=DATA.config.regions[index],wrap=box&&box.lon[0]>box.lon[1];
    const lon=r=>wrap&&r[3]<0?r[3]+360:r[3];
    if($('section-view').value==='3d') {
        const shown=sample(part),lon0=median(part.map(lon)),lat0=median(part.map(r=>r[2]));
        const traces=groups(shown).filter(g=>g.rows.length).map(g=>({type:'scatter3d',mode:'markers',name:g.name,
            x:g.rows.map(r=>(lon(r)-lon0)*111.195*Math.cos(lat0*Math.PI/180)),y:g.rows.map(r=>(r[2]-lat0)*111.195),z:g.rows.map(r=>-r[4]),
            marker:{size:2.5,color:g.color},customdata:g.rows.map(r=>[escapeText(r[0]),r[4],r[5]]),
            hovertemplate:'%{customdata[0]}<br>Depth %{customdata[1]} km · M %{customdata[2]}<extra>'+escapeText(g.name)+'</extra>'}));
        $('section-note').textContent+=' Local east/north coordinates use an equirectangular approximation in km. This projection is for display only; it is not used in distance analysis. '+number(shown.length)+' of '+number(part.length)+' plotted.';
        return plot('cross-section',traces,{showlegend:true,scene:{xaxis:{title:'East (km)'},yaxis:{title:'North (km)'},zaxis:{title:'Vertical (km)',range:[-750,10]},aspectmode:'manual',aspectratio:{x:1.3,y:1.3,z:.8}},margin:{l:10,r:10,b:50,t:25},uirevision:'section-3d-'+index});
    }
    const traces=groups(part).filter(g=>g.rows.length).map(g=>({type:'scattergl',mode:'markers',name:g.name,x:g.rows.map(lon),y:g.rows.map(r=>r[4]),marker:{size:4,color:g.color,opacity:.6},
        customdata:g.rows.map(r=>[escapeText(r[0]),r[5]]),hovertemplate:'%{customdata[0]}<br>Longitude %{x:.3f}°<br>Depth %{y:.1f} km · M %{customdata[1]}<extra>'+escapeText(g.name)+'</extra>'}));
    return plot('cross-section',traces,{showlegend:true,legend:{orientation:'h',y:1.06},xaxis:{title:'Longitude (degrees east, unwrapped)'},yaxis:{title:'Depth (km; positive down)',autorange:'reversed'}});
}
async function renderDepth(rows) {
    const known=rows.filter(r=>r[4]!==null);
    if(!known.length)return Promise.all([empty('depth-hist','No selected events with known depth'),empty('depth-box','No selected events with known depth'),renderSection(rows)]);
    const min=Math.min(-10,...known.map(r=>r[4])),max=Math.max(710,...known.map(r=>r[4])),width=10;
    const h=histogram(known.map(r=>r[4]),Math.floor(min/10)*10,width,Math.ceil((max-min)/width)+1);
    const boxes=DATA.regions.map((name,i)=>({type:'box',orientation:'h',name,y:rows.filter(r=>r[7]===i&&r[4]!==null).map(()=>name),
        x:rows.filter(r=>r[7]===i&&r[4]!==null).map(r=>r[4]),boxpoints:false,marker:{color:REGION_COLORS[i]},line:{width:1.4},hovertemplate:'%{x:.1f} km<extra>'+escapeText(name)+'</extra>'}));
    await Promise.all([plot('depth-hist',[{type:'bar',...h,width:9.7,marker:{color:COLORS[0]}}],{xaxis:{title:'Depth (km)'},yaxis:{title:'Earthquake count',rangemode:'tozero'},bargap:.02}),
        plot('depth-box',boxes,{margin:{l:195,r:25,t:20,b:55},xaxis:{title:'Depth (km)'},yaxis:{categoryorder:'array',categoryarray:DATA.regions,autorange:'reversed'}}),renderSection(rows)]);
}
async function renderMagnitude(rows) {
    if(!rows.length)return Promise.all([empty('mag-hist'),empty('mag-frequency'),empty('relationship')]);
    const h=histogram(rows.map(r=>r[5]),5,.1,50);
    const mags=rows.map(r=>r[5]).sort((a,b)=>a-b),x=[],y=[];
    mags.forEach((m,i)=>{if(i===0||m!==mags[i-1]){x.push(m);y.push(mags.length-i);}});
    const known=rows.filter(r=>r[4]!==null),shown=sample(known);
    $('relationship-note').textContent=number(shown.length)+' of '+number(known.length)+' selected events with known depth shown'+(known.length>shown.length?' by deterministic time-order sampling.':'.')+' All selected records are used in the magnitude frequency curves. Exact pairwise and subgroup Spearman coefficients are in outputs/tables/spearman_correlations.csv.';
    await Promise.all([plot('mag-hist',[{type:'bar',...h,width:.097,marker:{color:COLORS[0]}}],{xaxis:{title:'Preferred magnitude',range:[5,9.5]},yaxis:{title:'Earthquake count',rangemode:'tozero'},bargap:.02}),
        plot('mag-frequency',[{type:'scatter',mode:'lines+markers',x,y,line:{color:COLORS[0],shape:'vh'},marker:{size:3},hovertemplate:'M ≥ %{x}: %{y:,} events<extra></extra>'}],
            {xaxis:{title:'Magnitude threshold m',range:[5,9.5]},yaxis:{title:'Recorded events with M ≥ m',type:'log'}}),
        known.length?plot('relationship',groups(shown).filter(g=>g.rows.length).map(g=>({type:'scattergl',mode:'markers',name:g.name,x:g.rows.map(r=>r[5]),y:g.rows.map(r=>r[4]),marker:{size:4,color:g.color,opacity:.5},customdata:g.rows.map(r=>escapeText(r[0])),hovertemplate:'%{customdata}<br>M %{x} · Depth %{y} km<extra>'+escapeText(g.name)+'</extra>'})),
            {showlegend:true,legend:{orientation:'h',y:1.08},xaxis:{title:'Magnitude'},yaxis:{title:'Depth (km)'}}):empty('relationship','No selected events with known depth')]);
}
async function renderCases() {
    const c=DATA.cases[+$('case-select').value],rows=c.indices.map(i=>ROWS[i]),offset=x=>c.anchor_longitude+(x-c.anchor_longitude+540)%360-180;
    const before=[],after=[];rows.forEach((r,i)=>(c.relative_days[i]<0?before:after).push(r));
    $('case-stats').textContent='Anchor M'+c.anchor_magnitude+' · '+c.anchor_time+' · '+number(c.before_count)+' before / '+number(c.after_count)+' after · '+(c.fully_observed?'Both windows fully observed':'INCOMPLETE OBSERVATION WINDOW');
    const lines=flattenedLines(DATA.coast,p=>[offset(p[0]),p[1]]),bounds=flattenedLines(DATA.boundaries,p=>[offset(p[0]),p[1]]);
    const traces=[{type:'scatter',mode:'lines',...lines,line:{color:'#a1afb8',width:.7},hoverinfo:'skip',showlegend:false},
        {type:'scatter',mode:'lines',...bounds,line:{color:'#60798b',width:.8},hoverinfo:'skip',showlegend:false}];
    for(const [part,color,name] of [[before,COLORS[0],'Before'],[after,COLORS[1],'After']]) {
        const trace=eventTrace(part,color,name);trace.x=part.map(r=>offset(r[3]));traces.push(trace);
    }
    traces.push({type:'scatter',mode:'markers',name:'Anchor',x:[c.anchor_longitude],y:[c.anchor_latitude],marker:{symbol:'star',size:15,color:'#152e42'},hovertemplate:'Anchor M'+c.anchor_magnitude+'<extra></extra>'});
    const dy=c.radius_km/111.195*1.15,dx=dy/Math.cos(c.anchor_latitude*Math.PI/180);
    const counts=Array(60).fill(0);c.relative_days.forEach(d=>{const i=Math.floor(d+30);if(i>=0&&i<60)counts[i]++;});
    await Promise.all([plot('case-map',traces,{showlegend:true,legend:{orientation:'h',y:1.1},xaxis:{title:'Longitude (degrees)',range:[c.anchor_longitude-dx,c.anchor_longitude+dx]},yaxis:{title:'Latitude (degrees)',range:[c.anchor_latitude-dy,c.anchor_latitude+dy]}}),
        plot('case-timeline',[{type:'bar',x:range(-30,29).map(d=>d+.5),y:counts,width:.95,marker:{color:range(-30,29).map(d=>d<0?COLORS[0]:COLORS[1])},hovertemplate:'Bin centre %{x:.1f} days<br>%{y} M ≥ 5 events<extra></extra>'}],
            {xaxis:{title:'Days relative to anchor (UTC)',range:[-30,30]},yaxis:{title:'M ≥ 5 events per one-day bin',rangemode:'tozero'},shapes:[{type:'line',x0:0,x1:0,y0:0,y1:1,yref:'paper',line:{color:'#213e54',dash:'dash',width:1}}]})]);
}
async function update() {
    pending=true;
    if(busy)return;
    busy=true;
    try {
        while(pending) {
            pending=false;
            $('status').textContent='Updating views…';
            const cases=currentTab==='cases';
            $('global-filters').hidden=cases;$('metrics').hidden=cases;
            selected=filteredRows();updateMetrics(selected);
            if(currentTab==='overview')await renderOverview(selected);
            else if(currentTab==='boundaries')await renderBoundaries(selected);
            else if(currentTab==='depth')await renderDepth(selected);
            else if(currentTab==='magnitude')await renderMagnitude(selected);
            else await renderCases();
            renderCount++;
            $('status').textContent=cases?'Fixed case-study window · M ≥ 5 · global filters do not apply':number(selected.length)+' of '+number(ROWS.length)+' catalogue events selected · '+$('year-start').value+'–'+$('year-end').value+' UTC';
        }
    } catch(error) {
        $('status').textContent='This view could not be rendered: '+error.message;
        console.error(error);
    } finally { busy=false; }
}
document.querySelectorAll('[data-tab]').forEach(button=>button.addEventListener('click',()=>{
    currentTab=button.dataset.tab;
    document.querySelectorAll('[data-tab]').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-current',b===button?'page':'false');});
    document.querySelectorAll('[data-panel]').forEach(p=>p.hidden=p.dataset.panel!==currentTab);
    update();
}));
for(const id of ['year-start','year-end','min-mag','region','depth-class','world-view','section-region','section-view','case-select'])$(id).addEventListener('change',()=>{
    if(+$('year-start').value>+$('year-end').value)$(id==='year-start'?'year-end':'year-start').value=$(id).value;
    update();
});
$('reset').addEventListener('click',()=>{ $('year-start').value=DATA.config.start_year;$('year-end').value=DATA.config.end_year;$('min-mag').value='5';$('region').value='all';$('depth-class').value='all';update(); });
window.earthquakeApp={getState:()=>({busy,renderCount,currentTab,selectedCount:selected.length,totalCount:ROWS.length})};
update();
