// Optional browser QA. Requires Playwright and its Chromium browser.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const { pathToFileURL } = require('node:url');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname,'..');
(async()=>{
    const browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_BROWSER_CHANNEL || undefined,args:['--enable-unsafe-swiftshader']});
    const page=await browser.newPage({viewport:{width:1440,height:1080},deviceScaleFactor:1});
    const errors=[],remote=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url());});
    await page.route('https://**/*',route=>route.abort());
    await page.route('http://**/*',route=>route.abort());
    const wait=()=>page.waitForFunction(()=>window.earthquakeApp&&!window.earthquakeApp.getState().busy&&window.earthquakeApp.getState().renderCount>0,{},{timeout:60000});
    const select=async(id,value)=>{await page.selectOption('#'+id,value);await wait();};
    const tab=async(name)=>{await page.click('[data-tab="'+name+'"]');await wait();};
    await page.goto(pathToFileURL(path.join(root,process.env.DASHBOARD_PATH||'outputs/final/dashboard.html')).href,{waitUntil:'load',timeout:60000});
    await wait();
    assert.equal(await page.locator('#count').textContent(),'46,463');
    assert.deepEqual(await page.evaluate(()=>histogram([5,5.1,5.2],5,.1,3).y),[1,1,1]);
    const geographicRange=await page.locator('#world').evaluate(e=>({x:e._fullLayout.xaxis.range,y:e._fullLayout.yaxis.range}));
    assert.ok(geographicRange.x[0]>=-180.001&&geographicRange.x[1]<=180.001);
    assert.ok(geographicRange.y[0]>=-90.001&&geographicRange.y[1]<=90.001);
    await page.screenshot({path:path.join(root,'outputs/dashboard_desktop.png'),fullPage:true});
    await select('world-view','globe');
    assert.equal(await page.locator('#world').evaluate(e=>e.data[0].type),'surface');
    await page.screenshot({path:path.join(root,'outputs/dashboard_globe.png'),fullPage:true});
    await select('year-start','2011');await select('year-end','2011');
    assert.equal(await page.locator('#count').textContent(),'2,701');
    await select('min-mag','9');
    assert.equal(await page.locator('#count').textContent(),'1');
    await select('depth-class','2');
    assert.equal(await page.locator('#count').textContent(),'0');
    assert.match(await page.locator('#world').evaluate(e=>e.layout.annotations[0].text),/No events/);
    await page.click('#reset');await wait();
    await tab('boundaries');
    assert.ok(await page.locator('#distance-ecdf').evaluate(e=>e.data.length>0));
    await page.screenshot({path:path.join(root,'outputs/dashboard_boundaries.png'),fullPage:true});
    await tab('depth');
    await select('section-region','2');
    assert.ok(await page.locator('#cross-section').evaluate(e=>e.data.some(t=>t.x.some(v=>v>180))));
    await select('section-view','3d');
    assert.equal(await page.locator('#cross-section').evaluate(e=>e.data[0].type),'scatter3d');
    await select('section-region','0');
    const sceneSnapshot=()=>page.locator('#cross-section').evaluate(e=>({
        ranges:['x','y','z'].map(axis=>e._fullLayout.scene[axis+'axis'].range),
        aspect:e._fullLayout.scene.aspectratio,
        positions:Object.fromEntries(e.data.filter(t=>t.mode==='markers').flatMap(t=>t.customdata.map((d,i)=>[d[0],[t.x[i],t.y[i],t.z[i]]]))),
        depthLabels:e._fullLayout.scene.zaxis.ticktext,
        correctDepth:e.data.filter(t=>t.mode==='markers').every(t=>t.z.every((z,i)=>z===-t.customdata[i][1]))
    }));
    const initialScene=await sceneSnapshot();
    assert.ok(initialScene.correctDepth&&initialScene.depthLabels.every(value=>value>=0));
    const contextCheck=await page.locator('#cross-section').evaluate(e=>({
        depths:e.data.filter(t=>t.meta?.kind==='depth-boundary').map(t=>t.meta.depth),
        coastlinePresent:e.data.some(t=>t.meta?.kind==='coastline')
    }));
    assert.deepEqual(contextCheck.depths,[70,300]);assert.equal(contextCheck.coastlinePresent,false);
    await select('min-mag','7');
    const filteredScene=await sceneSnapshot();
    const near=(actual,expected)=>assert.ok(Math.abs(actual-expected)<1e-6);
    assert.ok(Object.keys(filteredScene.positions).length>0);
    for(const [id,position] of Object.entries(filteredScene.positions)) {
        assert.ok(initialScene.positions[id]);
        position.forEach((value,i)=>near(value,initialScene.positions[id][i]));
    }
    filteredScene.ranges.flat().forEach((value,i)=>near(value,initialScene.ranges.flat()[i]));
    ['x','y','z'].forEach(axis=>near(filteredScene.aspect[axis],initialScene.aspect[axis]));
    await select('min-mag','5');
    await page.screenshot({path:path.join(root,'outputs/dashboard_depth.png'),fullPage:true});
    await tab('magnitude');
    assert.equal(await page.locator('#mag-frequency').evaluate(e=>e.data[0].y[0]),46463);
    await tab('cases');
    assert.ok(await page.locator('#global-filters').isHidden());
    await select('case-select','2');
    assert.match(await page.locator('#case-stats').textContent(),/33 before \/ 563 after/);
    assert.equal(await page.locator('#case-timeline').evaluate(e=>e.data[0].y.reduce((a,b)=>a+b,0)),596);
    await page.screenshot({path:path.join(root,'outputs/dashboard_cases.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await tab('overview');await select('world-view','map');
    await page.screenshot({path:path.join(root,'outputs/dashboard_mobile.png'),fullPage:true});
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+2);
    assert.equal(overflow,false);
    await page.goto(pathToFileURL(path.join(root,'outputs/report.html')).href,{waitUntil:'load'});
    assert.equal(await page.locator('figure').count(),12);
    await page.locator('img').evaluateAll(images=>images.forEach(i=>i.loading='eager'));
    await page.waitForFunction(()=>Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0));
    assert.equal(await page.locator('img').evaluateAll(images=>images.filter(i=>!i.complete||!i.naturalWidth).length),0);
    await page.setViewportSize({width:1440,height:1080});
    await page.screenshot({path:path.join(root,'outputs/report_preview.png'),fullPage:false});
    assert.deepEqual(errors,[]);
    assert.deepEqual(remote,[]);
    const receipt={status:'PASS',remote_requests:remote.length,page_errors:errors.length,checks:['default counts','decimal magnitude bin edges','valid geographic map axes','3D globe','year filters','magnitude filter','empty selection','boundary ECDF','date-line cross-section','3D hypocentres','stable 3D coordinates and frame across filters','positive-down 3D depth labels','magnitude survival','case windows','mobile layout','twelve report images','offline without HTTP requests']};
    fs.writeFileSync(path.join(root,'outputs/browser_verification.json'),JSON.stringify(receipt,null,2)+'\n');
    console.log(JSON.stringify(receipt,null,2));
    await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
