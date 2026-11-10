const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {pathToFileURL}=require('url');
const root=path.resolve(__dirname,'..'),out=path.join(root,'outputs/final');
(async()=>{
 const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_BROWSER_CHANNEL||'msedge',headless:true,args:['--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1420,height:1100},deviceScaleFactor:2});
 const errors=[],remote=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url())});
 await page.goto(pathToFileURL(path.join(out,'animation.html')).href);await page.waitForFunction(()=>window.animationAudit&&document.querySelector('#anim-map-0')._fullLayout);
 const records=[];
 const aspect=await page.evaluate(()=>animationAudit.data().map((d,i)=>{
   const l=document.querySelector('#anim-map-'+i)._fullLayout,x=l.xaxis,y=l.yaxis;
   return {actual:(y._length/(y.range[1]-y.range[0]))/(x._length/(x.range[1]-x.range[0])),expected:1/Math.cos(d.anchorLat*Math.PI/180)};
 }));
 for(const a of aspect)assert.ok(Math.abs(a.actual-a.expected)<1e-6,`Map kilometre aspect: ${a.actual} vs ${a.expected}`);
 for(const t of [-.001,1,3,30]){
  await page.evaluate(t=>window.animationAudit.setTime(t),t);
  await page.waitForTimeout(700);
  const result=await page.evaluate(t=>({shown:animationAudit.counts(),expected:animationAudit.data().map(d=>d.rels.filter(x=>x<=t+1e-9).length)}),t);
  assert.deepEqual(result.shown,result.expected);records.push({t,...result});
  if([1,3,30].includes(t))await page.locator('#keyframe').screenshot({path:path.join(out,`animation_keyframe_day${t}.png`)});
 }
 assert.deepEqual(records[0].shown,[2,1,33]);assert.deepEqual(records[3].shown,[145,303,596]);
 await page.evaluate(()=>animationAudit.setTime(3));await page.waitForTimeout(500);
 await page.addStyleTag({content:'#keyframe h3{font-size:27px}#keyframe .stat{font-size:24px;min-height:30px}#keyframe-title{font-size:28px}.frames{padding:6px;gap:12px}#keyframe .chart{height:240px}#keyframe .note{font-size:20px}'});
 await page.evaluate(async()=>{
  const names=['Sumatra 2004','Maule 2010','Tohoku 2011'];const counts=animationAudit.counts(),data=animationAudit.data();
  for(let i=0;i<3;i++){
   document.querySelector('#anim-title-'+i).textContent=names[i];document.querySelector('#anim-stat-'+i).textContent=counts[i]+' / '+data[i].rows.length+' events revealed';
   await Plotly.relayout('anim-map-'+i,{'font.size':20,'xaxis.title.text':'','yaxis.title.text':'','margin.l':45,'margin.b':35});
   await Plotly.Plots.resize('anim-map-'+i);
  }
 });
 await page.locator('#keyframe').screenshot({path:path.join(out,'animation_poster_keyframe.png')});
 await page.selectOption('#anim-mode','sliding');await page.evaluate(()=>animationAudit.setTime(3));
 assert.deepEqual(await page.evaluate(()=>animationAudit.counts()),await page.evaluate(()=>animationAudit.data().map(d=>d.rels.filter(x=>x<=3+1e-9&&x>3-7).length)));
 await page.click('#anim-play');await page.waitForTimeout(600);assert.equal(await page.evaluate(()=>animationAudit.playing()),true);
 await page.click('#anim-reset');assert.equal(await page.evaluate(()=>animationAudit.playing()),false);assert.deepEqual(await page.evaluate(()=>animationAudit.counts()),[0,0,0]);
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+2),true);
 await page.setViewportSize({width:1420,height:1100});await page.goto(pathToFileURL(path.join(out,'dashboard.html')).href);
 await page.waitForFunction(()=>window.earthquakeApp&&!earthquakeApp.getState().busy&&earthquakeApp.getState().renderCount>0);
 await page.click('[data-tab="cases"]');await page.waitForFunction(()=>document.querySelector('#anim-map-2')._fullLayout);
 assert.equal(await page.locator('#anim-play').count(),1);
 await page.locator('#anim-slider').evaluate(e=>{e.value=30;e.dispatchEvent(new Event('input',{bubbles:true}))});await page.waitForTimeout(600);
 assert.ok((await page.locator('#anim-stat-2').textContent()).includes('596'));
 await page.click('[data-tab="depth"]');await page.waitForFunction(()=>!earthquakeApp.getState().busy);
 await page.selectOption('#section-view','profile');await page.waitForFunction(()=>!earthquakeApp.getState().busy);
 assert.ok((await page.locator('#section-location').textContent()).includes('Tohoku'));
 await page.screenshot({path:path.join(out,'integrated_depth_view.png'),fullPage:true});
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 fs.writeFileSync(path.join(out,'browser_verification.json'),JSON.stringify({status:'PASS',map_aspect:aspect,keyframe_counts:records,checks:['map kilometre aspect','four keyframes','complete case counts','trailing window','play','reset stops playback','mobile overflow','integrated animation','integrated cross section'],pageErrors:errors,externalRequests:remote},null,2));
 await browser.close();console.log('PASS: animation counts, controls, mobile layout, integrated RQ3/RQ5; zero external requests.');
})().catch(e=>{console.error(e);process.exit(1)});
