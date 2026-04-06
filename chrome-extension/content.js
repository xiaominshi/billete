// Content script - runs inside Amadeus web pages
// Detects PNR content, ticket issuance, and provides translation button

(function () {
  'use strict';

  // ── Chrome context guard ──────────────────────────────────────────────────
  // MV3 service workers sleep; SPA pages never reload → context can invalidate
  function isContextAlive() {
    try { return !!chrome.runtime?.id; } catch (_) { return false; }
  }

  function safeSendMessage(msg) {
    if (!isContextAlive()) return;
    try { chrome.runtime.sendMessage(msg); } catch (_) {}
  }

  async function safeStorageGet(key) {
    if (!isContextAlive()) return {};
    try { return await chrome.storage.local.get(key); } catch (_) { return {}; }
  }

  async function safeStorageSet(obj) {
    if (!isContextAlive()) return;
    try { await chrome.storage.local.set(obj); } catch (_) {}
  }

  let translateBtn    = null;
  let lastDetectedPNR = '';

  // Map of passenger refs P1/P2... → name, updated whenever a PNR is captured
  let passengerNames = {};   // { 'P1': 'SHI/XIAOMIN', 'P2': 'JI/LULU' }

  // ── Extract the last PNR block from terminal history ─────────────────────
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

  // ── Parse passenger names from PNR text ──────────────────────────────────
  function parsePassengerNames(pnr) {
    const map = {};
    const re = /(\d+)\.\s*([A-Z]+\/[A-Z]+)/g;
    let m;
    while ((m = re.exec(pnr)) !== null) map[`P${m[1]}`] = m[2];
    return map;
  }

  // ── Parse all flight departure dates from PNR ─────────────────────────────
  // Returns array of Date objects sorted ascending
  const MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  function parseFlightDates(pnr) {
    if (!pnr) return [];
    const dates = [];
    // Flight lines: "  3  CZ 378 Z 23MAY 6 MADCAN ..."
    // Match day+month token like 23MAY that appears after a flight number pattern
    const re = /\b[A-Z0-9]{2}\s*\d{3,4}\s+[A-Z]\s+(\d{1,2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b/g;
    const now = new Date();
    let baseYear = now.getFullYear();
    let lastMonth = null;
    let m;
    while ((m = re.exec(pnr)) !== null) {
      const day      = parseInt(m[1]);
      const monthIdx = MONTHS.indexOf(m[2]); // 0-based
      // Roll over year if month goes backward
      if (lastMonth !== null && monthIdx < lastMonth) baseYear++;
      lastMonth = monthIdx;
      dates.push(new Date(baseYear, monthIdx, day));
    }
    return dates.sort((a, b) => a - b);
  }

  // ── PNR detection heuristic ──────────────────────────────────────────────
  function looksLikePNR(text) {
    if (!text || text.trim().length < 20) return false;
    if (/---\s*(?:[A-Z]+\s+)?RLR(?:\s+[A-Z]+)?\s*---/.test(text)) return true;
    const hasPax       = /\d+[\.\s]\s*[A-Z]+\/[A-Z]+/.test(text);
    const hasFlight    = /\b[A-Z]{2}\s*\d{3,4}\b/.test(text);
    const hasDate      = /\b\d{1,2}[A-Z]{3}\b/.test(text);
    const hasCondensed = /[A-Z]+\/[A-Z]+\s+[A-Z]{2}\s+\d{3,4}\s+[A-Z]\s+\d{2}[A-Z]{3}/.test(text);
    return hasCondensed || (hasPax && hasDate) || (hasFlight && hasDate);
  }

  // ── Known Amadeus ASPC selectors ──────────────────────────────────────────
  const TERMINAL_SELECTORS = [
    '.terminal-output', '.cryptic-output',
    '[class*="TerminalOutput"]', '[class*="terminal-content"]',
    '[class*="crypticArea"]', '[class*="pnrDisplay"]',
    '[class*="responseArea"]', '.output-area', 'pre.output',
    'pre', 'textarea'
  ];

  function findTerminalText() {
    const candidates = [];
    for (const sel of TERMINAL_SELECTORS) {
      for (const el of document.querySelectorAll(sel)) {
        const raw = (el.innerText || el.value || '').trim();
        if (raw.length > 50) candidates.push(raw);
      }
    }
    for (const raw of [...candidates].reverse()) {
      const pnr = extractLastPNR(raw);
      if (pnr) return pnr;
    }
    for (const raw of [...candidates].reverse()) {
      if (looksLikePNR(raw)) return raw;
    }
    return null;
  }

  // ── Floating translate button ─────────────────────────────────────────────
  function createTranslateButton() {
    // If button was removed from DOM by SPA re-render, reset so we can recreate it
    if (translateBtn && !document.contains(translateBtn)) translateBtn = null;
    if (translateBtn) return;
    translateBtn = document.createElement('div');
    translateBtn.id = 'billete-translate-btn';
    translateBtn.innerHTML = `
      <span style="font-size:14px;">✈</span>
      <span>翻译PNR</span>
    `;
    Object.assign(translateBtn.style, {
      position: 'fixed', bottom: '24px', right: '24px',
      zIndex: '2147483647',
      background: 'linear-gradient(135deg, #1a73e8, #0d47a1)',
      color: '#fff', padding: '10px 18px', borderRadius: '24px',
      cursor: 'pointer', fontSize: '13px', fontFamily: 'system-ui, sans-serif',
      display: 'flex', alignItems: 'center', gap: '6px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.25)', userSelect: 'none',
      transition: 'transform 0.15s, box-shadow 0.15s'
    });
    translateBtn.addEventListener('mouseenter', function () {
      this.style.transform = 'scale(1.05)';
      this.style.boxShadow = '0 6px 20px rgba(0,0,0,0.35)';
    });
    translateBtn.addEventListener('mouseleave', function () {
      this.style.transform = '';
      this.style.boxShadow = '0 4px 16px rgba(0,0,0,0.25)';
    });
    translateBtn.addEventListener('click', async () => {
      const text = lastDetectedPNR || findTerminalText() || '';
      // Write PNR to session storage directly — sidepanel reads this on focus/open
      await safeStorageSet({ pendingPNR: text });
      // Also try to open the side panel via background (may fail silently if gesture lost)
      safeSendMessage({ type: 'OPEN_SIDE_PANEL', text });
      // Visual feedback so user knows the PNR was captured
      if (translateBtn) {
        const orig = translateBtn.innerHTML;
        translateBtn.innerHTML = '<span style="font-size:14px;">✓</span><span>已捕获，点击扩展图标</span>';
        setTimeout(() => { if (translateBtn) translateBtn.innerHTML = orig; }, 2500);
      }
    });
    document.body.appendChild(translateBtn);
  }

  function flashBtn(color) {
    if (!translateBtn) return;
    translateBtn.style.background = color;
    setTimeout(() => {
      if (translateBtn) translateBtn.style.background = 'linear-gradient(135deg, #1a73e8, #0d47a1)';
    }, 800);
  }

  // ── Text selection ────────────────────────────────────────────────────────
  document.addEventListener('mouseup', () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;
    const raw          = selection.toString().trim();
    const selectedText = extractLastPNR(raw) || raw;
    if (looksLikePNR(selectedText)) {
      lastDetectedPNR = selectedText;
      createTranslateButton();
      flashBtn('linear-gradient(135deg, #34a853, #1e7e34)');
    }
  });

  // ── Auto-scan ─────────────────────────────────────────────────────────────
  let scanTimeout = null;
  function scheduleScan() {
    clearTimeout(scanTimeout);
    scanTimeout = setTimeout(() => {
      const text = findTerminalText();
      if (text && text !== lastDetectedPNR) {
        lastDetectedPNR = text;
        createTranslateButton();
      }
    }, 500);
  }
  const observer = new MutationObserver(scheduleScan);
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  setTimeout(scheduleScan, 1500);

  // ── Save ticket records to storage ────────────────────────────────────────
  const TICKETS_KEY = 'billeteTickets';

  async function saveTickets(newTickets) {
    const data = await safeStorageGet(TICKETS_KEY);
    const existing = data[TICKETS_KEY] || [];

    // Deduplicate by ticket number
    const existingNums = new Set(existing.map(t => t.ticketNumber));
    const toAdd = newTickets.filter(t => !existingNums.has(t.ticketNumber));
    if (!toAdd.length) return;

    const now         = new Date().toLocaleString('zh-CN');
    const flightDates = parseFlightDates(lastDetectedPNR);
    // firstDep: ISO date string of first departure (for "not yet departed" filter)
    const firstDep  = flightDates.length ? flightDates[0].toISOString().slice(0, 10) : null;
    // lastDep: last departure date (return leg)
    const lastDep   = flightDates.length > 1 ? flightDates[flightDates.length - 1].toISOString().slice(0, 10) : firstDep;

    const enriched = toAdd.map(t => ({
      ...t,
      passengerName:  passengerNames[t.passengerRef] || t.passengerRef || '未知',
      timestamp:      now,
      firstDepDate:   firstDep,
      lastDepDate:    lastDep,
      allDepDates:    flightDates.map(d => d.toISOString().slice(0, 10)),
      id: Date.now() + Math.random()
    }));

    const updated = [...enriched, ...existing].slice(0, 200);
    await safeStorageSet({ [TICKETS_KEY]: updated });
  }

  // ── Listen for messages from MAIN-world interceptor ───────────────────────
  window.addEventListener('message', (event) => {
    if (event.source !== window || !event.data) return;

    if (event.data.type === 'BILLETE_PNR_CAPTURED') {
      const pnr = event.data.pnr;
      if (!pnr) return;
      lastDetectedPNR = pnr;
      // Update passenger name map from the fresh PNR
      const names = parsePassengerNames(pnr);
      if (Object.keys(names).length > 0) passengerNames = names;
      createTranslateButton();
      flashBtn('linear-gradient(135deg, #34a853, #1e7e34)');
    }

    if (event.data.type === 'BILLETE_TICKETS_CAPTURED') {
      const tickets = event.data.tickets;
      if (!tickets || !tickets.length) return;
      saveTickets(tickets);
    }
  });

  // ── Listen for "get page text" request from side panel ────────────────────
  if (isContextAlive()) {
    try {
      chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
        if (msg.type === 'GET_PAGE_TEXT') {
          const text = lastDetectedPNR || findTerminalText() || '';
          sendResponse({ text });
        }
        return true;
      });
    } catch (_) {}
  }

})();
