// Focused acceptance checks for the three current Member 3 dashboard tasks.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const out=path.join(root,'outputs/final/rq3_browser_acceptance');
fs.mkdirSync(out,{recursive:true});
const palette=['#2166ac','#b06816','#8e4b98','#57823b','#b14f76','#4b8793','#656565'];
const depthColors=['#2166ac','#cc8b19','#8e4b98'];
const near=(a,b,tolerance=1e-6)=>assert.ok(Math.abs(a-b)<=tolerance,`${a} differs from ${b}`);
const classification=depth=>depth===null?3:depth<70?0:depth<300?1:2;
let stage='startup';
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_BROWSER_CHANNEL||undefined,args:['--enable-unsafe-swiftshader'],
  executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||undefined});
 const errors=[],remote=[],checks=[],timings=[];
 let page;
 try{
  const context=await browser.newContext({viewport:{width:1480,height:1080},offline:true});
  page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  page.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url());});
  const idle=async()=>{const start=Date.now();await page.waitForFunction(()=>window.earthquakeApp&&!earthquakeApp.getState().busy,{},{timeout:7000});timings.push(Date.now()-start);};
  const select=async(id,value)=>{await page.locator('#'+id).selectOption(String(value));await idle();};
  const reset=async()=>{await page.locator('#reset').click();await idle();};
  await page.setContent(fs.readFileSync(path.join(root,'outputs/final/dashboard.html'),'utf8'),{waitUntil:'load'});await idle();
  const payload=await page.evaluate(()=>({rows:DATA.rows,regions:DATA.regions,sections:DATA.sections,config:DATA.config}));
  const lookup=new Map(payload.rows.map(row=>[row[0],row]));
  await page.getByRole('button',{name:'03 Depth'}).click();await idle();
  assert.equal(await page.locator('#section-region').inputValue(),'0');
  assert.equal(await page.locator('#section-view').inputValue(),'2d');
  assert.deepEqual(await page.locator('#section-view option').allTextContents(),['Regional projection','Cross-section','3D hypocentres']);
  assert.deepEqual(await page.locator('#section-region option').allTextContents(),payload.regions.map(n=>n==='Other'?'Other regions':n));
  const selected=async()=>{
   const f=await page.evaluate(()=>Object.fromEntries(['year-start','year-end','min-mag','region','depth-class'].map(id=>[id,document.getElementById(id).value])));
   const start=Date.UTC(+f['year-start'],0,1),end=Date.UTC(+f['year-end']+1,0,1);
   return payload.rows.filter(r=>Date.parse(r[1])>=start&&Date.parse(r[1])<end&&r[5]>=+f['min-mag']&&
    (f.region==='all'||r[7]===+f.region)&&(f['depth-class']==='all'||classification(r[4])===+f['depth-class']));
  };
  const traces=async id=>page.locator('#'+id).evaluate(e=>e.data);
  const checkComparison=async label=>{
   const rows=await selected(),known=rows.filter(r=>r[4]!==null);
   near(Number((await page.locator('#count').innerText()).replaceAll(',','')),rows.length);
   const histogram=await traces('depth-hist');
   if(known.length)assert.equal(histogram[0].y.reduce((a,b)=>a+b,0),known.length);
   await select('regional-depth-view','box');
   if(known.length){
    const boxes=await traces('depth-box');assert.equal(boxes.length,7);
    boxes.forEach((box,i)=>{assert.deepEqual(box.x,known.filter(r=>r[7]===i).map(r=>r[4]));assert.equal(box.marker.color,palette[i]);});
    const drawn=await page.locator('#depth-box').evaluate(e=>e.calcdata.map(t=>({lower:t[0].q1,median:t[0].med,upper:t[0].q3})));
    boxes.forEach((box,i)=>{if(box.meta)for(const key of ['lower','median','upper'])near(box.meta[key],drawn[i][key]);});
   }else assert.match(await page.locator('#depth-box').innerText(),/No selected events with known depth/);
   await select('regional-depth-view','shares');
   if(known.length){
    const bars=await traces('depth-box'),totals=payload.regions.map((_,i)=>known.filter(r=>r[7]===i).length);
    const present=totals.map((n,i)=>n?i:-1).filter(i=>i>=0);assert.equal(bars.length,3);
    present.forEach((i,j)=>{
     const counts=[0,1,2].map(c=>known.filter(r=>r[7]===i&&classification(r[4])===c).length);
     bars.forEach((bar,c)=>{near(bar.x[j],100*counts[c]/totals[i],1e-9);assert.equal(bar.y[j],payload.regions[i]);assert.equal(bar.customdata[j][1],counts[c]);assert.equal(bar.customdata[j][2],totals[i]);});
     near(bars.reduce((s,b)=>s+b.x[j],0),100,1e-9);assert.equal(bars[1].marker.color[j],`rgb(${parseInt(palette[i].slice(1,3),16)},${parseInt(palette[i].slice(3,5),16)},${parseInt(palette[i].slice(5,7),16)})`);
    });
    const title=await page.locator('#depth-box').evaluate(e=>e._fullLayout.xaxis.title.text);
    assert.ok(title.includes('N = '+known.length.toLocaleString('en-US')));
   }else assert.match(await page.locator('#depth-box').innerText(),/No selected events with known depth/);
   checks.push({task:1,label,selected:rows.length,known:known.length});
  };
  stage='regional comparisons';
  await checkComparison('all regions');
  await page.locator('#depth-box').screenshot({path:path.join(out,'depth-shares-desktop.png')});
  for(let i=0;i<7;i++){
   await select('region',i);await checkComparison(payload.regions[i]);
   assert.equal((await traces('depth-hist'))[0].marker.color,palette[i]);
  }
  await reset();await select('year-start',2011);await select('year-end',2011);await checkComparison('2011 only');
  await reset();await select('min-mag',7);await checkComparison('M >= 7');
  await reset();await select('depth-class',1);await checkComparison('intermediate only');
  await reset();await select('region',2);await select('year-start',2010);await select('min-mag',6);await checkComparison('combined region/year/magnitude');
  await reset();await select('year-start',2025);await select('min-mag',9);await checkComparison('empty selection');
  await reset();await select('regional-depth-view','box');
  stage='single box hover cards';
  await page.locator('#depth-box').scrollIntoViewIfNeeded();
  for(let i=0;i<7;i++){
   const position=await page.locator('#depth-box').evaluate((e,i)=>{const b=e.data[i],f=e._fullLayout,r=e.getBoundingClientRect();return {x:r.left+f.xaxis._offset+f.xaxis.d2p((b.meta.lower+b.meta.upper)/2),y:r.top+f.yaxis._offset+f.yaxis.d2p(b.name)};},i);
   await page.mouse.move(position.x,position.y);
   await page.waitForFunction(()=>!document.getElementById('depth-box-tooltip').hidden,{},{timeout:7000});
   assert.equal(await page.locator('#depth-tooltip-region').innerText(),payload.regions[i]);
   assert.equal(await page.locator('#depth-box .hoverlayer .hovertext').count(),0);
   await page.mouse.move(0,0);assert.ok(await page.locator('#depth-box-tooltip').isHidden());
  }
  await page.locator('#depth-box').screenshot({path:path.join(out,'depth-boxes-desktop.png')});
  checks.push({task:1,label:'seven real pointer hover cards'});
  stage='missing and boundary depths';
  await select('regional-depth-view','shares');
  const synthetic=await page.evaluate(async()=>{
   const depths=[-2,0,69.999,70,299.999,300,null];
   const rows=depths.map((d,i)=>['test-'+i,'2000-01-01T00:00:00Z',38,140,d,5,0,0,d===null?3:d<70?0:d<300?1:2,'Test']);
   await renderRegionalDepth(rows);
   const values=document.getElementById('depth-box').data.map(t=>({share:t.x[0],counts:t.customdata[0].slice(1)}));
   await renderRegionalDepth(rows.filter(r=>r[4]===null));
   const missingOnly=document.getElementById('depth-box').innerText;
   await update();return {values,missingOnly};
  });
  synthetic.values.forEach((v,c)=>{near(v.share,100*[3,2,1][c]/6);assert.deepEqual(v.counts,[[3,2,1][c],6,1]);});
  assert.match(synthetic.missingOnly,/No selected events with known depth/);
  checks.push({task:1,label:'70/300 km boundaries, negative and missing depths'});
  await select('regional-depth-view','box');await reset();
  const markerTraces=ts=>ts.filter(t=>t.mode==='markers');
  const ids=ts=>markerTraces(ts).flatMap(t=>t.customdata.map(d=>d[0]));
  const read3d=()=>page.locator('#cross-section').evaluate(e=>({data:e.data,ranges:['x','y','z'].map(k=>e._fullLayout.scene[k+'axis'].range),aspect:e._fullLayout.scene.aspectratio,ticks:e._fullLayout.scene.zaxis.ticktext}));
  stage='all seven projections, profiles and 3D';
  for(let i=0;i<7;i++){
   const name=payload.regions[i],section=payload.sections[name],regional=payload.rows.filter(r=>r[7]===i&&r[4]!==null);
   await select('section-region',i);await select('section-view','2d');
   assert.deepEqual(ids(await traces('cross-section')).sort(),regional.map(r=>r[0]).sort());
   await select('section-view','profile');
   const map=await traces('section-map'),profile=await traces('section-profile'),expected=section.events.map(r=>r[0]).sort();
   assert.deepEqual(ids(map).sort(),expected);assert.deepEqual(ids(profile).sort(),expected);
   markerTraces(profile).forEach(t=>t.customdata.forEach((d,k)=>{assert.equal(t.y[k],lookup.get(d[0])[4]);assert.ok(t.x[k]>=-200-1e-6&&t.x[k]<=1200+1e-6);assert.ok(Math.abs(d[3])<=100+1e-6);}));
   const scales=await page.locator('#section-profile').evaluate(e=>({x:Math.abs(e._fullLayout.xaxis._m),y:Math.abs(e._fullLayout.yaxis._m),range:e._fullLayout.yaxis.range}));
   near(scales.x,scales.y,1e-8);assert.ok(scales.range[0]>scales.range[1]);
   const caption=await page.locator('#section-preview').innerText();assert.ok(!/[\u4e00-\u9fff]/.test(caption));
   assert.ok((await page.locator('#section-location').innerText()).includes('N = '+expected.length.toLocaleString('en-US')));
   await page.locator('.section-pair').screenshot({path:path.join(out,'profile-'+i+'-desktop.png')});
   await select('section-view','3d');
   const scene=await read3d(),events=markerTraces(scene.data),shown=regional.length<=8000?regional:Array.from({length:8000},(_,k)=>regional[Math.floor(k*regional.length/8000)]);
   assert.deepEqual(ids(events).sort(),shown.map(r=>r[0]).sort());
   const box=payload.config.regions[i],wrap=box&&box.lon[0]>box.lon[1];
   const longitude=r=>wrap&&r[3]<0?r[3]+360:r[3];
   const middle=values=>{const sorted=values.slice().sort((a,b)=>a-b),m=Math.floor(sorted.length/2);return sorted.length%2?sorted[m]:(sorted[m-1]+sorted[m])/2;};
   const lon0=middle(regional.map(longitude)),lat0=middle(regional.map(r=>r[2])),kmPerDegree=payload.config.earth_radius_km*Math.PI/180;
   events.forEach(t=>t.customdata.forEach((d,k)=>{const row=lookup.get(d[0]);near(t.x[k],(longitude(row)-lon0)*kmPerDegree*Math.cos(lat0*Math.PI/180),.05);near(t.y[k],(row[2]-lat0)*kmPerDegree,.05);}));
   events.forEach(t=>{assert.equal(t.marker.size,1.6);assert.equal(t.marker.opacity,.8);t.customdata.forEach((d,k)=>{assert.equal(t.z[k],-lookup.get(d[0])[4]);assert.equal(t.marker.color,depthColors[classification(lookup.get(d[0])[4])]);});});
   assert.ok(scene.ticks.every(t=>t>=0));assert.ok(!scene.data.some(t=>t.meta?.kind==='coastline'));
   assert.deepEqual(scene.data.filter(t=>t.meta?.kind==='depth-boundary').map(t=>t.meta.depth),i===0?[70,300]:[]);
   await page.mouse.move(0,0);await page.locator('#cross-section').screenshot({path:path.join(out,'3d-'+i+'-desktop.png')});
   await select('min-mag',7);const filtered=await read3d();
   scene.ranges.flat().forEach((v,k)=>near(v,filtered.ranges.flat()[k]));['x','y','z'].forEach(k=>near(scene.aspect[k],filtered.aspect[k]));
   await select('min-mag',5);
   checks.push({task:2,region:name,profileEvents:expected.length,mapProfileIdentity:true,equalKmScale:true});
   checks.push({task:3,region:name,plotted:shown.length,eligible:regional.length,coordinatesStable:true});
  }
  stage='scope intersections and empty states';
  await select('region',0);await select('section-region',2);await select('section-view','profile');
  assert.equal(ids(await traces('section-profile')).length,0);
  assert.match(await page.locator('#section-profile').innerText(),/No selected known-depth events/);
  await select('section-view','3d');assert.match(await page.locator('#cross-section').innerText(),/No selected events/);
  await reset();await select('section-region',0);await select('min-mag',9);await select('year-start',2025);
  for(const mode of ['2d','profile','3d']){await select('section-view',mode);assert.equal(ids(await traces(mode==='profile'?'section-profile':'cross-section')).length,0);}
  assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
  const receipt={status:'PASS',checks,renderWaitMaxMs:Math.max(...timings),pageErrors:errors,externalRequests:remote,
   scopes:{figures:['depth histogram','regional boxplots','depth-class shares','regional projection','route map','finite cross-section','regional 3D'],regions:payload.regions,viewportWidths:[1480]},
   limitations:['Representative combined filters, not every possible filter combination.','Desktop browser only; numerical source/geometry audit is recorded separately.']};
  fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify(receipt,null,2));
  console.log(JSON.stringify({status:'PASS',checks:checks.length,renderWaitMaxMs:receipt.renderWaitMaxMs,pageErrors:errors.length,externalRequests:remote.length}));
 }catch(error){
  if(page)await page.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});
  fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({stage,error:error.stack,checks,errors,remote},null,2));
  throw error;
 }finally{await browser.close();}
})().catch(error=>{console.error('RQ3 acceptance failed at '+stage+'\n'+error.stack);process.exitCode=1;});
