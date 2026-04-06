'use strict';

// ── DOM refs ──────────────────────────────────────────────────────────────
const pnrInput       = document.getElementById('pnrInput');
const termInput      = document.getElementById('termInput');
const translateBtn   = document.getElementById('translateBtn');
const getFromPageBtn = document.getElementById('getFromPageBtn');
const handCount      = document.getElementById('handCount');
const handWeight     = document.getElementById('handWeight');
const packCount      = document.getElementById('packCount');
const packWeight     = document.getElementById('packWeight');
const resultSection  = document.getElementById('resultSection');
const resultBox      = document.getElementById('resultBox');
const copyBtn        = document.getElementById('copyBtn');
const imgBtn         = document.getElementById('imgBtn');
const errorBox       = document.getElementById('errorBox');

// Structured data from last translation, for image generation
let lastTranslateData = null;

// ── Get PNR from active Amadeus tab ──────────────────────────────────────
getFromPageBtn.addEventListener('click', async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) { showError('未找到活动标签页'); return; }

    try {
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_PAGE_TEXT' });
      if (response && response.text) {
        pnrInput.value = response.text;
        hideError();
        return;
      }
    } catch (_) {}

    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        function extractLastPNR(text) {
          if (!text) return null;
          // Format 1: --- (TST) RLR [MSC] --- ... )>
          const rlrRe = /---\s*(?:[A-Z]+\s+)?RLR(?:\s+[A-Z]+)?\s*---/g;
          let lastMatch = null, m;
          while ((m = rlrRe.exec(text)) !== null) lastMatch = m;
          if (lastMatch) {
            const start  = lastMatch.index;
            const endIdx = text.indexOf(')>', start);
            return text.slice(start, endIdx !== -1 ? endIdx + 2 : text.length).trim();
          }
          // Format 2: RP/OFFICE/ ... )>  (raw PNR without RLR wrapper)
          const rpRe = /^RP\/[A-Z0-9]+\//gm;
          let lastRp = null;
          while ((m = rpRe.exec(text)) !== null) lastRp = m;
          if (lastRp) {
            const start  = lastRp.index;
            const endIdx = text.indexOf(')>', start);
            return text.slice(start, endIdx !== -1 ? endIdx + 2 : text.length).trim();
          }
          return null;
        }
        const selectors = [
          '.terminal-output', '.cryptic-output',
          '[class*="TerminalOutput"]', '[class*="crypticArea"]',
          '[class*="pnrDisplay"]', '[class*="responseArea"]',
          'pre', 'textarea'
        ];
        const candidates = [];
        for (const sel of selectors) {
          for (const el of document.querySelectorAll(sel)) {
            const raw = (el.innerText || el.value || '').trim();
            if (raw.length > 50) candidates.push(raw);
          }
        }
        for (const raw of [...candidates].reverse()) {
          const pnr = extractLastPNR(raw);
          if (pnr) return pnr;
        }
        if (candidates.length > 0) return candidates[candidates.length - 1];
        return '';
      }
    });

    if (result && result.result) {
      pnrInput.value = result.result;
      hideError();
    } else {
      showError('页面上未找到PNR内容，请手动粘贴');
    }
  } catch (e) {
    showError('无法读取页面: ' + e.message);
  }
});

// ── Check for pending PNR (from context menu / floating button) ───────────
async function checkPendingPNR() {
  // Check both local (written by content.js click) and session (written by background)
  const [local, session] = await Promise.all([
    chrome.storage.local.get('pendingPNR'),
    chrome.storage.session.get('pendingPNR')
  ]);
  const pnr = local.pendingPNR || session.pendingPNR;
  if (pnr) {
    pnrInput.value = pnr;
    await Promise.all([
      chrome.storage.local.remove('pendingPNR'),
      chrome.storage.session.remove('pendingPNR')
    ]);
    doTranslate();
  }
}

// ── Translate ─────────────────────────────────────────────────────────────
translateBtn.addEventListener('click', doTranslate);
pnrInput.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.key === 'Enter') doTranslate();
});

