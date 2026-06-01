SELECTORS = {
    "chatgpt": {
        "input": "textarea, [contenteditable='true'], div.ProseMirror, [role='textbox']",
        "send": "button[data-testid='send-button'], button[aria-label*='Send'], button[aria-label*='发送'], button:has-text('Send')",
        "messages": "[data-message-author-role='assistant'], .markdown",
    },
    "claude": {
        "input": "div[contenteditable='true'], textarea, div.ProseMirror, [role='textbox']",
        "send": "button[aria-label*='Send'], button:has-text('Send')",
        "messages": "[data-testid*='message'], [data-testid*='conversation'], .font-claude-message, [class*='message'], main article, main [role='article']",
        "body_marker": "claude",
    },
    "gemini": {
        "input": "rich-textarea div[contenteditable='true'], textarea",
        "send": "button[aria-label*='Send']",
        "messages": ".model-response-text, message-content",
    },
    "kimi": {
        "input": "textarea, [contenteditable='true']",
        "send": "button",
        "messages": ".markdown, .message",
    },
    "claude_web": {
        "input": "div[contenteditable='true'], textarea, div.ProseMirror, [role='textbox']",
        "send": "button[aria-label*='Send'], button:has-text('Send')",
        "messages": "[data-testid*='message'], [data-testid*='conversation'], .font-claude-message, [class*='message'], main article, main [role='article']",
        "body_marker": "claude",
    },
    "doubao": {
        "input": "textarea, [contenteditable='true']",
        "send": "button",
        "messages": ".markdown, .message",
    },
}
URLS = {
    "chatgpt": "https://chatgpt.com/",
    "claude": "https://claude.ai/new",
    "gemini": "https://gemini.google.com/app",
    "kimi": "https://www.kimi.com/",
    "doubao": "https://www.doubao.com/chat/",
}
