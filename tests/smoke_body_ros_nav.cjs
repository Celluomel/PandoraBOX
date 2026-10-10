const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright');

const python = process.env.BODY_PYTHON || 'python';
const html = execFileSync(python, ['-c', 'from body_runtime_host.body_gui import BODY_GUI_HTML; print(BODY_GUI_HTML)'], {
  cwd: process.cwd(), encoding: 'utf8', maxBuffer: 12 * 1024 * 1024,
  env: {...process.env, PYTHONIOENCODING:'utf-8'},
});
const settings = {
  enabled: true, nav2_simulation_enabled: true, publish_topic: '/body/observations',
  input_topic: '/body/observations_in', sensor_topics: {imu:'/imu/data',gps:'/gps/fix',lidar:'/scan',odometry:'/odom',range:'/range/front'},
  nav2_stack: {state:'running'}, status: {
    available:true,state:'running',ros_distro:'jazzy',domain_id:'0',nav2_packages_available:true,
    nav2_server_available:true,nav2_preflight:{ready:true,blockers:[]},
    nav2_simulation:{enabled:true,cmd_vel_hardware_isolated:true,cmd_vel_subscribers:[{}],pose:{x:1.5,y:0,yaw_rad:0}},
    sensor_subscriptions:{lidar:{state:'active',topic:'/scan',count:20},odometry:{state:'active',topic:'/odom',count:20}},
  },
};
const visual = {
  available:true,source:'synthetic_nav2',simulation_only:true,
  map:{origin:-8,size_m:16,obstacles:[[2.02,-.48,2.98,.48],[2.18,.88,2.82,1.52]]},
  pose:{x:1.5,y:0,yaw_rad:0},scan:{returns:[[0,1],[.5,1.4],[-.5,1.1]]},
};

(async () => {
  const browser = await chromium.launch({headless:true,...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {})});
  try {
    for (const width of [1440, 390]) {
      const page = await browser.newPage({viewport:{width,height:900}});
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.route('http://body.test/**', route => {
        const path = new URL(route.request().url()).pathname;
        const payload = path === '/navigation' ? html : JSON.stringify(
          path === '/ros2/settings' ? settings : path === '/ros2/visualization' ? visual :
          path === '/ros2/nav2/simulation/route-test' ? {ok:true,status:'succeeded',elapsed_s:12.4,position_error_m:.1} :
          path === '/body/camera/frame' ? {available:false,status:'disabled'} : {ok:true}
        );
        return route.fulfill({status:200,contentType:path === '/navigation' ? 'text/html' : 'application/json',body:payload});
      });
      await page.goto('http://body.test/navigation');
      await page.locator('#navops-bridge').getByText('Online').waitFor();
      assert.equal(await page.locator('#nav-navigation').getAttribute('class'), 'active');
      assert.equal(await page.locator('#navops-route').isEnabled(), true);
      const pixels = await page.locator('#navops-map').evaluate(canvas => {
        const data = canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
        let nonblank = 0;
        for (let i=0;i<data.length;i+=4) if (data[i] > 20 || data[i+1] > 35 || data[i+2] > 40) nonblank++;
        return nonblank;
      });
      assert.ok(pixels > 1000, `map is blank at ${width}px`);
      await page.waitForTimeout(450);
      if (process.env.BODY_NAV_SCREENSHOT) await page.screenshot({path:`body-nav-map-${width}.png`,fullPage:true});
      await page.locator('#navops-route').click();
      await page.locator('#navops-result').getByText('succeeded').waitFor();
      assert.equal(await page.locator('#navops-result').getByText('No').count(), 1);
      await page.locator('#navops-tab-ros').click();
      await page.locator('#navops-topic-imu').fill('/robot/imu');
      await page.waitForTimeout(2200);
      assert.equal(await page.locator('#navops-topic-imu').inputValue(), '/robot/imu');
      assert.equal(await page.locator('#navops-page-ros').isVisible(), true);
      assert.deepEqual(errors, [], `page errors at ${width}px`);
      if (process.env.BODY_NAV_SCREENSHOT) await page.screenshot({path:`body-nav-ros-${width}.png`,fullPage:true});
      await page.close();
    }
    console.log('Body ROS 2 + Navigation browser smoke passed at desktop and mobile widths.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
