const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5174';
const REPORT_DIR = __dirname;

const BREAKPOINTS = [
  { name: '320', width: 320, height: 568 },
  { name: '375', width: 375, height: 667 },
  { name: '390', width: 390, height: 844 },
  { name: '430', width: 430, height: 932 },
  { name: '768', width: 768, height: 1024 },
  { name: '1024', width: 1024, height: 768 },
  { name: '1280', width: 1280, height: 720 },
  { name: '1440', width: 1440, height: 900 },
];

const ROUTES = [
  { name: 'Login', path: '/login', public: true },
  { name: 'Register', path: '/register', public: true },
  { name: 'Forbidden', path: '/forbidden', public: true },
  { name: 'Dashboard', path: '/' },
  { name: 'Inventory', path: '/inventory' },
  { name: 'Forecasting', path: '/forecasting' },
  { name: 'Purchasing', path: '/purchasing' },
  { name: 'Suppliers', path: '/suppliers' },
  { name: 'AI-Assistant', path: '/ai-assistant' },
  { name: 'Invoice-Scan', path: '/invoice-scan' },
  { name: 'Profile', path: '/profile' },
  { name: 'Settings', path: '/settings' },
];

async function setupMocks(page) {
  // Mock auth endpoints - use broader pattern matching
  await page.route('**/*auth*refresh*', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ access: 'mock-access-token-for-testing', refresh: 'mock-refresh-token-for-testing' })
    });
  });

  await page.route('**/*auth*me*', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 1, email: 'admin@test.com', name: 'Admin User', role: 'admin', is_active: true })
    });
  });

  // Mock health endpoint
  await page.route('**/*health*', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ database: 'connected', redis: 'connected' })
    });
  });

  // Mock all other API endpoints with empty data
  await page.route('**/api/**', (route) => {
    const url = route.request().url();
    // Don't intercept auth or health endpoints
    if (url.includes('auth') || url.includes('health')) return route.fallback();
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: [],
        results: [],
        low_stock: [],
        alerts: [],
        skus: [],
        pagination: { total: 0, page: 1, per_page: 20 }
      })
    });
  });
}

async function checkOverflow(page) {
  const result = await page.evaluate(() => {
    const doc = document.documentElement;
    const hScroll = doc.scrollWidth > doc.clientWidth + 2;
    const overflowing = [];
    for (const el of document.querySelectorAll('div, section, main, header, aside, table, form, button, a')) {
      const r = el.getBoundingClientRect();
      if (r.right > window.innerWidth + 5 && r.width < 5000) {
        const tag = el.tagName.toLowerCase();
        const cls = el.className ? `.${String(el.className).split(' ').filter(Boolean).slice(0, 3).join('.')}` : '';
        overflowing.push({ sel: `${tag}${cls}`, right: Math.round(r.right), width: Math.round(r.width) });
        if (overflowing.length >= 3) break;
      }
    }
    return { hScroll, overflowing, scrollWidth: doc.scrollWidth, clientWidth: doc.clientWidth };
  });

  const issues = [];
  if (result.hScroll) issues.push(`H-SCROLL: scrollWidth(${result.scrollWidth}) > clientWidth(${result.clientWidth})`);
  for (const el of result.overflowing) {
    issues.push(`OVERFLOW: ${el.sel} right=${el.right} width=${el.width}`);
  }
  return issues;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();

  await setupMocks(page);

  // Establish auth first
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(3000);

  const currentUrl = page.url();
  console.log(`After initial load: ${currentUrl}`);

  const results = {};
  const allIssues = [];

  for (const route of ROUTES) {
    results[route.name] = {};
    const routeDir = path.join(REPORT_DIR, route.name);
    fs.mkdirSync(routeDir, { recursive: true });

    for (const bp of BREAKPOINTS) {
      await page.setViewportSize({ width: bp.width, height: bp.height });
      const url = `${BASE_URL}${route.path}`;

      try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 10000 });
        await page.waitForTimeout(1500);

        const bpDir = path.join(routeDir, bp.name);
        fs.mkdirSync(bpDir, { recursive: true });
        await page.screenshot({ path: path.join(bpDir, 'page.png'), fullPage: true });

        const issues = await checkOverflow(page);
        results[route.name][bp.name] = issues.length > 0 ? 'FAIL' : 'PASS';

        if (issues.length > 0) {
          allIssues.push({ route: route.name, breakpoint: bp.name, issues });
        }
      } catch (e) {
        results[route.name][bp.name] = 'ERROR';
        allIssues.push({ route: route.name, breakpoint: bp.name, issues: [e.message.substring(0, 100)] });
      }
    }

    const passed = Object.values(results[route.name]).filter(v => v === 'PASS').length;
    console.log(`${route.name}: ${passed}/${BREAKPOINTS.length} passed`);
  }

  await browser.close();

  console.log('\n=== SUMMARY ===');
  console.log(`Issues found: ${allIssues.length}`);
  if (allIssues.length > 0) {
    console.log('\n=== ISSUES ===');
    for (const issue of allIssues) {
      console.log(`[${issue.route}] ${issue.breakpoint}:`);
      for (const i of issue.issues) console.log(`  - ${i}`);
    }
  }

  fs.writeFileSync(path.join(REPORT_DIR, 'test-results.json'), JSON.stringify({ results, allIssues }, null, 2));
})();
