// CounterGuide static front end. Calls only /api/* on the application tier.
const $ = (sel, root = document) => root.querySelector(sel);

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[c]));

function money(v) {
  const n = Number(v);
  return Number.isFinite(n) ? `$${n.toFixed(2)}` : '';
}

function stockBadge(n) {
  n = Number(n);
  if (!Number.isFinite(n)) return '';
  if (n <= 0) return '<span class="stock stock-out">Out of stock</span>';
  if (n < 10) return `<span class="stock stock-low">${n} in stock</span>`;
  return `<span class="stock stock-ok">${n} in stock</span>`;
}

function skeleton(lines = 3) {
  return Array.from({ length: lines }, (_, i) => (
    `<div class="skeleton" style="width:${[92, 78, 64, 84][i % 4]}%"></div>`
  )).join('');
}

const DOC_TITLES = {
  'battery-safety.md': 'Battery safety',
  'device-care.md': 'Device care',
  'rc-beginner-setup.md': 'Beginner RC setup',
  'returns-policy.md': 'Returns',
};

const TOOL_LABELS = {
  read_load_balancer_target_health: 'Load balancer targets',
  read_service_status: 'Application service',
  read_database_status: 'Database',
  read_knowledge_base_sync_status: 'Knowledge base sync',
  read_cloudwatch_alarms: 'CloudWatch alarms',
  read_request_log: 'Request log',
};

// Local file or localhost preview only. Served from CloudFront, these responses are never used.
const PREVIEW = location.protocol === 'file:' || ['localhost', '127.0.0.1'].includes(location.hostname);

const PREVIEW_PRODUCTS = [
  { sku: 'EL-BTSPK-01', name: 'Pocket Bluetooth Speaker', category: 'electronics', description: 'Portable speaker with a built-in rechargeable battery and USB-C charging.', price: 39.99, stock: 22 },
  { sku: 'EL-PWRBNK-10K', name: '10,000mAh Power Bank', category: 'electronics', description: 'USB-C power bank for phones and small electronics. Airline carry-on friendly (under 100Wh).', price: 29.99, stock: 30 },
  { sku: 'CP-PHONE-A15', name: 'Nova A15 Smartphone 128GB', category: 'cell phones', description: 'Unlocked smartphone with a 5000mAh built-in battery and USB-C fast charging.', price: 249.99, stock: 20 },
  { sku: 'CP-CHG-USBC20', name: '20W USB-C Wall Charger', category: 'cell phones', description: 'Certified 20W USB-C power adapter for phones and small electronics.', price: 19.99, stock: 60 },
  { sku: 'CP-CASE-A15', name: 'Rugged Case for Nova A15', category: 'cell phones', description: 'Drop-resistant case for the Nova A15.', price: 17.99, stock: 35 },
  { sku: 'HB-RC-TRUCK1', name: 'Trailblazer 1:18 Beginner RC Truck Kit', category: 'hobby equipment', description: 'Ready-to-run beginner RC truck. Uses one 7.2V NiMH stick pack with a Tamiya-style connector. Battery and charger sold separately.', price: 89.99, stock: 14 },
  { sku: 'HB-RC-BUGGY2', name: 'Dustrunner 1:16 Beginner RC Buggy', category: 'hobby equipment', description: 'Beginner off-road buggy. Uses one 7.2V NiMH stick pack with a Tamiya-style connector. Battery and charger sold separately.', price: 99.99, stock: 9 },
  { sku: 'HB-RC-LIPO-ADV', name: 'Velocity 1:10 Advanced RC Car (LiPo)', category: 'hobby equipment', description: 'Advanced RC car for experienced drivers. Requires a 2S 7.4V LiPo pack and a LiPo balance charger. Not a beginner kit.', price: 219.99, stock: 4 },
  { sku: 'HB-TX-AAPACK', name: 'RC Transmitter (takes 4x AA)', category: 'hobby equipment', description: 'Replacement handheld transmitter for the beginner trucks. Powered by four AA cells in the transmitter only.', price: 24.99, stock: 11 },
  { sku: 'BT-NIMH-72', name: '7.2V 3000mAh NiMH Stick Pack (Tamiya)', category: 'batteries', description: 'Approved drive battery for beginner RC trucks and buggies. Matches the Tamiya-style connector.', price: 29.99, stock: 32 },
  { sku: 'BT-LIPO-2S', name: '7.4V 2S 5000mAh LiPo Pack (hard case)', category: 'batteries', description: 'LiPo drive pack for advanced RC cars. Requires a LiPo balance charger and a LiPo-safe charging bag.', price: 54.99, stock: 12 },
  { sku: 'BT-AA-ALK8', name: 'AA Alkaline Cells, 8-pack (loose)', category: 'batteries', description: 'Loose single-use AA cells for remotes, transmitters, flashlights and small electronics.', price: 8.99, stock: 120 },
  { sku: 'BT-AA-NIMH4', name: 'AA Rechargeable NiMH Cells, 4-pack (loose)', category: 'batteries', description: 'Loose rechargeable AA cells for transmitters and household devices.', price: 14.99, stock: 40 },
  { sku: 'BT-CHG-NIMH', name: 'Smart NiMH Peak-Detect Charger', category: 'batteries', description: 'Charger for 6-8.4V NiMH stick packs with a Tamiya-style connector. Stops automatically when the pack is full.', price: 34.99, stock: 18 },
  { sku: 'BT-CHG-LIPO', name: 'LiPo Balance Charger 2S-4S', category: 'batteries', description: 'Balance charger for 2S-4S LiPo packs. Use with a LiPo-safe charging bag.', price: 59.99, stock: 7 },
  { sku: 'BT-BAG-LIPO', name: 'LiPo-Safe Charging Bag', category: 'batteries', description: 'Fire-resistant bag for charging and storing LiPo packs.', price: 12.99, stock: 25 },
];

