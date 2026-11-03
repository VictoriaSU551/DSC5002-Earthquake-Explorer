// Optional offline rendering/interaction QA, using Playwright and Chromium/Edge.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),output=path.join(root,'outputs/temporal_regional_v2_20261103');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_BROWSER_CHANNEL||undefined});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[],remote=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url());});
 await page.route('https://**/*',r=>r.abort());await page.route('http://**/*',r=>r.abort());
 const wait=()=>page.waitForFunction(()=>window.temporalApp&&!temporalApp.getState().busy&&temporalApp.getState().generation>0,{},{timeout:60000});
 const select=async(id,value)=>{await page.selectOption('#'+id,value);await wait();};
 await page.goto(pathToFileURL(path.join(output,'dashboard.html')).href,{waitUntil:'load'});await wait();
 assert.equal(await page.locator('#total').textContent(),'46,463');assert.equal(await page.locator('#change').textContent(),'-6.63%');
 assert.equal(await page.locator('#annual').evaluate(e=>e.data[0].y.reduce((a,b)=>a+b,0)),46463);
 assert.ok(await page.locator('#shares').evaluate(e=>e.data[0].y.every(v=>v===100)));
 assert.equal(await page.locator('#audit tbody tr').count(),26);
 await page.screenshot({path:path.join(output,'dashboard_desktop.png'),fullPage:true});
 await select('threshold','6');assert.equal(await page.locator('#total').textContent(),'3,874');assert.equal(await page.locator('#change').textContent(),'-15.42%');
 await select('threshold','5');await select('region','Indonesia and Philippines');
 assert.equal(await page.locator('#total').textContent(),'9,313');assert.equal(await page.locator('#change').textContent(),'-25.58%');
 assert.equal(await page.locator('#comparison').evaluate(e=>e.data[0].y.length),7);
 await select('region','All');await select('measure','rate_per_365_2425_days');
 assert.ok(Math.abs(await page.locator('#annual').evaluate(e=>e.data[0].y[0])-1494*365.2425/366)<1e-8);
 await select('region','Alaska and Aleutians');await select('threshold','7');
 assert.ok(await page.locator('#annual').evaluate(e=>e.data[0].y.some(v=>v===0)));
 await page.click('#reset');await wait();assert.equal(await page.locator('#total').textContent(),'46,463');
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);
 await page.screenshot({path:path.join(output,'dashboard_mobile.png'),fullPage:true});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2),false);
 await page.goto(pathToFileURL(path.join(output,'report.html')).href,{waitUntil:'load'});
 await page.locator('img').evaluateAll(images=>images.forEach(i=>i.loading='eager'));
 await page.waitForFunction(()=>Array.from(document.images).every(i=>i.complete&&i.naturalWidth));
 assert.equal(await page.locator('figure').count(),9);
 // Every local link must refer to a real sibling file or an in-page anchor.
 const missing=await page.locator('a[href]').evaluateAll(links=>links.map(a=>a.getAttribute('href')).filter(x=>x&&!/^(https?:|#)/.test(x)));
 for(const relative of missing)assert.ok(fs.existsSync(path.resolve(output,relative)),relative);
 await page.setViewportSize({width:1440,height:1050});await page.screenshot({path:path.join(output,'report_preview.png')});
 await page.locator('#comparability').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(output,'report_comparability.png')});
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 const receipt={status:'PASS',page_errors:0,http_requests:0,checks:['global/threshold counts','regional counts','rate change','exact leap-year exposure','zero-count years','same-threshold shares','all-region comparison scope','reset','26 audit rows','mobile overflow','nine report figures','local links','offline operation']};
 fs.writeFileSync(path.join(output,'browser_verification.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
