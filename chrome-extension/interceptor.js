// Runs in MAIN world (page JS context) to intercept Amadeus network responses
// Captures cryptic/PNR responses before they are rendered to DOM
(function () {
  'use strict';

  let lastCaptured = '';

  // ── PNR extraction helpers (duplicated here; MAIN world can't share modules) ─
  function extractLastPNR(text) {
    if (!text || typeof text !== 'string') return null;
    const rlrRe = /---\s*(?:TST\s+)?RLR\s*---/g;
    let lastMatch = null, m;
    while ((m = rlrRe.exec(text)) !== null) lastMatch = m;
    if (!lastMatch) return null;
    const start = lastMatch.index;
    const endIdx = text.indexOf(')>', start);
    return text.slice(start, endIdx !== -1 ? endIdx + 2 : text.length).trim();
  }

  // Recursively search all string values inside a parsed JSON object
  function searchJSON(obj, depth) {
    if (depth > 12) return null;
    if (typeof obj === 'string') return extractLastPNR(obj);
    if (Array.isArray(obj)) {
      for (const item of obj) {
        const r = searchJSON(item, depth + 1);
        if (r) return r;
      }
    } else if (obj && typeof obj === 'object') {
      for (const v of Object.values(obj)) {
        const r = searchJSON(v, depth + 1);
        if (r) return r;
      }
    }
    return null;
  }

  function tryExtract(text) {
    if (!text) return null;
    // Try JSON first (Amadeus SPC uses JSON APIs)
    try {
      const parsed = JSON.parse(text);
      const r = searchJSON(parsed, 0);
      if (r) return r;
    } catch (_) {}
    // Fallback: plain text
    return extractLastPNR(text);
  }

  function report(pnr) {
    if (!pnr || pnr === lastCaptured) return;
    lastCaptured = pnr;
    window.postMessage({ type: 'BILLETE_PNR_CAPTURED', pnr }, '*');
  }

  // ── Intercept fetch ────────────────────────────────────────────────────────
  const origFetch = window.fetch;
  window.fetch = async function (...args) {
    const response = await origFetch.apply(this, args);
    try {
      const clone = response.clone();
      clone.text().then(text => {
        const pnr = tryExtract(text);
        if (pnr) report(pnr);
      }).catch(() => {});
    } catch (_) {}
    return response;
  };

  // ── Intercept XMLHttpRequest ───────────────────────────────────────────────
  const origSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function (...args) {
    this.addEventListener('load', function () {
      if (this.responseText) {
        const pnr = tryExtract(this.responseText);
        if (pnr) report(pnr);
      }
    });
    return origSend.apply(this, args);
  };

  // ── Intercept WebSocket ────────────────────────────────────────────────────
  const OrigWS = window.WebSocket;
  function PatchedWebSocket(url, protocols) {
    const ws = protocols !== undefined
      ? new OrigWS(url, protocols)
      : new OrigWS(url);

    ws.addEventListener('message', (event) => {
      let text = null;
      if (typeof event.data === 'string') {
        text = event.data;
      } else if (event.data instanceof Blob) {
        event.data.text().then(t => {
          const pnr = tryExtract(t);
          if (pnr) report(pnr);
        }).catch(() => {});
        return;
      }
      if (text) {
        const pnr = tryExtract(text);
        if (pnr) report(pnr);
      }
    });
    return ws;
  }
  // Preserve static constants and prototype
  PatchedWebSocket.prototype = OrigWS.prototype;
  PatchedWebSocket.CONNECTING = OrigWS.CONNECTING;
  PatchedWebSocket.OPEN       = OrigWS.OPEN;
  PatchedWebSocket.CLOSING    = OrigWS.CLOSING;
  PatchedWebSocket.CLOSED     = OrigWS.CLOSED;
  window.WebSocket = PatchedWebSocket;

})();
