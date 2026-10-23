"""
Anti-Bot Stealth and Fingerprint Randomization Engine for Milli-Scrapes.
Injects comprehensive evasion overrides into Chromium run-loop prior to document evaluation:
- Clears navigator.webdriver at the prototype level
- Emulates window.chrome, chrome.runtime, chrome.csi, and chrome.loadTimes
- Canvas Fingerprint Jitter: Microscopic RGB noise to scramble canvas hash tracking
- AudioContext Fingerprint Jitter: Defeats audio frequency hash tracking
- WebGL Vendor & Renderer spoofing: Mimics real hardware graphics drivers
- Spoofs hardwareConcurrency, deviceMemory, maxTouchPoints, and permissions
"""

from typing import Dict, Any


STEALTH_INJECTION_SCRIPT = """
(() => {
    // 1. Overwrite navigator.webdriver completely
    try {
        delete Navigator.prototype.webdriver;
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
    } catch (e) {}

    // 2. Comprehensive window.chrome emulation
    if (!window.chrome) {
        window.chrome = {};
    }
    window.chrome.app = window.chrome.app || { isInstalled: false };
    window.chrome.csi = window.chrome.csi || function() { return {}; };
    window.chrome.loadTimes = window.chrome.loadTimes || function() { return {}; };
    window.chrome.runtime = window.chrome.runtime || {
        id: undefined,
        connect: function() {},
        sendMessage: function() {},
        onMessage: { addListener: function() {}, removeListener: function() {} }
    };

    // 3. Spoof navigator hardware properties
    try {
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8, configurable: true });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 8, configurable: true });
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0, configurable: true });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'], configurable: true });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
            ],
            configurable: true
        });
    } catch (e) {}

    // 4. Canvas Fingerprint Micro-Jitter (Defeats FingerprintJS and canvas tracking)
    try {
        const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            const ctx = this.getContext('2d');
            if (ctx && this.width > 16 && this.height > 16) {
                // Introduce an imperceptible 1-bit jitter in a corner pixel to randomize hash
                try {
                    const imgData = ctx.getImageData(0, 0, 1, 1);
                    imgData.data[0] = (imgData.data[0] ^ 1);
                    ctx.putImageData(imgData, 0, 0);
                } catch (e) {}
            }
            return origToDataURL.apply(this, arguments);
        };

        const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function() {
            const res = origGetImageData.apply(this, arguments);
            // Slight jitter on last byte to scramble bulk canvas hashes
            if (res && res.data && res.data.length > 4) {
                res.data[res.data.length - 2] = res.data[res.data.length - 2] ^ 1;
            }
            return res;
        };
    } catch (e) {}

    // 5. Spoof WebGL Vendor & Renderer
    try {
        const getParameterProto = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // UNMASKED_VENDOR_WEBGL
            if (parameter === 37445) return 'Google Inc. (NVIDIA)';
            // UNMASKED_RENDERER_WEBGL
            if (parameter === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)';
            return getParameterProto.apply(this, arguments);
        };

        if (typeof WebGL2RenderingContext !== 'undefined') {
            const getParameter2Proto = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Google Inc. (NVIDIA)';
                if (parameter === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                return getParameter2Proto.apply(this, arguments);
            };
        }
    } catch (e) {}

    // 6. AudioContext Fingerprint Jitter
    try {
        if (window.AudioBuffer) {
            const origGetChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function() {
                const results = origGetChannelData.apply(this, arguments);
                if (results && results.length > 0) {
                    // Inject undetectable delta (1e-7)
                    results[0] += 0.0000001;
                }
                return results;
            };
        }
    } catch (e) {}

    // 7. Mock Permissions API
    try {
        if (navigator.permissions && navigator.permissions.query) {
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        }
    } catch (e) {}
})();
"""


class StealthManager:
    """
    Manages browser evasion overrides and anti-bot mitigation.
    """

    @staticmethod
    def get_stealth_script() -> str:
        """Returns the full JavaScript payload injected into every browser context."""
        return STEALTH_INJECTION_SCRIPT
