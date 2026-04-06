// Runs in MAIN world (page JS context) to intercept Amadeus network responses
// Captures cryptic/PNR responses and ticket issuance (FA PAX) before DOM render
(function () {
  'use strict';

  let lastCaptured = '';

  // ── Text cleanup ──────────────────────────────────────────────────────────
  function cleanText(text) {
    return text
      .split('\n')
      .filter(line => line.trim() !== 'undefined')
      .join('\n')
      // Amadeus sparse-array artifact: passenger number and name split across lines
      // e.g. "  1\n.XIU/QI" → "  1.XIU/QI"
      .replace(/(\d)\s*\n\s*\./g, '$1.');
  }

  // ── PNR extraction ────────────────────────────────────────────────────────
  function extractLastPNR(text) {
    if (!text || typeof text !== 'string') return null;
    text = cleanText(text);

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

  // ── Ticket issuance extraction (FA PAX lines) ─────────────────────────────
  // Amadeus FA PAX formats:
  //   FA PAX 784-1234567890/ETCZ/EUR875.00/P1
  //   FA PAX 784-1234567890/S3/EUR875.00/ETCZ/P2
  //   FA PAX 160-9876543210/P1
  function extractTickets(text) {
    if (!text || typeof text !== 'string') return [];
    text = cleanText(text);
    const results = [];
    const re = /FA\s+PAX\s+(\d{3}-\d{10})((?:\/[^\s\n]+)*)/g;
    let m;
    while ((m = re.exec(text)) !== null) {
      const ticketNumber = m[1];
      const slashParts   = m[2] ? m[2].split('/').filter(Boolean) : [];

      // Passenger ref: /P1 /P2 etc (last /Pn in the parts)
      let passengerRef = '';
      for (const p of slashParts) {
        if (/^P\d+$/.test(p)) passengerRef = p;
      }

      // Amount: look for pattern like EUR875.00 or USD1234.56
      let currency = '', amount = 0;
      for (const p of slashParts) {
        const amtMatch = p.match(/^([A-Z]{3})([\d]+\.[\d]{2})$/);
        if (amtMatch) { currency = amtMatch[1]; amount = parseFloat(amtMatch[2]); break; }
      }

      results.push({ ticketNumber, passengerRef, currency, amount, raw: m[0].trim() });
    }
    return results;
  }

  // ── Recursive JSON search ─────────────────────────────────────────────────
  function searchJSONForPNR(obj, depth) {
    if (depth > 12) return null;
    if (typeof obj === 'string') return extractLastPNR(obj);
    if (Array.isArray(obj)) {
      for (const item of obj) { const r = searchJSONForPNR(item, depth + 1); if (r) return r; }
    } else if (obj && typeof obj === 'object') {
      for (const v of Object.values(obj)) { const r = searchJSONForPNR(v, depth + 1); if (r) return r; }
    }
    return null;
  }

  function searchJSONForTickets(obj, depth, acc) {
    if (depth > 12) return;
    if (typeof obj === 'string') {
      const t = extractTickets(obj);
      if (t.length) acc.push(...t);
    } else if (Array.isArray(obj)) {
      for (const item of obj) searchJSONForTickets(item, depth + 1, acc);
    } else if (obj && typeof obj === 'object') {
      for (const v of Object.values(obj)) searchJSONForTickets(v, depth + 1, acc);
    }
  }

  // ── Process a raw response body ───────────────────────────────────────────
  function processText(text) {
    if (!text) return;

    let parsed = null;
    try { parsed = JSON.parse(text); } catch (_) {}

    // PNR detection
    const pnr = parsed ? searchJSONForPNR(parsed, 0) : extractLastPNR(text);
    if (pnr && pnr !== lastCaptured) {
      lastCaptured = pnr;
      window.postMessage({ type: 'BILLETE_PNR_CAPTURED', pnr }, '*');
    }

    // Ticket detection
    const tickets = [];
    if (parsed) {
      searchJSONForTickets(parsed, 0, tickets);
    } else {
      tickets.push(...extractTickets(text));
    }
    if (tickets.length > 0) {
      window.postMessage({ type: 'BILLETE_TICKETS_CAPTURED', tickets }, '*');
    }
  }

  // ── Intercept fetch ────────────────────────────────────────────────────────
  const origFetch = window.fetch;
  window.fetch = async function (...args) {
    const response = await origFetch.apply(this, args);
    try {
      response.clone().text().then(processText).catch(() => {});
    } catch (_) {}
    return response;
  };

  // ── Intercept XMLHttpRequest ───────────────────────────────────────────────
  const origSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function (...args) {
    this.addEventListener('load', function () {
      if (this.responseText) processText(this.responseText);
    });
    return origSend.apply(this, args);
  };

  // ── Intercept WebSocket ────────────────────────────────────────────────────
  const OrigWS = window.WebSocket;
  function PatchedWebSocket(url, protocols) {
    const ws = protocols !== undefined ? new OrigWS(url, protocols) : new OrigWS(url);
    ws.addEventListener('message', (event) => {
      if (typeof event.data === 'string') {
        processText(event.data);
      } else if (event.data instanceof Blob) {
        event.data.text().then(processText).catch(() => {});
      }
    });
    return ws;
  }
  PatchedWebSocket.prototype    = OrigWS.prototype;
  PatchedWebSocket.CONNECTING   = OrigWS.CONNECTING;
  PatchedWebSocket.OPEN         = OrigWS.OPEN;
  PatchedWebSocket.CLOSING      = OrigWS.CLOSING;
  PatchedWebSocket.CLOSED       = OrigWS.CLOSED;
  window.WebSocket = PatchedWebSocket;

})();