const SKU = Object.fromEntries(PREVIEW_PRODUCTS.map((p) => [p.sku, p]));

function previewChat(body) {
  const q = String((body && body.question) || '').toLowerCase();
  if (/employee discount|store hours|payroll|weather|out of scope|not in the guides/.test(q)) {
    return {
      answer: "I couldn't find that in the product guides, so I won't guess. Please check with a supervisor.",
      sources: [],
      skus: [],
      retrieved: 0,
    };
  }
  if (/loose aa|beginner rc kit|aa batteries/.test(q)) {
    return {
      answer: 'For the Trailblazer 1:18 Beginner RC Truck Kit (HB-RC-TRUCK1), sell the 7.2V NiMH stick pack BT-NIMH-72 and the Smart NiMH Peak-Detect Charger BT-CHG-NIMH. Do not power the truck with loose AA cells. The battery safety guide forbids loose AA cells as the drive battery; they can short, overheat, and cannot deliver the current the motor draws [battery-safety.md]. Loose AA cells are only for the handheld transmitter [rc-beginner-setup.md].',
      sources: ['battery-safety.md', 'rc-beginner-setup.md'],
      skus: [SKU['HB-RC-TRUCK1'], SKU['BT-NIMH-72'], SKU['BT-CHG-NIMH']],
      retrieved: 3,
    };
  }
  if (/return window|which battery|safe for the trailblazer|battery pack/.test(q)) {
    return {
      answer: 'Use the 7.2V NiMH stick pack BT-NIMH-72 for the Trailblazer beginner truck, and charge it on the Smart NiMH Peak-Detect Charger BT-CHG-NIMH [battery-safety.md]. Unopened batteries can be returned within 15 days. Opened batteries can only be exchanged if they are defective [returns-policy.md].',
      sources: ['battery-safety.md', 'returns-policy.md'],
      skus: [SKU['BT-NIMH-72'], SKU['BT-CHG-NIMH']],
      retrieved: 4,
    };
  }
  return {
    answer: "I couldn't find that in the product guides, so I won't guess. Please check with a supervisor.",
    sources: [],
    skus: [],
    retrieved: 0,
  };
}