async function doTranslate() {
  const code  = pnrInput.value.trim();
  const terms = termInput ? termInput.value.trim() : '';
  if (!code) { showError('请输入或粘贴PNR内容'); return; }

  hideError();
  resultSection.style.display = 'none';

  try {
    const customAirports = await loadCustomAirports();
    const logic  = new BilleteLogic(customAirports);
    const result = logic.process(code);

    const luggageOpts = {
      handCount:  parseInt(handCount.value)  || 1,
      handWeight: parseInt(handWeight.value) || 8,
      packCount:  parseInt(packCount.value)  || 2,
      packWeight: parseInt(packWeight.value) || 23,
    };

    const text = logic.generateText({ ...luggageOpts, terms });
    const output = text || result.text;

    // Save structured data for image generation
    lastTranslateData = { structured: result.structured, opts: { ...luggageOpts, terms } };

    displayResult(output);
    await saveHistory(code, output);
    renderHistoryList();
  } catch (e) {
    showError('解析失败: ' + e.message);
  }
}

function displayResult(text) {
  resultBox.textContent = text;
  resultSection.style.display = 'block';
  resultSection.scrollIntoView({ behavior: 'smooth' });
  navigator.clipboard.writeText(text).then(() => {
    copyBtn.textContent = '已复制 ✓';
    setTimeout(() => { copyBtn.textContent = '复制'; }, 1500);
  }).catch(() => {});
}

// ── Copy button ───────────────────────────────────────────────────────────
copyBtn.addEventListener('click', async () => {
  const text = resultBox.textContent;
  if (!text) return;
  await navigator.clipboard.writeText(text);
  copyBtn.textContent = '已复制 ✓';
  setTimeout(() => { copyBtn.textContent = '复制'; }, 1500);
});

// ── Generate Image ────────────────────────────────────────────────────────
imgBtn.addEventListener('click', async () => {
  if (!lastTranslateData) { showError('请先翻译PNR'); return; }
  try {
    imgBtn.textContent = '生成中...';
    imgBtn.disabled = true;
    const canvas = drawItineraryCanvas(lastTranslateData.structured, lastTranslateData.opts);
    canvas.toBlob(async (blob) => {
      imgBtn.disabled = false;
      if (!blob) { showError('生成图片失败'); return; }
      try {
        await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
        imgBtn.textContent = '已复制图片 ✓';
        setTimeout(() => { imgBtn.textContent = '生成图片'; }, 2000);
      } catch (_) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'billete_itinerary.png';
        a.click();
        URL.revokeObjectURL(url);
        imgBtn.textContent = '已下载 ✓';
        setTimeout(() => { imgBtn.textContent = '生成图片'; }, 2000);
      }
    }, 'image/png');
  } catch (e) {
    imgBtn.disabled = false;
    imgBtn.textContent = '生成图片';
    showError('生成图片失败: ' + e.message);
  }
});

