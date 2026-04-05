// Service Worker - handles extension lifecycle and messaging

// Open side panel when action button is clicked
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

// Create context menu for text selection
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'translate-selection',
    title: '翻译选中的PNR内容',
    contexts: ['selection']
  });
});

// Handle context menu click
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'translate-selection' && info.selectionText) {
    // Open side panel and send the selected text
    chrome.sidePanel.open({ tabId: tab.id });
    // Store the text so sidepanel can retrieve it
    chrome.storage.session.set({ pendingPNR: info.selectionText });
  }
});

// Handle messages from content script and side panel
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'OPEN_SIDE_PANEL') {
    chrome.sidePanel.open({ tabId: sender.tab.id });
    if (msg.text) {
      chrome.storage.session.set({ pendingPNR: msg.text });
    }
    sendResponse({ ok: true });
  }
  return true;
});