function previewShiftlead() {
  return {
    answer: 'Tier at fault: data.\nThe last 5 product-page requests failed with a database connection timeout on port 5432. Load balancer targets and the application service are healthy.\nNext action: check the Aurora writer. If capacity is exhausted, raise MaxAcu on the counterguide-application stack. A person ships that change with CloudFormation.',
    note: 'Proposal only. A person ships any change through CloudFormation.',
    sessionId: 'preview',
    toolsRun: [
      { tool: 'read_request_log', result: { recentErrors: 5 } },
      { tool: 'read_load_balancer_target_health', result: { targets: [{ state: 'healthy' }] } },
      { tool: 'read_service_status', result: { running: 2 } },
      { tool: 'read_database_status', result: { error: 'connection timeout', reachableFromApplication: 'no (OperationalError)' } },
    ],
  };
}

function previewData(path, body) {
  const key = path.split('?')[0];
  if (key === '/api/chat') return previewChat(body);
  if (key === '/api/shiftlead') return previewShiftlead();
  if (key === '/api/products') return { products: PREVIEW_PRODUCTS };
  if (key === '/api/demo/simulate-product-page-errors') {
    return { recorded: 5, simulated: true, note: 'Five SIMULATED product-page failures were written to the request log. No AWS resource changed.' };
  }
  if (key === '/api/demo/clear-simulated') return { cleared: true };
  return {};
}

async function api(path, body) {
  if (PREVIEW) {
    await new Promise((r) => setTimeout(r, 280));
    return { data: previewData(path, body), headers: new Headers() };
  }
  const opts = body === undefined ? {} : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
  const r = await fetch(path, opts);
  let data = {};
  try { data = await r.json(); } catch { /* non-JSON error page */ }
  if (!r.ok) {
    const err = new Error(data.error || `Request failed (HTTP ${r.status})`);
    err.payload = data;
    throw err;
  }
  return { data, headers: r.headers };
}

function firstText(...values) {
  for (const value of values) {
    if (value == null) continue;
    const text = String(value).trim();
    if (text) return text;
  }
  return '';
}

function servedBy(data, headers) {
  const bag = data && typeof data.servedBy === 'object' && data.servedBy ? data.servedBy : {};
  const instances = data && typeof data.instances === 'object' && data.instances ? data.instances : {};
  const web = firstText(
    data && data.webInstance,
    data && data.webInstanceId,
    data && data.web_instance,
    bag.web,
    bag.webInstance,
    instances.web,
    headers && headers.get('x-web-instance'),
  );
  const application = firstText(
    data && data.appInstance,
    data && data.appInstanceId,
    data && data.applicationInstance,
    data && data.taskId,
    data && data.taskArn,
    typeof (data && data.servedBy) === 'string' ? data.servedBy : '',
    bag.application,
    bag.app,
    bag.appInstance,
    instances.application,
    instances.app,
    headers && headers.get('x-app-instance'),
  );
  const parts = [];
  if (web) parts.push(`Web ${esc(web)}`);
  if (application) parts.push(`Application ${esc(application)}`);
  return parts.length ? `Served by ${parts.join(' · ')}` : '';
}

function showServed(el, data, headers) {
  const text = servedBy(data, headers);
  if (!text) {
    el.hidden = true;
    el.textContent = '';
    return;
  }
  el.hidden = false;
  el.textContent = text;
}

function formatAnswer(text, skus) {
  let html = esc(text);
  for (const p of skus || []) {
    if (!p || !p.sku) continue;
    html = html.split(esc(p.sku)).join(`<span class="sku">${esc(p.sku)}</span>`);
  }
  return html.replace(/\[([\w.-]+\.md)\]/g, '<span class="cite">[$1]</span>');
}

