// Content script - runs inside Amadeus web pages
// Detects PNR content and provides translation button

(function () {
  'use strict';

  let translateBtn = null;
  let lastDetectedPNR = '';

  // ── Extract the last PNR block from terminal history ─────────────────────
  // Amadeus terminal shows multiple command/response pairs.
  // A PNR block starts with "--- (TST )RLR ---" and ends with ")>"
  function extractLastPNR(text) {
    if (!text) return null;
    // Find the last occurrence of --- (TST )?RLR ---
    const rlrRe = /---\s*(?:TST\s+)?RLR\s*---/g;
    let lastMatch = null, m;
    while ((m = rlrRe.exec(text)) !== null) lastMatch = m;
    if (!lastMatch) return null;

    const start = lastMatch.index;
    const endIdx = text.indexOf(')>', start);
    return text.slice(start, endIdx !== -1 ? endIdx + 2 : text.length).trim();
  }

  // ── PNR detection heuristic ──────────────────────────────────────────────
  function looksLikePNR(text) {
    if (!text || text.trim().length < 20) return false;
    if (/---\s*(?:TST\s+)?RLR\s*---/.test(text)) return true;       // definitive marker
    const hasPax       = /\d+[\.\s]\s*[A-Z]+\/[A-Z]+/.test(text);
    const hasFlight    = /\b[A-Z]{2}\s*\d{3,4}\b/.test(text);
    const hasDate      = /\b\d{1,2}[A-Z]{3}\b/.test(text);
    const hasCondensed = /[A-Z]+\/[A-Z]+\s+[A-Z]{2}\s+\d{3,4}\s+[A-Z]\s+\d{2}[A-Z]{3}/.test(text);
    return hasCondensed || (hasPax && hasDate) || (hasFlight && hasDate);
  }

  // ── Known Amadeus ASPC selectors (best-effort, may vary by version) ──────
  const TERMINAL_SELECTORS = [
    '.terminal-output',
    '.cryptic-output',
    '[class*="TerminalOutput"]',
    '[class*="terminal-content"]',
    '[class*="crypticArea"]',
    '[class*="pnrDisplay"]',
    '[class*="responseArea"]',
    '.output-area',
    'pre.output',
    // Generic fallback: any <pre> or <textarea> with PNR-like content
    'pre',
    'textarea'
  ];

  function findTerminalText() {
    const candidates = [];
    for (const sel of TERMINAL_SELECTORS) {
      for (const el of document.querySelectorAll(sel)) {
        const raw = (el.innerText || el.value || '').trim();
        if (raw.length > 50) candidates.push(raw);
      }
    }

    // Priority 1: scan in REVERSE order → last element with an RLR block wins
    for (const raw of [...candidates].reverse()) {
      const pnr = extractLastPNR(raw);
      if (pnr) return pnr;
    }

    // Priority 2: last element that looks like a standalone PNR
    for (const raw of [...candidates].reverse()) {
      if (looksLikePNR(raw)) return raw;
    }

    return null;
  }

  // ── Floating translate button ─────────────────────────────────────────────
  function createTranslateButton() {
    if (translateBtn) return;
    translateBtn = document.createElement('div');
    translateBtn.id = 'billete-translate-btn';
    translateBtn.innerHTML = `
      <span style="font-size:14px;">✈</span>
      <span>翻译PNR</span>
    `;
    Object.assign(translateBtn.style, {
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: '2147483647',
      background: 'linear-gradient(135deg, #1a73e8, #0d47a1)',
      color: '#fff',
      padding: '10px 18px',
      borderRadius: '24px',
      cursor: 'pointer',
      fontSize: '13px',
      fontFamily: 'system-ui, sans-serif',
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
      userSelect: 'none',
      transition: 'transform 0.15s, box-shadow 0.15s'
    });

    translateBtn.addEventListener('mouseenter', () => {
      translateBtn.style.transform = 'scale(1.05)';
      translateBtn.style.boxShadow = '0 6px 20px rgba(0,0,0,0.35)';
    });
    translateBtn.addEventListener('mouseleave', () => {
      translateBtn.style.transform = '';
      translateBtn.style.boxShadow = '0 4px 16px rgba(0,0,0,0.25)';
    });

    translateBtn.addEventListener('click', () => {
      const text = lastDetectedPNR || findTerminalText();
      chrome.runtime.sendMessage({
        type: 'OPEN_SIDE_PANEL',
        text: text || ''
      });
    });

    document.body.appendChild(translateBtn);
  }

  // ── Text selection: show button + capture selected PNR ────────────────────
  document.addEventListener('mouseup', () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;
    const raw = selection.toString().trim();
    const selectedText = extractLastPNR(raw) || raw;
    if (looksLikePNR(selectedText)) {
      lastDetectedPNR = selectedText;
      createTranslateButton();
      // Flash button to indicate detection
      if (translateBtn) {
        translateBtn.style.background = 'linear-gradient(135deg, #34a853, #1e7e34)';
        setTimeout(() => {
          if (translateBtn) {
            translateBtn.style.background = 'linear-gradient(135deg, #1a73e8, #0d47a1)';
          }
        }, 800);
      }
    }
  });

  // ── Auto-scan: watch for page changes (terminal updates) ──────────────────
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

  // Initial scan after page load
  setTimeout(scheduleScan, 1500);

  // ── Listen for PNR captured by the MAIN-world interceptor ───────────────
  window.addEventListener('message', (event) => {
    if (event.source !== window) return;
    if (!event.data || event.data.type !== 'BILLETE_PNR_CAPTURED') return;
    const pnr = event.data.pnr;
    if (!pnr) return;
    lastDetectedPNR = pnr;
    createTranslateButton();
    // Flash green to indicate a fresh capture
    if (translateBtn) {
      translateBtn.style.background = 'linear-gradient(135deg, #34a853, #1e7e34)';
      setTimeout(() => {
        if (translateBtn) {
          translateBtn.style.background = 'linear-gradient(135deg, #1a73e8, #0d47a1)';
        }
      }, 800);
    }
  });

  // ── Listen for "get page text" request from side panel ────────────────────
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === 'GET_PAGE_TEXT') {
      const text = lastDetectedPNR || findTerminalText() || '';
      sendResponse({ text });
    }
    return true;
  });

})();