// ── Canvas itinerary card renderer ────────────────────────────────────────
function drawItineraryCanvas(structured, opts) {
  const { passengers, flights, layovers } = structured;
  const { handCount, handWeight, packCount, packWeight, terms } = opts;

  const SCALE  = 2;
  const W      = 460;
  const PAD    = 20;
  const CW     = W - PAD * 2;   // card width
  const CP     = 14;             // card inner padding

  const HDR_H      = 90;
  const FLIGHT_H   = 150;
  const SECTION_H  = 44;
  const TRANSFER_H = 40;
  const LUGGAGE_H  = 92;

  const termsLines = terms ? terms.split('\n') : [];
  const TERMS_H    = termsLines.length > 0 ? (16 + termsLines.length * 20 + 12) : 0;

  // ── Pre-calculate total height ──
  let totalH = HDR_H + PAD;
  totalH += (24 + passengers.length * 22 + 16) + 14; // pax card + gap

  let _inRet = false, _outDone = false;
  for (let i = 0; i < flights.length; i++) {
    const f = flights[i];
    if (!_outDone) { totalH += SECTION_H; _outDone = true; }
    if (f.isReturn && !_inRet) { totalH += SECTION_H; _inRet = true; }
    totalH += FLIGHT_H + 10;
    const lv = layovers.find(l => l.flightIndex === i + 1 && l.type === 'layover');
    if (lv) totalH += TRANSFER_H + 6;
  }
  totalH += 8 + LUGGAGE_H + 14;
  if (TERMS_H) totalH += TERMS_H + 14;
  totalH += 50; // footer

  // ── Create canvas ──
  const canvas = document.createElement('canvas');
  canvas.width  = W * SCALE;
  canvas.height = totalH * SCALE;
  const ctx = canvas.getContext('2d');
  ctx.scale(SCALE, SCALE);

  // ── Helpers ──
  function rrect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y,     x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x,     y + h, r);
    ctx.arcTo(x,     y + h, x,     y,     r);
    ctx.arcTo(x,     y,     x + w, y,     r);
    ctx.closePath();
  }

  function card(x, y, w, h) {
    ctx.save();
    ctx.shadowColor = 'rgba(65,88,208,0.10)';
    ctx.shadowBlur  = 14;
    ctx.shadowOffsetY = 3;
    ctx.fillStyle = '#ffffff';
    rrect(x, y, w, h, 10);
    ctx.fill();
    ctx.restore();
  }

  function hline(x1, x2, y) {
    ctx.beginPath();
    ctx.moveTo(x1, y);
    ctx.lineTo(x2, y);
    ctx.stroke();
  }

  // ── Background ──
  ctx.fillStyle = '#eef0fb';
  ctx.fillRect(0, 0, W, totalH);

  // ── Header gradient ──
  const grad = ctx.createLinearGradient(0, 0, W * 0.7, HDR_H);
  grad.addColorStop(0, '#6C63FF');
  grad.addColorStop(1, '#4158D0');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, HDR_H);

  // Title
  ctx.fillStyle = '#ffffff';
  ctx.font = "bold 22px '微软雅黑','Microsoft YaHei',system-ui,sans-serif";
  ctx.fillText('行程确认单', PAD, 38);
  ctx.fillStyle = 'rgba(255,255,255,0.75)';
  ctx.font = "13px '微软雅黑',system-ui,sans-serif";
  ctx.fillText('Flight Itinerary', PAD, 58);

  // Passenger name + date (top-right)
  const pFirst = passengers.length > 0
    ? (passengers[0].name.split('/')[1] || passengers[0].name.split('/')[0])
    : '';
  const now    = new Date();
  const nowStr = `${now.getMonth() + 1}/${now.getDate()}/${now.getFullYear()}`;

  ctx.textAlign = 'right';
  ctx.fillStyle = '#ffffff';
  ctx.font = "bold 15px '微软雅黑',system-ui,sans-serif";
  ctx.fillText(pFirst, W - PAD - 46, 34);
  ctx.fillStyle = 'rgba(255,255,255,0.75)';
  ctx.font = "11px system-ui,sans-serif";
  ctx.fillText(nowStr, W - PAD - 46, 50);
  ctx.textAlign = 'left';

  // Heart button top-right
  ctx.fillStyle = 'rgba(255,255,255,0.18)';
  rrect(W - PAD - 36, 18, 32, 32, 8);
  ctx.fill();
  ctx.fillStyle = '#ff6b9d';
  ctx.font = '15px system-ui';
  ctx.textAlign = 'center';
  ctx.fillText('❤', W - PAD - 20, 38);
  ctx.textAlign = 'left';

  let y = HDR_H + PAD;

  // ── Passengers card ──
  const paxH = 24 + passengers.length * 22 + 16;
  card(PAD, y, CW, paxH);
  ctx.fillStyle = '#4158D0';
  ctx.font = "bold 12px '微软雅黑',system-ui,sans-serif";
  ctx.fillText('👥  乘客信息 / Passenger Details', PAD + CP, y + 20);
  ctx.strokeStyle = '#e8eaf6';
  ctx.lineWidth = 1;
  hline(PAD + CP, PAD + CW - CP, y + 28);
  passengers.forEach((p, idx) => {
    ctx.fillStyle = '#1a1a2e';
    ctx.font = "13px '微软雅黑',system-ui,sans-serif";
    ctx.fillText(`乘客 ${idx + 1}：${p.name}`, PAD + CP, y + 28 + 18 + idx * 22);
  });
  y += paxH + 14;

  // ── Flights ──
  let inReturn = false, outDone = false;

  for (let i = 0; i < flights.length; i++) {
    const f = flights[i];

    // Section labels
    if (!outDone) {
      ctx.fillStyle = '#4158D0';
      ctx.font = "bold 15px '微软雅黑',system-ui,sans-serif";
      ctx.fillText('去程 / Outbound', PAD, y + 20);
      y += SECTION_H;
      outDone = true;
    }
    if (f.isReturn && !inReturn) {
      ctx.fillStyle = '#e74c3c';
      ctx.font = "bold 15px '微软雅黑',system-ui,sans-serif";
      ctx.fillText('回程 / Return Trip', PAD, y + 20);
      y += SECTION_H;
      inReturn = true;
    }

    // ── Flight card ──
    card(PAD, y, CW, FLIGHT_H);

    // Date row
    ctx.fillStyle = '#888';
    ctx.font = "12px '微软雅黑',system-ui,sans-serif";
    ctx.fillText(`${f.year}年${f.month}月${f.day}日 / ${f.month}-${f.day}`, PAD + CP, y + 22);

    // Flight number badge
    const badgeW = 64;
    ctx.fillStyle = '#eef0fb';
    rrect(PAD + CW - CP - badgeW, y + 10, badgeW, 20, 4);
    ctx.fill();
    ctx.fillStyle = '#4158D0';
    ctx.font = "bold 11px system-ui,sans-serif";
    ctx.textAlign = 'center';
    ctx.fillText(f.id, PAD + CW - CP - badgeW / 2, y + 23);
    ctx.textAlign = 'left';

    // Divider
    ctx.strokeStyle = '#e8eaf6';
    ctx.lineWidth = 1;
    hline(PAD + CP, PAD + CW - CP, y + 32);

    // City names (big)
    ctx.font = "bold 20px '微软雅黑',system-ui,sans-serif";
    ctx.fillStyle = '#1a1a2e';
    ctx.fillText(f.origin, PAD + CP, y + 62);
    const origW = ctx.measureText(f.origin).width;

    ctx.textAlign = 'right';
    ctx.fillText(f.dest, PAD + CW - CP, y + 62);
    const destW = ctx.measureText(f.dest).width;
    ctx.textAlign = 'left';

    // Dashed line + plane between cities
    const lx1  = PAD + CP + origW + 8;
    const lx2  = PAD + CW - CP - destW - 8;
    const midX = (lx1 + lx2) / 2;
    const ly   = y + 55;

    ctx.strokeStyle = '#c5cae9';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 3]);
    ctx.beginPath(); ctx.moveTo(lx1, ly); ctx.lineTo(midX - 14, ly); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(midX + 14, ly); ctx.lineTo(lx2, ly); ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = '#4158D0';
    ctx.font = '16px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText('✈', midX, ly + 5);
    ctx.textAlign = 'left';

    // Departure time
    ctx.fillStyle = '#1a1a2e';
    ctx.font = "bold 20px '微软雅黑',system-ui,sans-serif";
    ctx.fillText(f.start, PAD + CP, y + 90);

    // Arrival time (right, +1 badge if next day)
    ctx.textAlign = 'right';
    if (f.nextDay) {
      ctx.font = "bold 20px '微软雅黑',system-ui,sans-serif";
      ctx.fillStyle = '#1a1a2e';
      ctx.fillText(f.end, PAD + CW - CP - 18, y + 90);
      ctx.fillStyle = '#e74c3c';
      ctx.font = "bold 11px system-ui,sans-serif";
      ctx.fillText('+1', PAD + CW - CP, y + 80);
    } else {
      ctx.font = "bold 20px '微软雅黑',system-ui,sans-serif";
      ctx.fillText(f.end, PAD + CW - CP, y + 90);
    }
    ctx.textAlign = 'left';

    // Dates below times
    ctx.fillStyle = '#aaa';
    ctx.font = "11px system-ui,sans-serif";
    ctx.fillText(`${f.month}-${f.day}`, PAD + CP, y + 106);
    ctx.textAlign = 'right';
    ctx.fillText(f.arrivalDate, PAD + CW - CP, y + 106);
    ctx.textAlign = 'left';

    // Bottom divider + class info
    ctx.strokeStyle = '#e8eaf6';
    ctx.lineWidth = 1;
    hline(PAD + CP, PAD + CW - CP, y + 116);
    ctx.fillStyle = '#aaa';
    ctx.font = "12px '微软雅黑',system-ui,sans-serif";
    ctx.fillText('Class: Economy  |  Non-Stop', PAD + CP, y + 136);

    y += FLIGHT_H + 10;

    // Layover after this flight
    const lv = layovers.find(l => l.flightIndex === i + 1 && l.type === 'layover');
    if (lv) {
      ctx.fillStyle = '#fff8e1';
      rrect(PAD + 16, y, CW - 32, TRANSFER_H, 8);
      ctx.fill();
      ctx.strokeStyle = '#ffe082';
      ctx.lineWidth = 1;
      rrect(PAD + 16, y, CW - 32, TRANSFER_H, 8);
      ctx.stroke();
      ctx.fillStyle = '#f57c00';
      ctx.font = "12px '微软雅黑',system-ui,sans-serif";
      ctx.textAlign = 'center';
      ctx.fillText(`⏳  转机时间：${lv.hours}h ${lv.minutes}m`, W / 2, y + 24);
      ctx.textAlign = 'left';
      y += TRANSFER_H + 6;
    }
  }

  y += 8;

  // ── Luggage card ──
  card(PAD, y, CW, LUGGAGE_H);
  ctx.fillStyle = '#4158D0';
  ctx.font = "bold 12px '微软雅黑',system-ui,sans-serif";
  ctx.fillText('🧳  行李额度 / Luggage Allowance', PAD + CP, y + 20);
  ctx.strokeStyle = '#e8eaf6';
  ctx.lineWidth = 1;
  hline(PAD + CP, PAD + CW - CP, y + 28);

  ctx.fillStyle = '#1a1a2e';
  ctx.font = "13px '微软雅黑',system-ui,sans-serif";
  ctx.fillText('经济舱往返', PAD + CP, y + 52);
  ctx.fillStyle = '#aaa';
  ctx.font = "11px '微软雅黑',system-ui,sans-serif";
  ctx.fillText('Economy Round Trip', PAD + CP, y + 68);

  // Checked baggage (right side)
  ctx.textAlign = 'center';
  ctx.font = '20px system-ui';
  ctx.fillText('🧳', PAD + CW - CP - 80, y + 52);
  ctx.font = "12px '微软雅黑',system-ui,sans-serif";
  ctx.fillStyle = '#1a1a2e';
  ctx.fillText(`${packCount} x ${packWeight}kg`, PAD + CW - CP - 80, y + 70);

  ctx.font = '20px system-ui';
  ctx.fillText('👜', PAD + CW - CP - 20, y + 52);
  ctx.font = "12px '微软雅黑',system-ui,sans-serif";
  ctx.fillText(`${handCount} x ${handWeight}kg`, PAD + CW - CP - 20, y + 70);
  ctx.textAlign = 'left';

  y += LUGGAGE_H + 14;

  // ── Terms card ──
  if (termsLines.length > 0) {
    card(PAD, y, CW, TERMS_H);
    termsLines.forEach((line, idx) => {
      ctx.fillStyle = idx === 0 ? '#4158D0' : '#333';
      ctx.font = idx === 0
        ? "bold 12px '微软雅黑',system-ui,sans-serif"
        : "12px '微软雅黑',system-ui,sans-serif";
      ctx.fillText(line, PAD + CP, y + 16 + idx * 20);
    });
    y += TERMS_H + 14;
  }

  // ── Footer ──
  ctx.fillStyle = '#aaa';
  ctx.font = "11px '微软雅黑',system-ui,sans-serif";
  ctx.textAlign = 'center';
  ctx.fillText('祝您旅途愉快  Have a pleasant journey!  |  Generated by Billete', W / 2, y + 22);
  ctx.textAlign = 'left';

  return canvas;
}