function refusalHtml(answer) {
  if (!/loose AA/i.test(answer || '')) return '';
  if (!/\b(do not|don't|never|must not|not|forbids|forbidden|refuse)\b/i.test(answer || '')) return '';
  const sentence = String(answer).split(/(?<=\.)\s+/).find((s) => /loose AA/i.test(s));
  const line = sentence ? sentence.trim() : 'The safety guide forbids loose AA cells as the drive battery.';
  return `<div class="notice notice-warn"><strong>Loose AA cells refused.</strong> ${esc(line)}</div>`;
}

function skuCards(skus, refused) {
  if (!skus || !skus.length) return '<p class="empty">No catalog SKUs were named.</p>';
  return skus.map((p) => {
    const aa = refused && /^BT-AA-/.test(p.sku || '');
    return `<article class="sku-card">
      <div>
        <h3>${esc(p.name)}</h3>
        <p class="sku-line">${esc(p.sku)}</p>
        ${aa ? '<p class="refused-tag">Refused as the drive battery</p>' : ''}
      </div>
      <div class="sku-side">${money(p.price)}${stockBadge(p.stock)}</div>
    </article>`;
  }).join('');
}

function docList(sources) {
  return (sources || []).map((name) => {
    const title = DOC_TITLES[name] || name;
    return `<li><span class="doc-icon" aria-hidden="true"></span><span><span class="doc-title">${esc(title)}</span><span class="doc-file">${esc(name)}</span></span></li>`;
  }).join('');
}

function guideQuestion(product, question) {
  if (!product) return question;
  return `Product: ${product.name} (${product.sku}), category ${product.category}.\n${question}`;
}

function hasProblem(result) {
  if (!result || typeof result !== 'object') return false;
  return Boolean(result.error) || Number(result.recentErrors) > 0 || /no \(/.test(result.reachableFromApplication || '');
}

function parseDiagnosis(text) {
  const raw = String(text || '').trim();
  let tier = '';
  const labeled = raw.match(/tier at fault\s*[:\-–]\s*([^\n.]+)/i);
  if (labeled) {
    const named = labeled[1].toLowerCase().match(/\b(web|application|data)\b/);
    tier = named ? named[1] : labeled[1].trim();
  } else {
    const sentence = raw.match(/[^.]*\b(web|application|data)\b tier[^.]*\bat fault[^.]*\./i)
      || raw.match(/[^.]*\bat fault[^.]*\b(web|application|data)\b[^.]*\./i);
    if (sentence) {
      const named = sentence[0].toLowerCase().match(/\b(web|application|data)\b/);
      if (named) tier = named[1];
    }
  }
  const actionMatch = raw.match(/(?:proposed\s+)?next action\s*[:\-–]\s*([\s\S]+)/i);
  const action = actionMatch ? actionMatch[1].trim() : '';
  const pretty = { web: 'Web', application: 'Application', data: 'Data' };
  return { tier: pretty[tier.toLowerCase()] || tier, action };
}

const EXAMPLES = {
  battery: {
    category: 'hobby equipment',
    sku: 'HB-RC-TRUCK1',
    question: 'Which battery pack is safe for the Trailblazer beginner RC truck, and what is the return window if the customer changes their mind?',
  },
  kit: {
    category: 'hobby equipment',
    sku: 'HB-RC-TRUCK1',
    question: 'Build a beginner RC kit for a 10-year-old. The customer wants to power the truck with loose AA batteries.',
  },
  miss: {
    category: 'electronics',
    sku: 'EL-BTSPK-01',
    question: 'What is the employee discount?',
    bare: true,
  },
};

function initGuide() {
  const category = $('#category');
  const product = $('#product');
  const question = $('#q');
  const ask = $('#ask');
  const form = $('#guide-form');
  let catalog = [];
  let ticket = 0;
  let preferredSku = 'HB-RC-TRUCK1';

  function selectedProduct() {
    return catalog.find((p) => p.sku === product.value) || null;
  }

  function fillProducts() {
    const rows = catalog.filter((p) => p.category === category.value);
    if (!rows.length) {
      product.innerHTML = '<option value="">No products in this category</option>';
      renderCatalog([]);
      return;
    }
    product.innerHTML = rows.map((p) => `<option value="${esc(p.sku)}">${esc(p.name)}</option>`).join('');
    if (rows.some((p) => p.sku === preferredSku)) product.value = preferredSku;
    renderCatalog(rows);
    const chosen = selectedProduct();
    $('#picked').textContent = chosen
      ? `${chosen.name} · ${chosen.sku} · ${money(chosen.price)}`
      : '';
  }

  function renderCatalog(rows) {
    const caption = $('#catalog-caption');
    caption.textContent = rows.length
      ? `${category.options[category.selectedIndex].text} · ${rows.length} sample products`
      : 'No sample products in this category.';
    $('#catalog-list').innerHTML = rows.length
      ? rows.map((p) => `<article class="sku-card">
          <div>
            <h3>${esc(p.name)}</h3>
            <p class="sku-meta">${esc(p.description)}</p>
            <p class="sku-line">${esc(p.sku)}</p>
          </div>
          <div class="sku-side">${money(p.price)}${stockBadge(p.stock)}</div>
        </article>`).join('')
      : '';
  }

  category.addEventListener('change', () => {
    preferredSku = '';
    fillProducts();
  });
  product.addEventListener('change', () => {
    preferredSku = product.value;
    const chosen = selectedProduct();
    $('#picked').textContent = chosen
      ? `${chosen.name} · ${chosen.sku} · ${money(chosen.price)}`
      : '';
  });

  function applyExample(key) {
    const example = EXAMPLES[key];
    if (!example) return;
    category.value = example.category;
    preferredSku = example.sku;
    question.value = example.question;
    if (catalog.length) fillProducts();
    document.querySelectorAll('.chip').forEach((chip) => {
      chip.setAttribute('aria-pressed', String(chip.dataset.example === key));
    });
  }

  async function run(options = {}) {
    const text = question.value.trim();
    if (!text) {
      question.focus();
      return;
    }
    const chosen = options.bare ? null : selectedProduct();
    const payload = guideQuestion(chosen, text);
    if (payload.length > 1000) {
      $('#error').hidden = false;
      $('#error').textContent = 'Keep the question under 1000 characters.';
      return;
    }
    const my = ++ticket;
    ask.disabled = true;
    ask.textContent = 'Asking…';
    $('#error').hidden = true;
    $('#result').hidden = false;
    $('#hit').hidden = true;
    $('#miss').hidden = true;
    $('#served').hidden = true;
    $('#pending').hidden = false;
    $('#pending').innerHTML = skeleton(4);
    try {
      const { data, headers } = await api('/api/chat', { question: payload });
      if (my !== ticket) return;
      $('#pending').hidden = true;
      const found = Number(data.retrieved) > 0 && Array.isArray(data.sources) && data.sources.length > 0;
      const echo = chosen
        ? `${chosen.name} · ${text}`
        : text;
      if (!found) {
        $('#miss').hidden = false;
        $('#miss-echo').textContent = echo;
        $('#miss-detail').textContent = data.answer
          || 'Nothing in the product guides covers this question, so there is no answer.';
      } else {
        $('#hit').hidden = false;
        $('#echo').textContent = echo;
        $('#answer').innerHTML = formatAnswer(data.answer || '', data.skus);
        $('#refusal').innerHTML = refusalHtml(data.answer || '');
        $('#sources').innerHTML = docList(data.sources);
        const count = Number(data.retrieved);
        $('#retrieved').textContent = Number.isFinite(count) && count > 0
          ? `${count} passage${count === 1 ? '' : 's'} retrieved`
          : '';
        $('#skus').innerHTML = skuCards(data.skus, /loose AA/i.test(data.answer || ''));
      }
      showServed($('#served'), data, headers);
    } catch (e) {
      if (my !== ticket) return;
      $('#result').hidden = true;
      $('#error').hidden = false;
      $('#error').textContent = e.message;
    } finally {
      if (my === ticket) {
        ask.disabled = false;
        ask.textContent = 'Ask Guide';
      }
    }
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    run();
  });
  question.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      run();
    }
  });
  document.querySelectorAll('.chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      const example = EXAMPLES[chip.dataset.example];
      applyExample(chip.dataset.example);
      run({ bare: Boolean(example && example.bare) });
    });
  });

  api('/api/products').then(({ data }) => {
    catalog = Array.isArray(data.products) ? data.products : [];
    fillProducts();
    $('#catalog-error').hidden = true;
  }).catch((e) => {
    product.innerHTML = '<option value="">Catalog unavailable</option>';
    $('#picked').textContent = '';
    $('#catalog-caption').textContent = 'The product page could not read the catalog.';
    $('#catalog-list').innerHTML = '';
    $('#catalog-error').hidden = false;
    $('#catalog-error').textContent = e.message || 'The product page could not read the catalog.';
  });
}

