'use strict';

// ── DOM refs ──────────────────────────────────────────────────────────────
const pnrInput       = document.getElementById('pnrInput');
const translateBtn   = document.getElementById('translateBtn');
const getFromPageBtn = document.getElementById('getFromPageBtn');
const handCount      = document.getElementById('handCount');
const handWeight     = document.getElementById('handWeight');
const packCount      = document.getElementById('packCount');
const packWeight     = document.getElementById('packWeight');
const resultSection  = document.getElementById('resultSection');
const resultBox      = document.getElementById('resultBox');
const copyBtn        = document.getElementById('copyBtn');
const errorBox       = document.getElementById('errorBox');

// ── Get PNR from active Amadeus tab ──────────────────────────────────────
getFromPageBtn.addEventListener('click', async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) { showError('未找到活动标签页'); return; }

    // Try content script first (injected on Amadeus pages)
    try {
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_PAGE_TEXT' });
      if (response && response.text) {
        pnrInput.value = response.text;
        hideError();
        return;
      }
    } catch (_) { /* not on an Amadeus page, fall through */ }

    // Fallback: inject script to read page content and extract last PNR block
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        function extractLastPNR(text) {
          if (!text) return null;
          const rlrRe = /---\s*(?:TST\s+)?RLR\s*---/g;
          let lastMatch = null, m;
          while ((m = rlrRe.exec(text)) !== null) lastMatch = m;
          if (!lastMatch) return null;
          const start = lastMatch.index;
          const endIdx = text.indexOf(')>', start);
          return text.slice(start, endIdx !== -1 ? endIdx + 2 : text.length).trim();
        }
        const selectors = [
          '.terminal-output', '.cryptic-output',
          '[class*="TerminalOutput"]', '[class*="crypticArea"]',
          '[class*="pnrDisplay"]', '[class*="responseArea"]',
          'pre', 'textarea'
        ];
        // Collect all candidate text blocks
        const candidates = [];
        for (const sel of selectors) {
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
        // Priority 2: return the last candidate
        if (candidates.length > 0) {
          return candidates[candidates.length - 1];
        }
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
  const data = await chrome.storage.session.get('pendingPNR');
  if (data.pendingPNR) {
    pnrInput.value = data.pendingPNR;
    await chrome.storage.session.remove('pendingPNR');
    doTranslate();
  }
}

// ── Translate (pure JS, no server) ────────────────────────────────────────
translateBtn.addEventListener('click', doTranslate);

pnrInput.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.key === 'Enter') doTranslate();
});

function doTranslate() {
  const code = pnrInput.value.trim();
  if (!code) { showError('请输入或粘贴PNR内容'); return; }

  hideError();
  resultSection.style.display = 'none';

  try {
    // Load custom airports from storage (if any)
    const logic = new BilleteLogic();

    const result = logic.process(code);

    const text = logic.generateText({
      handCount:  parseInt(handCount.value)  || 1,
      handWeight: parseInt(handWeight.value) || 8,
      packCount:  parseInt(packCount.value)  || 2,
      packWeight: parseInt(packWeight.value) || 23
    });

    displayResult(text || result.text);
  } catch (e) {
    showError('解析失败: ' + e.message);
  }
}

function displayResult(text) {
  resultBox.textContent = text;
  resultSection.style.display = 'block';
  resultSection.scrollIntoView({ behavior: 'smooth' });
}

// ── Copy button ───────────────────────────────────────────────────────────
copyBtn.addEventListener('click', async () => {
  const text = resultBox.textContent;
  if (!text) return;
  await navigator.clipboard.writeText(text);
  copyBtn.textContent = '已复制 ✓';
  setTimeout(() => { copyBtn.textContent = '复制'; }, 1500);
});

// ── Helpers ───────────────────────────────────────────────────────────────
function showError(msg) {
  errorBox.textContent = msg;
  errorBox.classList.remove('hidden');
}
function hideError() {
  errorBox.classList.add('hidden');
}

// ── Init ──────────────────────────────────────────────────────────────────
checkPendingPNR();
window.addEventListener('focus', checkPendingPNR);
