SELECTORS = {
    "chatgpt": {
        "input": "textarea, [contenteditable='true']",
        "send": "button[data-testid='send-button'], button[aria-label*='Send'], button:has-text('Send')",
        "messages": "[data-message-author-role='assistant'], .markdown",
    },
    "claude": {
        "input": "div[contenteditable='true'], textarea",
        "send": "button[aria-label*='Send'], button:has-text('Send')",
        "messages": "div[data-testid*='message'], .font-claude-message",
    },
    "gemini": {"input": "rich-textarea div[contenteditable='true'], textarea", "send": "button[aria-label*='Send']", "messages": ".model-response-text, message-content"},
    "kimi": {"input": "textarea, [contenteditable='true']", "send": "button", "messages": ".markdown, .message"},
    "doubao": {"input": "textarea, [contenteditable='true']", "send": "button", "messages": ".markdown, .message"},
}
URLS = {
    "chatgpt": "https://chatgpt.com/",
    "claude": "https://claude.ai/new",
    "gemini": "https://gemini.google.com/app",
    "kimi": "https://www.kimi.com/",
    "doubao": "https://www.doubao.com/chat/",
}