function initShiftlead() {
  const question = $('#q');
  const ask = $('#ask');
  let sessionId = null;
  let ticket = 0;

  async function run() {
    const text = question.value.trim();
    if (!text) {
      question.focus();
      return;
    }
    const my = ++ticket;
    ask.disabled = true;
    ask.textContent = 'Checking…';
    $('#error').hidden = true;
    $('#result').hidden = false;
    $('#pending').hidden = false;
    $('#pending').innerHTML = skeleton(4);
    $('#diagnosis').hidden = true;
    $('#reply-wrap').hidden = true;
    $('#checks-wrap').hidden = true;
    $('#served').hidden = true;
    try {
      const { data, headers } = await api('/api/shiftlead', { question: text, sessionId });
      if (my !== ticket) return;
      sessionId = data.sessionId || sessionId;
      $('#pending').hidden = true;
      const parsed = parseDiagnosis(data.answer || '');
      $('#diagnosis').hidden = false;
      $('#tier-wrap').hidden = !parsed.tier;
      $('#tier').textContent = parsed.tier;
      $('#action-wrap').hidden = !parsed.action;
      $('#action').textContent = parsed.action;
      $('#ship').textContent = data.note || 'Proposal only. A person ships any change through CloudFormation.';
      $('#reply-wrap').hidden = false;
      $('#answer').textContent = data.answer || '';
      const runs = Array.isArray(data.toolsRun) ? data.toolsRun : [];
      $('#checks-wrap').hidden = false;
      $('#checks').innerHTML = runs.length
        ? runs.map((t) => {
          const label = TOOL_LABELS[t.tool] || t.tool || 'Check';
          return `<li><span class="dot${hasProblem(t.result) ? ' bad' : ''}"></span><span>${esc(label)}</span></li>`;
        }).join('')
        : '<li class="empty">No checks were returned.</li>';
      $('#raw').textContent = runs.length ? JSON.stringify(runs, null, 2) : '';
      $('#rawwrap').hidden = !runs.length;
      showServed($('#served'), data, headers);
    } catch (e) {
      if (my !== ticket) return;
      $('#result').hidden = true;
      $('#error').hidden = false;
      $('#error').textContent = e.message;
    } finally {
      if (my === ticket) {
        ask.disabled = false;
        ask.textContent = 'Diagnose';
      }
    }
  }

  $('#shift-form').addEventListener('submit', (e) => {
    e.preventDefault();
    run();
  });
  question.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      run();
    }
  });

  async function sim(path, pending) {
    const out = $('#simout');
    out.textContent = pending;
    try {
      const { data } = await api(path, {});
      if (data.note) out.textContent = data.note;
      else if (data.cleared) out.textContent = 'Simulated rows cleared.';
      else out.textContent = 'Done.';
    } catch (e) {
      out.textContent = e.message;
    }
  }

  $('#sim').addEventListener('click', () => sim('/api/demo/simulate-product-page-errors', 'Recording…'));
  $('#clr').addEventListener('click', () => sim('/api/demo/clear-simulated', 'Clearing…'));
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.body.dataset.view === 'guide') initGuide();
  if (document.body.dataset.view === 'shiftlead') initShiftlead();
});