// ── Ticket Tracker ────────────────────────────────────────────────────────
const TICKETS_KEY = 'billeteTickets';
let ticketFilter  = 'pending';   // 'pending' | 'all'

async function getTickets() {
  const data = await chrome.storage.local.get(TICKETS_KEY);
  return data[TICKETS_KEY] || [];
}

async function clearTickets() {
  await chrome.storage.local.set({ [TICKETS_KEY]: [] });
  renderTicketList();
}

async function deleteTicket(id) {
  const tickets = await getTickets();
  await chrome.storage.local.set({ [TICKETS_KEY]: tickets.filter(t => String(t.id) !== String(id)) });
  renderTicketList();
}

function isPending(t) {
  // A ticket is "not yet departed" if its LAST departure date is today or future
  const ref = t.lastDepDate || t.firstDepDate;
  if (!ref) return true;   // no date info → assume pending
  const today = new Date().toISOString().slice(0, 10);
  return ref >= today;
}

async function renderTicketList() {
  const all      = await getTickets();
  const tickets  = ticketFilter === 'pending' ? all.filter(isPending) : all;

  const list     = document.getElementById('ticketList');
  const summary  = document.getElementById('ticketSummary');
  const badge    = document.getElementById('ticketBadge');
  const clearBtn = document.getElementById('clearTicketsBtn');

  // Badge always shows pending count
  const pendingCount = all.filter(isPending).length;
  badge.textContent   = pendingCount || '';
  badge.style.display = pendingCount ? '' : 'none';
  clearBtn.style.display = all.length ? '' : 'none';

  if (!tickets.length) {
    summary.style.display = 'none';
    list.innerHTML = `<div style="color:#9aa0a6;font-size:12px;padding:6px 0">${
      ticketFilter === 'pending' ? '暂无未起飞的票' : '暂无出票记录，将从Amadeus实时读取'
    }</div>`;
    return;
  }

  // Summary totals for current view
  const totals = {};
  for (const t of tickets) {
    if (t.amount && t.currency) totals[t.currency] = (totals[t.currency] || 0) + t.amount;
  }
  const totalStr = Object.entries(totals).map(([c, a]) => `${c} ${a.toFixed(2)}`).join(' + ');
  summary.style.display = '';
  summary.textContent = `${tickets.length} 张票${totalStr ? '  |  总金额: ' + totalStr : ''}`;

  list.innerHTML = tickets.map(t => {
    const amtStr  = t.amount && t.currency
      ? `<span class="ticket-amount">${t.currency} ${t.amount.toFixed(2)}</span>` : '';
    const depStr  = t.firstDepDate
      ? `<div class="ticket-dep">✈ 出发 ${t.firstDepDate}${t.lastDepDate && t.lastDepDate !== t.firstDepDate ? '  回程 ' + t.lastDepDate : ''}</div>`
      : '';
    const pending = isPending(t)
      ? '<span style="background:#e8f5e9;color:#2e7d32;border-radius:3px;padding:1px 5px;font-size:10px;margin-left:4px">未起飞</span>'
      : '<span style="background:#f1f3f4;color:#9aa0a6;border-radius:3px;padding:1px 5px;font-size:10px;margin-left:4px">已起飞</span>';
    return `<div class="ticket-item">
      <div class="ticket-num">${escHtml(t.ticketNumber)}${pending}</div>
      <div class="ticket-pax">${escHtml(t.passengerName || t.passengerRef || '未知乘客')}${amtStr ? '&nbsp;&nbsp;' + amtStr : ''}</div>
      ${depStr}
      <div class="ticket-meta">${escHtml(t.timestamp || '')}
        <button class="btn-sm tick-del" data-id="${t.id}" style="color:#c62828;margin-left:8px">删除</button>
      </div>
    </div>`;
  }).join('');

  list.querySelectorAll('.tick-del').forEach(btn => {
    btn.addEventListener('click', () => deleteTicket(btn.dataset.id));
  });
}

