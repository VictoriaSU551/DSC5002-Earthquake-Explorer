'use strict';
const DATA=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id);
const fmt=(v,d=1)=>v===null||!Number.isFinite(v)?'undefined':v.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
DATA.regions.forEach(name=>$('region').add(new Option(name,name)));
const base={font:{family:'Segoe UI, sans-serif',size:12,color:'#21384a'},margin:{l:65,r:20,b:65,t:30},paper_bgcolor:'#fff',plot_bgcolor:'#fff',showlegend:true,legend:{orientation:'h',y:1.14},xaxis:{gridcolor:'#e4ebef',zeroline:false},yaxis:{gridcolor:'#e4ebef',rangemode:'tozero'},hovermode:'closest'};
const options={responsive:true,displaylogo:false,toImageButtonOptions:{format:'png',scale:2}};
let busy=false,pending=false,generation=0;
async function render(){pending=true;if(busy)return;busy=true;try{while(pending){pending=false;
 const region=$('region').value,threshold=+$('threshold').value,measure=$('measure').value;
 const rows=DATA.annual.filter(r=>r.region===region&&r.threshold===threshold),comparison=DATA.comparisons.find(r=>r.region===region&&r.threshold===threshold);
 $('total').textContent=fmt(rows.reduce((a,r)=>a+r.count,0),0);$('early').textContent=fmt(comparison.early_annual_mean);$('late').textContent=fmt(comparison.late_annual_mean);
 $('change').textContent=comparison.rate_change_pct===null?'undefined':(comparison.rate_change_pct>=0?'+':'')+fmt(comparison.rate_change_pct,2)+'%';
 $('annual-title').textContent=region+' · M ≥ '+threshold+' · annual recorded series';
 const measureLabel=measure==='count'?'Recorded events / calendar year':'Recorded events / 365.2425 days';
 const smooth=rows.map((r,i)=>i>0&&i<rows.length-1?(rows[i-1][measure]+r[measure]+rows[i+1][measure])/3:null);
 const regions=DATA.comparisons.filter(r=>r.region!=='All'&&r.threshold===threshold);
 await Promise.all([
  Plotly.react($('annual'),[{type:'scatter',mode:'lines+markers',name:'Annual',x:rows.map(r=>r.year),y:rows.map(r=>r[measure]),line:{color:'#2166ac'},marker:{size:5}},
   {type:'scatter',mode:'lines',name:'Centred 3-year mean',x:rows.map(r=>r.year),y:smooth,line:{color:'#b67b17',width:2}}],{...base,xaxis:{...base.xaxis,title:'Year (UTC)',tickvals:[2000,2005,2010,2015,2020,2025],range:[1999.6,2025.4]},yaxis:{...base.yaxis,title:measureLabel}},options),
  Plotly.react($('shares'),[{type:'scatter',mode:'lines+markers',name:region,x:rows.map(r=>r.year),y:rows.map(r=>r.global_share_pct),line:{color:'#2166ac'}}],{...base,showlegend:false,xaxis:{...base.xaxis,title:'Year (UTC)',tickvals:[2000,2005,2010,2015,2020,2025]},yaxis:{...base.yaxis,title:'Share of global selected-threshold count (%)',range:[0,region==='All'?105:Math.max(1,...rows.map(r=>r.global_share_pct||0))*1.12]}},options),
  Plotly.react($('comparison'),[{type:'bar',orientation:'h',name:'2000–2012',y:regions.map(r=>r.region),x:regions.map(r=>r.early_annual_mean),marker:{color:'#2166ac'}},
   {type:'bar',orientation:'h',name:'2013–2025',y:regions.map(r=>r.region),x:regions.map(r=>r.late_annual_mean),marker:{color:'#b67b17'}}],{...base,barmode:'group',margin:{l:195,r:20,t:40,b:65},xaxis:{...base.xaxis,title:'Mean events / calendar year'},yaxis:{automargin:true,autorange:'reversed'}},options)
 ]);
 const body=$('audit').querySelector('tbody');body.replaceChildren();
 for(const row of rows){const tr=document.createElement('tr');for(const value of [row.year,row.count,row.exposure_days,fmt(row.rate_per_365_2425_days,3),fmt(row.global_share_pct,2)]){const td=document.createElement('td');td.textContent=value;tr.appendChild(td);}body.appendChild(tr);}
 $('status').textContent=region+' · M ≥ '+threshold+' · 26 complete calendar years · selected-population counts above, all-region comparison on the right.';generation++;
}}catch(e){$('status').textContent='Rendering failed: '+e.message;console.error(e);}finally{busy=false;}}
for(const id of ['region','threshold','measure'])$(id).addEventListener('change',render);
$('reset').addEventListener('click',()=>{$('region').value='All';$('threshold').value='5';$('measure').value='count';render();});
window.temporalApp={getState:()=>({busy,generation,region:$('region').value,threshold:+$('threshold').value})};render();
