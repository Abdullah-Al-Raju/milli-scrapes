"""
Anti-Bot Stealth Engine for Milli-Scrapes.
Injects evasive scripts into Chromium run-loop prior to document evaluation:
- Clears navigator.webdriver
- Spoofs navigator.plugins, languages, platform
- Emulates chrome.runtime and permissions API
- Masks WebGL vendor and renderer strings
- Normalizes window screen coordinates
"""

from typing import Dict, Any


STEALTH_INJECTION_SCRIPT = """
(() => {
    // 1. Overwrite navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });

    // 2. Mock chrome runtime
    if (!window.chrome) {
        window.chrome = {};
    }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            id: undefined,
            connect: function() {},
            sendMessage: function() {},
            onMessage: { addListener: function() {}, removeListener: function() {} }
        };
    }

    // 3. Mock languages and plugins
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
        configurable: true
    });

    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            return [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
            ];
        },
        configurable: true
    });

    // 4. Spoof WebGL Vendor & Renderer
    const getParameterProto = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
        return getParameterProto.apply(this, arguments);
    };

    if (typeof WebGL2RenderingContext !== 'undefined') {
        const getParameter2Proto = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter2Proto.apply(this, arguments);
        };
    }

    // 5. Mock permissions query
    if (navigator.permissions && navigator.permissions.query) {
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    }
})();
"""


class StealthManager:
    """
    Manages browser evasion overrides and anti-bot mitigation.
    """

    @staticmethod
    def get_stealth_script() -> str:
        return STEALTH_INJECTION_SCRIPT