// Tab switching
document.querySelectorAll('.ticket-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    ticketFilter = tab.dataset.filter;
    document.querySelectorAll('.ticket-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    renderTicketList();
  });
});

// Toggle ticket section
document.getElementById('ticketToggle').addEventListener('click', () => {
  const panel = document.getElementById('ticketPanel');
  const arrow = document.getElementById('ticketArrow');
  const open  = panel.style.display !== 'none';
  panel.style.display = open ? 'none' : 'block';
  arrow.textContent   = open ? '▼' : '▲';
  if (!open) renderTicketList();
});

document.getElementById('clearTicketsBtn').addEventListener('click', clearTickets);

// Real-time storage update from content.js
chrome.storage.onChanged.addListener((changes, area) => {
  // Real-time PNR push from floating button click (content.js writes to local)
  if ((area === 'local' || area === 'session') && changes.pendingPNR?.newValue) {
    checkPendingPNR();
  }
  // Ticket tracker update
  if (area === 'local' && changes[TICKETS_KEY]) {
    const newVal = changes[TICKETS_KEY].newValue || [];
    renderTicketBadge(newVal);
    const panel = document.getElementById('ticketPanel');
    if (panel.style.display !== 'none') renderTicketList();
  }
});

function renderTicketBadge(tickets) {
  const badge       = document.getElementById('ticketBadge');
  const pendingCount = tickets.filter(isPending).length;
  badge.textContent   = pendingCount || '';
  badge.style.display = pendingCount ? '' : 'none';
}

