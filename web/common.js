// Shared helpers for the CounterGuide pages.
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const money = (v) => '$' + Number(v).toFixed(2);

function stockBadge(n) {
  n = Number(n);
  if (n <= 0) return '<span class="stock stock-out">Out of stock</span>';
  if (n < 10) return `<span class="stock stock-low">Low · ${n}</span>`;
  return `<span class="stock stock-ok">In stock · ${n}</span>`;
}

// Local preview only (opening the files from disk): canned responses so the
// layout can be reviewed without AWS. Never used when served from CloudFront.
const PREVIEW = location.protocol === 'file:' || ['localhost', '127.0.0.1'].includes(location.hostname);
const PREVIEW_DATA = {
  '/api/chat': { answer: 'Use the 7.2V NiMH stick pack BT-NIMH-72 for the Trailblazer truck, charged on the peak-detect charger BT-CHG-NIMH [battery-safety.md]. Do not power the truck with loose AA cells; AA cells are only for the transmitter [battery-safety.md]. Unopened batteries can be returned within 15 days; opened batteries can only be exchanged if defective [returns-policy.md].', sources: ['battery-safety.md', 'returns-policy.md'], skus: [{ sku: 'BT-NIMH-72', name: '7.2V 3000mAh NiMH Stick Pack (Tamiya)', price: 29.99, stock: 32 }, { sku: 'BT-CHG-NIMH', name: 'Smart NiMH Peak-Detect Charger', price: 34.99, stock: 18 }], retrieved: 4 },
  '/api/products': { products: [
    { sku: 'BT-NIMH-72', name: '7.2V 3000mAh NiMH Stick Pack (Tamiya)', category: 'batteries', description: 'Approved drive battery for beginner RC trucks and buggies.', price: 29.99, stock: 32 },
    { sku: 'BT-CHG-LIPO', name: 'LiPo Balance Charger 2S-4S', category: 'batteries', description: 'Balance charger for 2S-4S LiPo packs.', price: 59.99, stock: 7 },
    { sku: 'HB-RC-TRUCK1', name: 'Trailblazer 1:18 Beginner RC Truck Kit', category: 'hobby equipment', description: 'Ready-to-run beginner RC truck. Uses one 7.2V NiMH stick pack.', price: 89.99, stock: 14 },
    { sku: 'HB-RC-LIPO-ADV', name: 'Velocity 1:10 Advanced RC Car (LiPo)', category: 'hobby equipment', description: 'Advanced RC car for experienced drivers.', price: 219.99, stock: 4 },
    { sku: 'CP-PHONE-A15', name: 'Nova A15 Smartphone 128GB', category: 'cell phones', description: 'Unlocked smartphone with USB-C fast charging.', price: 249.99, stock: 20 },
    { sku: 'EL-PWRBNK-10K', name: '10,000mAh Power Bank', category: 'electronics', description: 'USB-C power bank, under 100Wh.', price: 29.99, stock: 0 } ] },
  '/api/shiftlead': { answer: 'Tier at fault: data.\nThe last 5 product-page requests failed with a database connection timeout on port 5432, while load balancer targets and the ECS service are healthy.\nProposed next action: check the Aurora writer status; if capacity is exhausted, raise MaxAcu in counterguide-application through a CloudFormation stack update.', note: 'Proposal only. A person ships any change through CloudFormation.', sessionId: 'preview', toolsRun: [
    { tool: 'read_request_log', result: { recentErrors: 5 } }, { tool: 'read_load_balancer_target_health', result: {} }, { tool: 'read_service_status', result: {} }, { tool: 'read_database_status', result: { error: 'preview' } } ] },
  '/api/demo/simulate-product-page-errors': { note: 'Five SIMULATED product-page failures were written to the request log. No AWS resource changed.' },
  '/api/demo/clear-simulated': { cleared: true },
};

async function api(path, body) {
  if (PREVIEW) {
    await new Promise(r => setTimeout(r, 400));
    return PREVIEW_DATA[path.split('?')[0]] || {};
  }
  const opts = body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
  const r = await fetch(path, opts);
  let d = {};
  try { d = await r.json(); } catch { /* non-JSON error page */ }
  if (!r.ok) throw new Error(d.error || `Request failed (HTTP ${r.status})`);
  return d;
}

function skeleton(lines = 3) {
  return Array.from({ length: lines }, (_, i) => `<div class="skeleton" style="width:${[92, 78, 60, 84][i % 4]}%"></div>`).join('');
}
