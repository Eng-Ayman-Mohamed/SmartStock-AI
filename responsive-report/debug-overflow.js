const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:5174';

const BREAKPOINTS = [
  { name: '320', width: 320, height: 568 },
  { name: '375', width: 375, height: 667 },
  { name: '390', width: 390, height: 844 },
  { name: '430', width: 430, height: 932 },
  { name: '768', width: 768, height: 1024 },
  { name: '1024', width: 1024, height: 768 },
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();

  // Mock auth
  await page.route('**/api/auth/refresh/**', (route) => {
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ access: 'mock-token', refresh: 'mock-refresh' }) });
  });
  await page.route('**/api/auth/me/**', (route) => {
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ id: 1, email: 'admin@test.com', name: 'Admin User', role: 'admin', is_active: true }) });
  });
  await page.route('**/api/**', (route) => {
    const url = route.request().url();
    if (url.includes('/auth/')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    if (url.includes('/health/')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ database: 'connected', redis: 'connected' }) });
    return route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ data: [], results: [], low_stock: [], alerts: [], skus: [], pagination: { total: 0, page: 1, per_page: 20 } }) });
  });

  // First visit at 1280 to establish auth
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);

  for (const bp of BREAKPOINTS) {
    await page.setViewportSize({ width: bp.width, height: bp.height });
    await page.waitForTimeout(1000);

    const docInfo = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      url: window.location.href,
    }));

    const hasOverflow = docInfo.scrollWidth > docInfo.clientWidth + 2;
    console.log(`${bp.name}px: scrollWidth=${docInfo.scrollWidth} clientWidth=${docInfo.clientWidth} overflow=${hasOverflow} url=${docInfo.url}`);

    if (hasOverflow) {
      const widest = await page.evaluate(() => {
        const results = [];
        for (const el of document.querySelectorAll('*')) {
          const r = el.getBoundingClientRect();
          if (r.width > window.innerWidth) {
            const tag = el.tagName.toLowerCase();
            const cls = el.className ? `.${String(el.className).split(' ').filter(Boolean).slice(0, 3).join('.')}` : '';
            results.push({ sel: `${tag}${cls}`, width: Math.round(r.width), right: Math.round(r.right) });
          }
        }
        results.sort((a, b) => b.width - a.width);
        return results.slice(0, 5);
      });
      console.log('  Widest:', widest.map(e => `${e.sel}(${e.width}px)`).join(', '));
    }
  }

  await browser.close();
})();