// ── History ───────────────────────────────────────────────────────────────
const HISTORY_KEY = 'billeteHistory';
const HISTORY_MAX = 50;

async function saveHistory(code, result) {
  const data = await chrome.storage.local.get(HISTORY_KEY);
  const list = data[HISTORY_KEY] || [];
  const filtered = list.filter(h => h.code !== code);
  filtered.unshift({ id: Date.now(), timestamp: new Date().toLocaleString('zh-CN'), code, result });
  if (filtered.length > HISTORY_MAX) filtered.length = HISTORY_MAX;
  await chrome.storage.local.set({ [HISTORY_KEY]: filtered });
}

async function getHistory() {
  const data = await chrome.storage.local.get(HISTORY_KEY);
  return data[HISTORY_KEY] || [];
}

async function deleteHistoryItem(id) {
  const data = await chrome.storage.local.get(HISTORY_KEY);
  const list = (data[HISTORY_KEY] || []).filter(h => h.id !== id);
  await chrome.storage.local.set({ [HISTORY_KEY]: list });
  renderHistoryList();
}

async function clearHistory() {
  await chrome.storage.local.set({ [HISTORY_KEY]: [] });
  renderHistoryList();
}

async function renderHistoryList() {
  const list      = await getHistory();
  const container = document.getElementById('historyList');
  const clearBtn  = document.getElementById('clearHistoryBtn');

  if (!list.length) {
    container.innerHTML = '<div style="color:#9aa0a6;font-size:12px;padding:6px 0">暂无记录</div>';
    clearBtn.style.display = 'none';
    return;
  }

  clearBtn.style.display = '';
  container.innerHTML = list.map(h => {
    const preview = (h.result || '').split('\n')[0] || h.code.slice(0, 30);
    return `<div class="history-item" data-id="${h.id}">
      <div class="history-preview" title="${escHtml(h.result)}">${escHtml(preview)}</div>
      <div class="history-meta">${escHtml(h.timestamp)}</div>
      <div style="display:flex;gap:4px;margin-top:4px">
        <button class="btn-sm hist-restore" data-id="${h.id}">恢复</button>
        <button class="btn-sm hist-del" data-id="${h.id}" style="color:#c62828">删除</button>
      </div>
    </div>`;
  }).join('');

  container.querySelectorAll('.hist-restore').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id   = parseInt(btn.dataset.id);
      const list = await getHistory();
      const item = list.find(h => h.id === id);
      if (item) { pnrInput.value = item.code; doTranslate(); }
    });
  });
  container.querySelectorAll('.hist-del').forEach(btn => {
    btn.addEventListener('click', () => deleteHistoryItem(parseInt(btn.dataset.id)));
  });
}

