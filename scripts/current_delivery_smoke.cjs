// Current static presentation: image loading, links and mobile/desktop layout.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {pathToFileURL,fileURLToPath}=require('url');
const root=path.resolve(__dirname,'..'),out=path.join(root,'outputs/final');
(async()=>{
 const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_BROWSER_CHANNEL||'msedge',headless:true});
 const page=await browser.newPage();const errors=[],remote=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url())});
 for(const file of ['START_HERE.html','docs/index.html','outputs/final/report.html','docs/final_results/report.html']){
  await page.setViewportSize({width:1440,height:1100});await page.goto(pathToFileURL(path.join(root,file)).href);
  await page.evaluate(async()=>{await Promise.all([...document.images].map(img=>{img.loading='eager';return img.decode()}))});
  const images=await page.locator('img').count();assert.equal(images,file.includes('report.html')?14:1);
  assert.ok(await page.evaluate(()=>[...document.images].every(i=>i.naturalWidth>0)));
  const links=await page.locator('a[href]').evaluateAll(as=>as.map(a=>a.href));
  for(const url of links)if(url.startsWith('file:'))assert.ok(fs.existsSync(fileURLToPath(url.split('#')[0])),url);
  assert.ok(!links.some(url=>url.includes('animation.html')));
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
  if(file==='docs/index.html')await page.screenshot({path:path.join(out,'current_delivery_preview.png'),fullPage:true});
  if(file==='outputs/final/report.html')await page.screenshot({path:path.join(out,'current_report_preview.png')});
  await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),file+' mobile overflow');
  checks.push({file,images,links:links.length,desktop_mobile:'PASS'});
 }
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);await browser.close();
 const result={status:'PASS',pages:checks,console_errors:errors,external_requests:remote};
 fs.writeFileSync(path.join(out,'current_browser_verification.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exit(1)});
