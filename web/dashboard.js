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
async function plot(id,traces,extra={}) {
    const chart=await Plotly.react($(id),traces,layout(extra),chartConfig);
    if(chart.clientWidth>0&&chart.clientHeight>0&&
        (Math.abs(chart.clientWidth-chart._fullLayout.width)>.5||Math.abs(chart.clientHeight-chart._fullLayout.height)>.5)) {
        await Plotly.Plots.resize(chart);
    }
    return chart;
}
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
DATA.regions.forEach((r,i)=>{ $('region').add(new Option(r,i));$('section-region').add(new Option(r==='Other'?'Other regions':r,i)); });
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
async function renderProfileSection(rows) {
    const section=DATA.sections[DATA.regions[+$('section-region').value]];
    const selectedRows=new Map(rows.map(row=>[row[0],row]));
    const events=section.events.filter(([id])=>selectedRows.has(id))
        .map(([id,distance,offset])=>({row:selectedRows.get(id),distance,offset}));
    const coordinateLabel=([lon,lat])=>Math.abs(lon).toFixed(2)+'°'+(lon>=0?'E':'W')+', '+Math.abs(lat).toFixed(2)+'°'+(lat>=0?'N':'S');
    const wrapLongitude=lon=>((lon+180)%360+360)%360-180;
    const project=([lon,lat])=>[section.central_longitude+wrapLongitude(lon-section.central_longitude),lat];
    const longitudeLabel=lon=>Math.abs(wrapLongitude(lon)).toFixed(0)+'°'+(wrapLongitude(lon)>=0?'E':'W');
    $('section-location').textContent=section.name+' · Known-depth events N = '+number(events.length)+' · Half-width '+section.half_width_km+' km · Equal km scale';
    $('section-endpoint-a').textContent='A (start) — '+section.a.place+' ('+coordinateLabel(section.a.coordinates)+')';
    $('section-endpoint-b').textContent='B (end) — '+section.b.place+' ('+coordinateLabel(section.b.coordinates)+')';
    $('section-method').textContent=section.method;
    $('section-reference').href=section.reference;

    const mapTraces=mapBase().slice(0,2);
    mapTraces[0]={...mapTraces[0],...flattenedLines(DATA.land,project)};
    mapTraces[1]={...mapTraces[1],...flattenedLines(DATA.coast,project)};
    const swath=section.swath.map(project);
    mapTraces.push({type:'scatter',mode:'lines',x:swath.map(p=>p[0]),y:swath.map(p=>p[1]),
        fill:'toself',fillcolor:'rgba(33,102,172,.09)',line:{color:'#7c9fb9',width:1,dash:'dot'},
        name:'Swath ±100 km',hoverinfo:'skip',showlegend:true});
    const trench=flattenedLines(section.trench,project);
    mapTraces.push({type:'scatter',mode:'lines',...trench,line:{color:'#465768',width:1.6,dash:'dash'},
        name:section.trench_name+' · PB2002',hoverinfo:'skip',showlegend:true});
    const profileTraces=[];
    const classNames=['Shallow','Intermediate','Deep'];
    classNames.forEach((name,index)=>{
        const part=events.filter(event=>event.row[8]===index);
        if(!part.length)return;
        const mapTrace=eventTrace(part.map(event=>event.row),COLORS[index],name);
        mapTrace.x=part.map(event=>project([event.row[3],event.row[2]])[0]);
        mapTrace.customdata=part.map(event=>[escapeText(event.row[0]),event.row[1],event.row[5],coordinateLabel([event.row[3],event.row[2]]),event.row[4]]);
        mapTrace.hovertemplate='%{customdata[0]}<br>%{customdata[1]}<br>%{customdata[3]}<br>M %{customdata[2]} · Depth %{customdata[4]:.1f} km<extra>'+escapeText(name)+'</extra>';
        mapTrace.showlegend=false;
        mapTraces.push(mapTrace);
        profileTraces.push({type:'scatter',mode:'markers',name,
            x:part.map(event=>event.distance),y:part.map(event=>event.row[4]),
            marker:{size:4.5,color:COLORS[index],opacity:.65},
            customdata:part.map(event=>[escapeText(event.row[0]),event.row[1],event.row[5],event.offset]),
            hovertemplate:'Distance from trench %{x:.1f} km<br>Depth %{y:.1f} km · M %{customdata[2]}<br>%{customdata[1]}<br>%{customdata[0]}<extra>'+escapeText(name)+'</extra>'});
    });
    const route=section.route.map(project);
    mapTraces.push({type:'scatter',mode:'lines',x:route.map(p=>p[0]),y:route.map(p=>p[1]),
        line:{color:'#102b42',width:2},hoverinfo:'skip',showlegend:false});
    const endpoints=[section.a,section.b];
    mapTraces.push({type:'scatter',mode:'markers+text',x:endpoints.map(p=>project(p.coordinates)[0]),y:endpoints.map(p=>p.coordinates[1]),
        text:['A · Start','B · End'],textposition:['middle right','middle left'],textfont:{size:12,color:'#102b42'},
        marker:{size:8,symbol:['circle','square'],color:'#102b42',line:{color:'white',width:1}},
        customdata:endpoints.map(p=>[p.place,coordinateLabel(p.coordinates)]),hovertemplate:'%{text} · %{customdata[0]}<br>%{customdata[1]}<extra></extra>',showlegend:false});
    const arrowStart=route[39],arrowEnd=route[43];
    const mapAnnotations=[{x:arrowEnd[0],y:arrowEnd[1],ax:arrowStart[0],ay:arrowStart[1],xref:'x',yref:'y',axref:'x',ayref:'y',
        text:'',showarrow:true,arrowhead:2,arrowsize:1.2,arrowwidth:2,arrowcolor:'#102b42'},
        ...section.map_labels.map(([lon,lat,text])=>({x:project([lon,lat])[0],y:lat,text,showarrow:false,font:{size:11,color:'#586b7c'}}))];
    const annotations=section.distance_range_km.map((distance,index)=>({x:distance,y:1.02,xref:'x',yref:'y domain',text:index===0?'A · Start':'B · End',
        showarrow:false,xanchor:index===0?'left':'right',yanchor:'bottom',font:{size:12,color:'#102b42'}}));
    if(!events.length)annotations.push({x:.5,y:.5,xref:'paper',yref:'paper',text:'No selected known-depth events in this swath',showarrow:false});
    const longitudeTicks=range(Math.ceil(section.map_longitude_range[0]/5),Math.floor(section.map_longitude_range[1]/5)).map(value=>value*5);
    const distanceTicks=range(section.distance_range_km[0]/200,section.distance_range_km[1]/200).map(value=>value*200);
    await Promise.all([
        plot('section-map',mapTraces,{showlegend:true,legend:{orientation:'h',x:0,y:1.17,font:{size:10}},margin:{l:47,r:15,t:50,b:48},
            annotations:mapAnnotations,xaxis:{title:'Longitude',range:section.map_longitude_range,tickvals:longitudeTicks,ticktext:longitudeTicks.map(longitudeLabel),zeroline:false},
            yaxis:{title:'Latitude (°)',range:section.map_latitude_range,dtick:5,scaleanchor:'x',scaleratio:1/Math.cos(section.origin[1]*Math.PI/180),zeroline:false}}),
        plot('section-profile',profileTraces,{showlegend:true,legend:{orientation:'h',x:0,y:1.17,font:{size:11}},margin:{l:62,r:20,t:50,b:65},
            annotations,xaxis:{title:'Distance from trench (km)',range:section.distance_range_km,tickvals:distanceTicks,
                ticktext:distanceTicks.map(value=>value===0?'0<br>Trench':number(value)),constrain:'domain',zeroline:false},
            yaxis:{title:'Depth (km)',range:section.depth_range_km.slice().reverse(),dtick:100,scaleanchor:'x',scaleratio:1,constrain:'domain',zeroline:false},
            shapes:[{type:'line',x0:0,x1:0,y0:0,y1:1,yref:'y domain',line:{color:'#8495a2',width:1,dash:'dash'}},
                ...[70,300].map(depth=>({type:'line',x0:0,x1:1,xref:'x domain',y0:depth,y1:depth,line:{color:'#a5afb7',width:.8,dash:'dot'}}))]})
    ]);
}
async function renderSection(rows) {
    const index=+$('section-region').value;
    const part=rows.filter(r=>r[7]===index&&r[4]!==null),name=DATA.regions[index];
    const profileView=$('section-view').value==='profile';
    const threeDView=$('section-view').value==='3d';
    const contextView=threeDView&&index===0;
    $('cross-section').classList.toggle('is-3d',threeDView);
    $('cross-section').classList.toggle('has-depth-guides',contextView);
    $('section-preview').hidden=!profileView;
    $('cross-section').hidden=profileView;
    $('section-note').hidden=profileView;
    $('section-intro').textContent=profileView?'Route map and local two-dimensional depth section.':
        threeDView?'Regional earthquake locations and depths. Drag to rotate; hover for event details.':
        'Choose a geographic box for a longitude–depth projection or local hypocentre view.';
    if(profileView)return renderProfileSection(rows);
    $('section-note').textContent=name+' · '+number(part.length)+' events with known depth from the current filters.'+
        (threeDView?'':' All latitudes in the box are projected together; this is not a narrow trench-normal section. Vertical scale is exaggerated.');
    if(!part.length)return empty('cross-section','No selected events in '+escapeText(name));
    const box=DATA.config.regions[index],wrap=box&&box.lon[0]>box.lon[1];
    const lon=r=>wrap&&r[3]<0?r[3]+360:r[3];
    if(threeDView) {
        const regionalRows=ROWS.filter(r=>r[7]===index&&r[4]!==null);
        const shown=sample(part),lon0=median(regionalRows.map(lon)),lat0=median(regionalRows.map(r=>r[2]));
        const east=row=>(lon(row)-lon0)*111.195*Math.cos(lat0*Math.PI/180);
        const north=row=>(row[2]-lat0)*111.195;
        const extent=values=>{
            const low=Math.min(...values),high=Math.max(...values),padding=Math.max(25,(high-low)*.04);
            return [low-padding,high+padding];
        };
        const eastRange=extent(regionalRows.map(east)),northRange=extent(regionalRows.map(north));
        const maximumDepth=Math.max(750,...regionalRows.map(r=>r[4]));
        const depthRange=[-maximumDepth,-Math.min(-10,...regionalRows.map(r=>r[4]))];
        const spans=[eastRange[1]-eastRange[0],northRange[1]-northRange[0],depthRange[1]-depthRange[0]];
        const canvas=$('cross-section');
        const verticalExaggeration=Math.max(1,Math.max(spans[0],spans[1])*.5/spans[2]);
        const displaySpans=[spans[0],spans[1],spans[2]*verticalExaggeration];
        const margins=contextView?{l:40,r:40,b:50,t:100}:{l:40,r:40,b:55,t:55};
        const displaySpan=Math.min(contextView?1.9:1.8,(canvas.clientWidth-100)/(canvas.clientHeight-margins.t-margins.b)*(contextView?1:.9));
        const normalization=Math.max(...displaySpans)/displaySpan;
        const depthTicks=range(0,Math.floor(maximumDepth/150)).map(value=>value*150);
        const markerStyle={size:1.6,opacity:.8};
        const traces=groups(shown).filter(g=>g.rows.length).map(g=>({type:'scatter3d',mode:'markers',name:g.name,
            x:g.rows.map(east),y:g.rows.map(north),z:g.rows.map(r=>-r[4]),
            marker:{...markerStyle,color:g.color},customdata:g.rows.map(r=>[escapeText(r[0]),r[4],r[5]]),
            hovertemplate:'%{customdata[0]}<br>Depth %{customdata[1]} km · M %{customdata[2]}<extra>'+escapeText(g.name)+'</extra>'}));
        const sceneAnnotations=[];
        if(contextView) {
            for(const depth of [70,300]) {
                traces.push({type:'scatter3d',mode:'lines',name:depth+' km depth boundary',
                    x:[eastRange[0],eastRange[0],eastRange[1]],y:[northRange[0],northRange[1],northRange[1]],z:[-depth,-depth,-depth],
                    line:{color:'#8097a8',width:1.5,dash:'dash'},opacity:.8,hoverinfo:'skip',showlegend:false,meta:{kind:'depth-boundary',depth}});
                sceneAnnotations.push({x:eastRange[1],y:northRange[1],z:-depth,text:depth+' km',showarrow:false,
                    xanchor:'left',xshift:7,font:{size:10,color:'#586f80'},bgcolor:'rgba(255,255,255,.85)',borderpad:2});
            }
        }
        $('section-note').textContent+=' Horizontal axes use equal km scale; vertical exaggeration: '+verticalExaggeration.toFixed(1)+'×. East/north coordinates use a fixed regional reference and an equirectangular display approximation. '+number(shown.length)+' of '+number(part.length)+' events plotted.';
        if(contextView)$('section-note').textContent+=' Dashed guides mark the 70 km and 300 km depth-class boundaries.';
        const axisStyle={nticks:5,showbackground:true,backgroundcolor:'#f8fafc',gridcolor:'#dfe6ec',zeroline:false,showspikes:false,
            tickfont:{size:11,color:'#586b7c'},title:{font:{size:12,color:'#263c4e'}}};
        const horizontalTicks=span=>span<Math.max(spans[0],spans[1])*.5?3:5;
        return plot('cross-section',traces,{showlegend:true,legend:{orientation:'h',x:contextView?0.02:0,y:contextView?1.06:1.08,itemsizing:'constant'},
            ...(contextView?{title:{text:escapeText(name)+'<br><span style="font-size:12px;color:#586b7c">3D hypocentres</span>',x:.04,y:.94,xanchor:'left',yanchor:'top',font:{size:18,color:'#263c4e'}}}:{}),
            scene:{xaxis:{...axisStyle,backgroundcolor:contextView?'#f0f5f9':axisStyle.backgroundcolor,nticks:horizontalTicks(spans[0]),title:{...axisStyle.title,text:'East (km)'},range:eastRange},
                yaxis:{...axisStyle,backgroundcolor:contextView?'#f6f9fc':axisStyle.backgroundcolor,nticks:horizontalTicks(spans[1]),title:{...axisStyle.title,text:'North (km)'},range:northRange},
                zaxis:{...axisStyle,backgroundcolor:contextView?'#e8f0f6':axisStyle.backgroundcolor,title:{...axisStyle.title,text:'Depth (km)'},range:depthRange,tickvals:depthTicks.map(value=>-value),ticktext:depthTicks},
                annotations:sceneAnnotations,
                aspectmode:'manual',aspectratio:{x:displaySpans[0]/normalization,y:displaySpans[1]/normalization,z:displaySpans[2]/normalization},
                dragmode:'turntable',camera:{eye:{x:1.35,y:-1.45,z:.8},projection:{type:'orthographic'}}},
            margin:margins,uirevision:'section-3d-'+index});
    }
    const traces=groups(part).filter(g=>g.rows.length).map(g=>({type:'scattergl',mode:'markers',name:g.name,x:g.rows.map(lon),y:g.rows.map(r=>r[4]),marker:{size:4,color:g.color,opacity:.6},
        customdata:g.rows.map(r=>[escapeText(r[0]),r[5]]),hovertemplate:'%{customdata[0]}<br>Longitude %{x:.3f}°<br>Depth %{y:.1f} km · M %{customdata[1]}<extra>'+escapeText(g.name)+'</extra>'}));
    return plot('cross-section',traces,{showlegend:true,legend:{orientation:'h',y:1.06},xaxis:{title:'Longitude (degrees east, unwrapped)'},yaxis:{title:'Depth (km; positive down)',autorange:'reversed'}});
}
function depthShade(color,depthClass) {
    const tint=[.5,0,-.27][depthClass];
    const rgb=parseInt(color.slice(1),16);
    const target=tint>0?255:0;
    const channels=[16,8,0].map(shift=>{
        const channel=(rgb>>shift)&255;
        return Math.round(channel+(target-channel)*Math.abs(tint));
    });
    return 'rgb('+channels.join(',')+')';
}
function boxPercentile(sorted,fraction) {
    // Match the linear quartile calculation used by Plotly box traces.
    const index=Math.max(0,Math.min(sorted.length-1,sorted.length*fraction-.5));
    const lower=Math.floor(index),weight=index-lower;
    return sorted[lower]*(1-weight)+sorted[Math.ceil(index)]*weight;
}
const depthTooltip=$('depth-box-tooltip');
let depthHoverBound=false;
function hideDepthTooltip() { depthTooltip.hidden=true; }
function showDepthTooltip({points,event}) {
    const box=points[0]?.data;
    if(box?.type!=='box'||!box.meta||!event) {
        hideDepthTooltip();
        return;
    }
    const {median,lower,upper}=box.meta;
    $('depth-tooltip-region').textContent=box.name;
    $('depth-tooltip-median').textContent='Median depth '+median.toFixed(1)+' km';
    $('depth-tooltip-range').textContent='Middle 50% '+lower.toFixed(1)+'–'+upper.toFixed(1)+' km';
    depthTooltip.style.borderLeftColor=box.marker.color;
    depthTooltip.hidden=false;
    const gap=12;
    depthTooltip.style.left=Math.max(gap,Math.min(event.clientX+gap,innerWidth-depthTooltip.offsetWidth-gap))+'px';
    const below=event.clientY+gap+depthTooltip.offsetHeight<=innerHeight-gap;
    depthTooltip.style.top=Math.max(gap,below?event.clientY+gap:event.clientY-depthTooltip.offsetHeight-gap)+'px';
}
async function renderRegionalDepth(rows) {
    hideDepthTooltip();
    const regionalLayout={margin:{l:195,r:25,t:20,b:55},yaxis:{categoryorder:'array',categoryarray:DATA.regions,autorange:'reversed'}};
    if($('regional-depth-view').value==='shares') {
        const counts=DATA.regions.map(()=>[0,0,0,0]);
        for(const row of rows)counts[row[7]][row[8]]++;
        const summaries=DATA.regions.map((name,i)=>({name,color:REGION_COLORS[i],counts:counts[i],known:counts[i][0]+counts[i][1]+counts[i][2]}))
            .filter(region=>region.known>0);
        if(!summaries.length)return empty('depth-box','No selected events with known depth');
        const depthNames=DATA.depth_names.slice(0,3);
        const traces=depthNames.map((name,i)=>({
            type:'bar',orientation:'h',name,marker:{color:summaries.map(region=>depthShade(region.color,i))},
            x:summaries.map(region=>100*region.counts[i]/region.known),y:summaries.map(region=>region.name),
            customdata:summaries.map(region=>[escapeText(region.name),region.counts[i],region.known,region.counts[3]]),
            hovertemplate:'%{customdata[0]}<br>%{customdata[1]:,} of %{customdata[2]:,} known depths (%{x:.1f}%)<br>%{customdata[3]:,} missing depths<extra>'+escapeText(name)+'</extra>'
        }));
        const regionIndex=+$('region').value;
        const title=DATA.regions[regionIndex]??'Share of known-depth events';
        const knownTotal=summaries.reduce((sum,region)=>sum+region.known,0);
        const keyColor=REGION_COLORS[regionIndex]??'#656565';
        const key=depthNames.map((name,i)=>'<span style="color:'+depthShade(keyColor,i)+'">■</span> '+escapeText(name)).join('　');
        return plot('depth-box',traces,{...regionalLayout,margin:{...regionalLayout.margin,t:45},barmode:'stack',bargap:.35,
            annotations:[{xref:'paper',yref:'paper',x:0,y:1.04,xanchor:'left',yanchor:'bottom',text:key,showarrow:false,font:{size:11}}],
            xaxis:{title:escapeText(title)+' · N = '+number(knownTotal),range:[0,100],dtick:25,ticksuffix:'%'},
            yaxis:{...regionalLayout.yaxis,automargin:true,ticks:'outside',ticklen:6,tickcolor:'transparent'}});
    }
    if(!rows.some(r=>r[4]!==null))return empty('depth-box','No selected events with known depth');
    const boxes=DATA.regions.map((name,i)=>{
        const depths=rows.filter(r=>r[7]===i&&r[4]!==null).map(r=>r[4]);
        const sorted=depths.slice().sort((a,b)=>a-b);
        const meta=sorted.length?{median:boxPercentile(sorted,.5),lower:boxPercentile(sorted,.25),upper:boxPercentile(sorted,.75)}:null;
        return {type:'box',orientation:'h',name,y:depths.map(()=>name),x:depths,meta,
            boxpoints:false,marker:{color:REGION_COLORS[i]},line:{width:1.4},hoveron:'boxes',hoverinfo:'none'};
    });
    const chart=await plot('depth-box',boxes,{...regionalLayout,xaxis:{title:'Depth (km)'}});
    if(!depthHoverBound) {
        chart.on('plotly_hover',showDepthTooltip);
        chart.on('plotly_unhover',hideDepthTooltip);
        chart.on('plotly_relayout',hideDepthTooltip);
        chart.addEventListener('pointerleave',hideDepthTooltip);
        window.addEventListener('scroll',hideDepthTooltip,{passive:true});
        depthHoverBound=true;
    }
    return chart;
}
async function renderDepth(rows) {
    const known=rows.filter(r=>r[4]!==null);
    if(!known.length)return Promise.all([empty('depth-hist','No selected events with known depth'),renderRegionalDepth(rows),renderSection(rows)]);
    const min=Math.min(-10,...known.map(r=>r[4])),max=Math.max(710,...known.map(r=>r[4])),width=10;
    const h=histogram(known.map(r=>r[4]),Math.floor(min/10)*10,width,Math.ceil((max-min)/width)+1);
    const color=REGION_COLORS[+$('region').value]??COLORS[0];
    await Promise.all([plot('depth-hist',[{type:'bar',...h,width:9.7,marker:{color}}],{xaxis:{title:'Depth (km)'},yaxis:{title:'Earthquake count',rangemode:'tozero'},bargap:.02}),
        renderRegionalDepth(rows),renderSection(rows)]);
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
    await Promise.all([plot('case-map',traces,{showlegend:true,legend:{orientation:'h',y:1.1},xaxis:{title:'Longitude (degrees)',range:[c.anchor_longitude-dx,c.anchor_longitude+dx],constrain:'domain'},yaxis:{title:'Latitude (degrees)',range:[c.anchor_latitude-dy,c.anchor_latitude+dy],scaleanchor:'x',scaleratio:1/Math.cos(c.anchor_latitude*Math.PI/180),constrain:'domain'}}),
        plot('case-timeline',[{type:'bar',x:range(-30,29).map(d=>d+.5),y:counts,width:.95,marker:{color:range(-30,29).map(d=>d<0?COLORS[0]:COLORS[1])},hovertemplate:'Bin centre %{x:.1f} days<br>%{y} M ≥ 5 events<extra></extra>'}],
            {xaxis:{title:'Days relative to anchor (UTC)',range:[-30,30]},yaxis:{title:'M ≥ 5 events per one-day bin',rangemode:'tozero'},shapes:[{type:'line',x0:0,x1:0,y0:0,y1:1,yref:'paper',line:{color:'#213e54',dash:'dash',width:1}}]})]);
}
let animData=null, animTimer=null, animT=-30, animPlaying=false, animReady=false;
const ANIM_WINDOW_DAYS=7, ANIM_TICK_MS=250;
function croppedLines(lines,transform,box){
    const [x0,x1,y0,y1]=box,x=[],y=[];
    for(const line of lines){
        let prevIn=false;
        for(const point of line){
            const p=transform(point);
            const inBox=p[0]>=x0&&p[0]<=x1&&p[1]>=y0&&p[1]<=y1;
            if(inBox){x.push(p[0]);y.push(p[1]);}else if(prevIn){x.push(null);y.push(null);}
            prevIn=inBox;
        }
        x.push(null);y.push(null);
    }
    return {x,y};
}
function animEventTrace(rows,color,name){
    return {type:'scattergl',mode:'markers',name,x:rows.map(r=>r[3]),y:rows.map(r=>r[2]),
        marker:{size:rows.map(r=>Math.max(3,Math.min(20,3+(r[5]-5)*3))),color,opacity:.7},
        customdata:rows.map(r=>[escapeText(r[0]),r[1],r[5],r[4]===null?'Missing':r[4]+' km',escapeText(r[9])]),
        hovertemplate:'%{customdata[0]}<br>%{customdata[1]}<br>Longitude %{x:.3f}° · Latitude %{y:.3f}°<br>M %{customdata[2]} · Depth %{customdata[3]}<br>%{customdata[4]}<extra>'+escapeText(name)+'</extra>'};
}
function buildAnimData(){
    animData=DATA.cases.map((c,ci)=>{
        const offset=x=>c.anchor_longitude+(x-c.anchor_longitude+540)%360-180;
        const rows=[],rels=[];
        c.indices.forEach((ri,k)=>{const r=ROWS[ri].slice();r[3]=offset(r[3]);rows.push(r);rels.push(c.relative_days[k]);});
        const order=rels.map((d,i)=>i).sort((a,b)=>rels[a]-rels[b]);
        const dy=c.radius_km/111.195*1.15,dx=dy/Math.max(.2,Math.cos(c.anchor_latitude*Math.PI/180));
        const box=[c.anchor_longitude-dx,c.anchor_longitude+dx,c.anchor_latitude-dy,c.anchor_latitude+dy];
        const counts=Array(60).fill(0);
        rels.forEach(d=>{const i=Math.floor(d+30);if(i>=0&&i<60)counts[i]++;});
        $('anim-title-'+ci).textContent=c.name;
        return {name:c.name,anchorLon:c.anchor_longitude,anchorLat:c.anchor_latitude,anchorMag:c.anchor_magnitude,
            anchorTimeMs:Date.parse(c.anchor_time),rows:order.map(i=>rows[i]),rels:order.map(i=>rels[i]),dy,dx,counts,
            coast:croppedLines(DATA.coast,p=>[offset(p[0]),p[1]],box),bounds:croppedLines(DATA.boundaries,p=>[offset(p[0]),p[1]],box)};
    });
    return animData;
}
function animVisible(cd,t,mode){
    const out=[];
    for(let i=0;i<cd.rels.length;i++){
        const d=cd.rels[i];
        if(d<=t+1e-9&&(mode==='cumulative'||d>t-ANIM_WINDOW_DAYS))out.push(cd.rows[i]);
    }
    return out;
}
function renderAnimMap(i,t,mode){
    const cd=animData[i],vis=animVisible(cd,t,mode);
    const traces=[{type:'scatter',mode:'lines',...cd.coast,line:{color:'#a1afb8',width:.7},hoverinfo:'skip',showlegend:false},
        {type:'scatter',mode:'lines',...cd.bounds,line:{color:'#60798b',width:.8},hoverinfo:'skip',showlegend:false}];
    for(const g of groups(vis))if(g.rows.length)traces.push(animEventTrace(g.rows,g.color,g.name));
    traces.push({type:'scatter',mode:'markers',name:'Anchor location (reference)',x:[cd.anchorLon],y:[cd.anchorLat],marker:{symbol:'star',size:15,color:'#152e42'},hovertemplate:'Reference location of anchor M'+cd.anchorMag+'<extra></extra>'});
    Plotly.react($('anim-map-'+i),traces,layout({showlegend:false,margin:{l:52,r:12,t:14,b:46},
        xaxis:{title:'Longitude (degrees)',range:[cd.anchorLon-cd.dx,cd.anchorLon+cd.dx],constrain:'domain'},
        yaxis:{title:'Latitude (degrees)',range:[cd.anchorLat-cd.dy,cd.anchorLat+cd.dy],scaleanchor:'x',scaleratio:1/Math.cos(cd.anchorLat*Math.PI/180),constrain:'domain'}}),chartConfig);
    const date=new Date(cd.anchorTimeMs+t*86400000).toISOString().slice(0,16).replace('T',' ');
    $('anim-stat-'+i).textContent=(mode==='cumulative'?number(vis.length)+' / '+number(cd.rows.length)+' revealed':'trailing '+ANIM_WINDOW_DAYS+' d · '+number(vis.length)+' events')+' · '+date+' UTC';
}
function renderAnimHistogram(t){
    const xs=range(-30,29).map(d=>d+.5);
    const traces=animData.map((cd,i)=>({type:'bar',name:cd.name,x:xs,y:cd.counts,
        marker:{color:REGION_COLORS[i],opacity:.6},hovertemplate:'%{x:.1f} days · %{y} events<extra>'+escapeText(cd.name)+'</extra>'}));
    Plotly.react($('anim-histogram'),traces,layout({barmode:'group',showlegend:true,legend:{orientation:'h',y:1.12},
        xaxis:{title:'Days relative to anchor (UTC)',range:[-30,30]},yaxis:{title:'M ≥ 5 events per one-day bin',rangemode:'tozero'},
        shapes:[{type:'line',x0:0,x1:0,y0:0,y1:1,yref:'paper',line:{color:'#213e54',dash:'dash',width:1}},
                {type:'line',x0:t,x1:t,y0:0,y1:1,yref:'paper',line:{color:'#b57b17',width:1.6}}]}),chartConfig);
}
function renderAnimFrame(){
    const t=animT,mode=$('anim-mode').value;
    $('anim-slider').value=t;
    $('anim-time-label').textContent='t = '+(t>=0?'+':'')+t.toFixed(1)+' d';
    for(let i=0;i<3;i++)renderAnimMap(i,t,mode);
    renderAnimHistogram(t);
}
function setAnimPlaying(on){
    animPlaying=on;
    $('anim-play').textContent=on?'Pause':'Play';
    clearInterval(animTimer);
    if(on)animTimer=setInterval(()=>{
        animT+=+$('anim-speed').value*(ANIM_TICK_MS/1000);
        if(animT>=30){animT=30;renderAnimFrame();setAnimPlaying(false);return;}
        renderAnimFrame();
    },ANIM_TICK_MS);
}
function initAnim(){
    const first=!animReady;
    if(first){
        animData=buildAnimData();
        animReady=true;
        animT=-30;
        $('anim-play').addEventListener('click',()=>{if(animPlaying)setAnimPlaying(false);else{if(animT>=30)animT=-30;setAnimPlaying(true);}});
        $('anim-reset').addEventListener('click',()=>{setAnimPlaying(false);animT=-30;renderAnimFrame();});
        $('anim-slider').addEventListener('input',()=>{setAnimPlaying(false);animT=parseFloat($('anim-slider').value);renderAnimFrame();});
        $('anim-speed').addEventListener('change',()=>{if(animPlaying)setAnimPlaying(true);});
        $('anim-mode').addEventListener('change',()=>renderAnimFrame());
    }
    renderAnimFrame();
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
            else { await renderCases(); initAnim(); }
            renderCount++;
            $('status').textContent=cases?'Fixed case-study window · M ≥ 5 · global filters do not apply':number(selected.length)+' of '+number(ROWS.length)+' catalogue events selected · '+$('year-start').value+'–'+$('year-end').value+' UTC';
        }
    } catch(error) {
        $('status').textContent='This view could not be rendered: '+error.message;
        console.error(error);
    } finally { busy=false; }
}
document.querySelectorAll('[data-tab]').forEach(button=>button.addEventListener('click',()=>{
    hideDepthTooltip();
    if(currentTab==='cases'&&button.dataset.tab!=='cases')setAnimPlaying(false);
    currentTab=button.dataset.tab;
    document.querySelectorAll('[data-tab]').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-current',b===button?'page':'false');});
    document.querySelectorAll('[data-panel]').forEach(p=>p.hidden=p.dataset.panel!==currentTab);
    update();
}));
for(const id of ['year-start','year-end','min-mag','region','depth-class','world-view','section-region','section-view','case-select'])$(id).addEventListener('change',()=>{
    if(+$('year-start').value>+$('year-end').value)$(id==='year-start'?'year-end':'year-start').value=$(id).value;
    update();
});
$('regional-depth-view').addEventListener('change',()=>{
    if(busy)update();
    else renderRegionalDepth(selected);
});
$('reset').addEventListener('click',()=>{ $('year-start').value=DATA.config.start_year;$('year-end').value=DATA.config.end_year;$('min-mag').value='5';$('region').value='all';$('depth-class').value='all';update(); });
let sectionResizeTimer;
window.addEventListener('resize',()=>{
    clearTimeout(sectionResizeTimer);
    sectionResizeTimer=setTimeout(()=>{
        if(currentTab==='depth'&&$('section-view').value==='3d') {
            if(busy)update();
            else renderSection(selected);
        }
    },150);
});
window.earthquakeApp={getState:()=>({busy,renderCount,currentTab,selectedCount:selected.length,totalCount:ROWS.length})};
update();