document.getElementById('historyToggle').addEventListener('click', () => {
  const list  = document.getElementById('historyList');
  const arrow = document.getElementById('historyArrow');
  const open  = list.style.display !== 'none';
  list.style.display = open ? 'none' : 'block';
  arrow.textContent  = open ? '▼' : '▲';
  if (!open) renderHistoryList();
});

document.getElementById('clearHistoryBtn').addEventListener('click', clearHistory);

// ── Airport Code Management ───────────────────────────────────────────────
const AIRPORTS_KEY = 'billeteCustomAirports';

async function loadCustomAirports() {
  const data = await chrome.storage.local.get(AIRPORTS_KEY);
  return data[AIRPORTS_KEY] || {};
}

async function saveAirport(code, name) {
  const airports = await loadCustomAirports();
  airports[code.toUpperCase()] = name;
  await chrome.storage.local.set({ [AIRPORTS_KEY]: airports });
}

async function deleteAirport(code) {
  const airports = await loadCustomAirports();
  delete airports[code.toUpperCase()];
  await chrome.storage.local.set({ [AIRPORTS_KEY]: airports });
}

async function renderAirportList(filter = '') {
  const airports  = await loadCustomAirports();
  const container = document.getElementById('airportList');
  const entries   = Object.entries(airports).filter(([code, name]) =>
    !filter || code.includes(filter.toUpperCase()) || name.includes(filter)
  );

  if (!entries.length) {
    container.innerHTML = '<div style="color:#9aa0a6;font-size:12px;padding:4px 0">暂无自定义机场代码</div>';
    return;
  }

  container.innerHTML = entries.map(([code, name]) =>
    `<div class="airport-item">
      <span class="airport-code-tag">${escHtml(code)}</span>
      <span class="airport-name-text">${escHtml(name)}</span>
      <div style="display:flex;gap:4px;margin-left:auto">
        <button class="btn-sm ap-edit" data-code="${escHtml(code)}" data-name="${escHtml(name)}">编辑</button>
        <button class="btn-sm ap-del" data-code="${escHtml(code)}" style="color:#c62828">删除</button>
      </div>
    </div>`
  ).join('');

  container.querySelectorAll('.ap-edit').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('airportCode').value = btn.dataset.code;
      document.getElementById('airportName').value = btn.dataset.name;
    });
  });
  container.querySelectorAll('.ap-del').forEach(btn => {
    btn.addEventListener('click', async () => {
      await deleteAirport(btn.dataset.code);
      renderAirportList(document.getElementById('airportSearch').value);
    });
  });
}

