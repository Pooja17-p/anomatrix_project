/**
 * Client-Side Device Biometrics & Fingerprint Extractor for ANOMATRIX Zero Trust
 * Collects browser features, hardware specs, WebGL renderer, HTML5 Canvas signature hash,
 * screen resolution, locale, and network telemetry.
 */

// Helper to generate a simple fast hash of a canvas data URL
function hashCanvasData(dataUrl) {
  let hash = 0;
  if (!dataUrl || dataUrl.length === 0) return "canvas_unsupported";

  for (let i = 0; i < dataUrl.length; i++) {
    const char = dataUrl.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0; // Convert to 32bit integer
  }
  return "cv_" + Math.abs(hash).toString(16) + "_" + dataUrl.length;
}

// Generate invisible HTML5 Canvas Signature
function getCanvasFingerprint() {
  try {
    const canvas = document.createElement("canvas");
    canvas.width = 240;
    canvas.height = 140;
    const ctx = canvas.getContext("2d");

    if (!ctx) return "canvas_no_context";

    // Text with different fonts and styling
    ctx.textBaseline = "top";
    ctx.font = "14px 'Arial', sans-serif";
    ctx.fillStyle = "#f60";
    ctx.fillRect(125, 1, 62, 20);

    ctx.fillStyle = "#069";
    ctx.fillText("AnomatriX Sec 2026! @#$", 2, 15);
    ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
    ctx.fillText("ZeroTrust Biometrics", 4, 45);

    // Geometric Shapes & Curves
    ctx.strokeStyle = "rgba(120, 20, 240, 0.8)";
    ctx.beginPath();
    ctx.arc(50, 90, 30, 0, Math.PI * 2, true);
    ctx.closePath();
    ctx.stroke();

    return hashCanvasData(canvas.toDataURL());
  } catch (e) {
    return "canvas_error_" + e.message;
  }
}

// Extract WebGL GPU Vendor & Renderer Info
function getWebGLInfo() {
  try {
    const canvas = document.createElement("canvas");
    const gl =
      canvas.getContext("webgl") || canvas.getContext("experimental-webgl");

    if (!gl) return { vendor: "WebGL Unsupported", renderer: "WebGL Unsupported" };

    const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
    if (debugInfo) {
      const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || "Unknown Vendor";
      const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || "Unknown Renderer";
      return { vendor, renderer };
    }

    return {
      vendor: gl.getParameter(gl.VENDOR) || "Generic WebGL Vendor",
      renderer: gl.getParameter(gl.RENDERER) || "Generic WebGL Renderer",
    };
  } catch (e) {
    return { vendor: "WebGL Error", renderer: e.message };
  }
}

// Parse Browser Name and Version from User Agent
function getBrowserInfo() {
  const ua = navigator.userAgent;
  let browserName = "Unknown Browser";
  let browserVersion = "0.0";

  if (ua.includes("Firefox/")) {
    browserName = "Firefox";
    browserVersion = ua.split("Firefox/")[1] || "";
  } else if (ua.includes("Edg/")) {
    browserName = "Edge";
    browserVersion = ua.split("Edg/")[1] || "";
  } else if (ua.includes("Chrome/")) {
    browserName = "Chrome";
    browserVersion = ua.split("Chrome/")[1]?.split(" ")[0] || "";
  } else if (ua.includes("Safari/") && !ua.includes("Chrome/")) {
    browserName = "Safari";
    browserVersion = ua.split("Version/")[1]?.split(" ")[0] || "";
  }

  return { name: browserName, version: browserVersion };
}

// Detect Operating System
function getOSInfo() {
  const ua = navigator.userAgent;
  const platform = navigator.platform || "";

  if (ua.includes("Win")) return "Windows 10/11";
  if (ua.includes("Mac")) return "macOS";
  if (ua.includes("Linux")) return "Linux";
  if (ua.includes("Android")) return "Android";
  if (ua.includes("like Mac")) return "iOS";

  return platform || "Unknown OS";
}

/**
 * Main Attribute Collector Function
 * Extracts full client-side biometrics dictionary.
 */
export function extractDeviceFingerprint() {
  const browser = getBrowserInfo();
  const webgl = getWebGLInfo();
  const canvasHash = getCanvasFingerprint();

  const timezone =
    Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Kolkata";

  const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

  return {
    browser_name: browser.name,
    browser_version: browser.version,
    os: getOSInfo(),
    platform: navigator.platform || "Unknown",
    screen_resolution: `${window.screen.width}x${window.screen.height}`,
    color_depth: window.screen.colorDepth || 24,
    pixel_ratio: window.devicePixelRatio || 1,
    hardware_concurrency: navigator.hardwareConcurrency || 4,
    device_memory: navigator.deviceMemory || 8,
    language: navigator.language || "en-US",
    timezone,
    webgl_vendor: webgl.vendor,
    webgl_renderer: webgl.renderer,
    canvas_hash: canvasHash,
    network_type: conn?.effectiveType || "4g",
    downlink: conn?.downlink || 10,
    rtt: conn?.rtt || 50,
    user_agent: navigator.userAgent,
    timestamp: new Date().toISOString(),
  };
}
