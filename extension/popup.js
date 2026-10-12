/* Muse2API Cookie Import -- Reads muse.ai cookies and POSTs to muse2api service.
 *
 * Uses chrome.cookies instead of document.cookie.
 * The 4 essential cookies (hatch_sess / hatch_gw / hatch_vml /
 * hatch_native_auth_device) are marked httpOnly, so webpage scripts cannot read them.
 * Only browser extension cookies API can access them.
 */

const $ = (id) => document.getElementById(id);
const STORE = 'muse2api_ext_cfg';

const ESSENTIAL = ['hatch_sess', 'hatch_gw', 'hatch_vml', 'hatch_native_auth_device'];

function log(html, cls) {
  const el = $('log');
  el.className = 'show';
  el.innerHTML = cls ? `<span class="${cls}">${html}</span>` : html;
}

/* Normalize base URL: strip trailing slash and /v1 suffix */
function normBase(v) {
  let s = (v || '').trim();
  if (!s) return '';
  if (!/^https?:\/\//i.test(s)) s = 'https://' + s;
  s = s.replace(/\/+$/, '');
  s = s.replace(/\/v1$/i, '');
  return s;
}

async function loadCfg() {
  const o = await chrome.storage.local.get(STORE);
  const c = o[STORE] || {};
  if (c.base) $('base').value = c.base;
  if (c.key) $('key').value = c.key;
  if (c.label) $('label').value = c.label;
  // If not configured, try guessing from current tab (if user is on admin page)
  if (!c.base) {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const u = tab && tab.url ? new URL(tab.url) : null;
      if (u && /\/admin/.test(u.pathname)) {
        $('base').value = u.origin;
        const k = new URLSearchParams(u.search).get('key');
        if (k) $('key').value = k;
      }
    } catch (e) { /* ignore */ }
  }
}

async function saveCfg() {
  await chrome.storage.local.set({
    [STORE]: {
      base: normBase($('base').value),
      key: $('key').value.trim(),
      label: $('label').value.trim(),
    },
  });
}

async function grabCookies() {
  const all = await chrome.cookies.getAll({ domain: 'muse.ai' });
  const out = {}, exp = {};
  for (const c of all) {
    const dom = (c.domain || '').replace(/^\./, '');
    if (!dom.endsWith('muse.ai')) continue;
    out[c.name] = c.value;
    if (c.expirationDate) exp[c.name] = Math.floor(c.expirationDate);
  }
  return { cookies: out, expires: exp };
}

async function run() {
  const base = normBase($('base').value);
  const key = $('key').value.trim();
  const label = $('label').value.trim();

  if (!base) return log('Vui lòng điền địa chỉ dịch vụ (BASE URL)', 'bad');
  if (!key) return log('Vui lòng điền API Key', 'bad');

  $('go').disabled = true;
  log('Đang đọc Cookie của muse.ai…');

  try {
    const { cookies, expires } = await grabCookies();
    const names = Object.keys(cookies);
    if (!names.length) {
      return log('Không đọc được Cookie của muse.ai.\n'
                 + 'Vui lòng mở https://muse.ai/ trên trình duyệt này và đăng nhập, '
                 + 'sau đó nhấn lại nút.', 'bad');
    }
    const missing = ESSENTIAL.filter((n) => !(n in cookies));
    if (missing.length) {
      log(`Đã đọc ${names.length} Cookie nhưng thiếu các mục cốt lõi: ${missing.join(', ')}\n`
          + 'Cho thấy trình duyệt này chưa đăng nhập thành công. Vui lòng đăng nhập đến khi thấy giao diện chat rồi thử lại.', 'warn');
      return;
    }

    log(`Đã đọc ${names.length} Cookie, đang tải lên ${base} …`);

    const r = await fetch(base + '/admin/accounts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key,
      },
      body: JSON.stringify({ label, cookies, expires }),
    });

    const text = await r.text();
    let data;
    try { data = JSON.parse(text); } catch (e) { data = { raw: text }; }

    if (r.status === 401) {
      return log('API Key không chính xác (Dịch vụ trả về 401).\n'
                 + 'Vui lòng sao chép API Key chính xác từ đầu trang quản trị.', 'bad');
    }
    if (!r.ok) {
      return log(`Nhập thất bại: HTTP ${r.status}\n${text.slice(0, 300)}`, 'bad');
    }

    const a = (data.added && data.added[0]) || {};
    await saveCfg();
    log(`✓ Nhập thành công\nNhãn tài khoản: ${a.label || label || '(Tự động)'}\n`
        + `ID Tài khoản: ${a.id || '?'}\nSố lượng Cookie: ${a.cookie_count || names.length}\n`
        + `Thời hạn đến: ${a.expires_at ? new Date(a.expires_at * 1000).toLocaleString('vi-VN') : 'Không rõ'}\n`
        + (data.warning ? `\nLưu ý: ${data.warning}` : ''), 'ok');
  } catch (e) {
    log('Có lỗi xảy ra: ' + (e && e.message ? e.message : String(e))
        + '\n\nNguyên nhân phổ biến:\n'
        + '· Địa chỉ dịch vụ điền sai hoặc dịch vụ chưa khởi động\n'
        + '· Địa chỉ này không phải https (hoặc chứng chỉ không được tin cậy)\n'
        + '· Trình duyệt chặn yêu cầu liên miền (CORS)', 'bad');
  } finally {
    $('go').disabled = false;
  }
}

$('go').addEventListener('click', run);
loadCfg();