document.getElementById('saveAirportBtn').addEventListener('click', async () => {
  const code = document.getElementById('airportCode').value.trim().toUpperCase();
  const name = document.getElementById('airportName').value.trim();
  if (!code || !name) { showError('请填写机场代码和名称'); return; }
  if (!/^[A-Z]{2,4}$/.test(code)) { showError('机场代码应为2-4位大写字母'); return; }
  await saveAirport(code, name);
  document.getElementById('airportCode').value = '';
  document.getElementById('airportName').value = '';
  renderAirportList(document.getElementById('airportSearch').value);
  hideError();
});

document.getElementById('airportSearch').addEventListener('input', (e) => {
  renderAirportList(e.target.value.trim());
});

document.getElementById('airportToggle').addEventListener('click', () => {
  const panel = document.getElementById('airportPanel');
  const arrow = document.getElementById('airportArrow');
  const open  = panel.style.display !== 'none';
  panel.style.display = open ? 'none' : 'block';
  arrow.textContent   = open ? '▼' : '▲';
  if (!open) renderAirportList();
});

// ── Helpers ───────────────────────────────────────────────────────────────
function showError(msg) {
  errorBox.textContent = msg;
  errorBox.classList.remove('hidden');
}
function hideError() {
  errorBox.classList.add('hidden');
}
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Init ──────────────────────────────────────────────────────────────────
checkPendingPNR();
window.addEventListener('focus', checkPendingPNR);
// Show ticket count badge on load
getTickets().then(renderTicketBadge);
