export const W = 1920;
export const H = 1080;
export const TOTAL = 56;

export const clamp = (v, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
export const lerp = (a, b, p) => a + (b - a) * clamp(p);

export function smoothstep(x, a, b) {
  const p = clamp((x - a) / (b - a));
  return p * p * (3 - 2 * p);
}

export const easeOutCubic = (p) => 1 - Math.pow(1 - clamp(p), 3);
export const easeInCubic = (p) => Math.pow(clamp(p), 3);
export const easeInOutCubic = (p) => {
  p = clamp(p);
  return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
};
export const easeOutExpo = (p) => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp(p)));
export const easeOutQuint = (p) => 1 - Math.pow(1 - clamp(p), 5);

export function setOpacity(el, value) {
  el.style.opacity = clamp(value).toFixed(4);
}

export function reveal(el, t, start, duration = 0.5, opts = {}) {
  const { y = 18, blur = 0, clip = false, scale = 1, origin = "50% 50%" } = opts;
  const p = easeOutCubic((t - start) / duration);
  el.style.opacity = p.toFixed(4);
  el.style.transformOrigin = origin;
  el.style.transform = `translate3d(0, ${(1 - p) * y}px, 0) scale(${1 + (1 - p) * (scale - 1)})`;
  if (blur > 0) el.style.filter = `blur(${((1 - p) * blur).toFixed(2)}px)`;
  if (clip) {
    el.style.clipPath = `inset(0 0 ${(1 - p) * 100}% 0)`;
    el.style.webkitClipPath = `inset(0 0 ${(1 - p) * 100}% 0)`;
  }
  return p;
}

export function revealX(el, t, start, duration = 0.5, x = 24) {
  const p = easeOutCubic((t - start) / duration);
  el.style.opacity = p.toFixed(4);
  el.style.transform = `translate3d(${(1 - p) * x}px, 0, 0)`;
  return p;
}

export function typeText(el, t, start, cps = 26, text = null) {
  const str = text ?? el.dataset.text ?? "";
  const count = Math.floor(clamp((t - start) * cps, 0, str.length));
  const value = str.slice(0, count);
  if (el.textContent !== value) el.textContent = value;
  return count >= str.length;
}

export function countUp(t, start, duration, max) {
  return Math.round(max * easeOutCubic((t - start) / duration));
}

export function setText(el, value) {
  const v = String(value);
  if (el.textContent !== v) el.textContent = v;
}

export function setWidth(el, p) {
  el.style.width = `${(clamp(p) * 100).toFixed(2)}%`;
}

export function setScaleX(el, p) {
  el.style.transform = `scaleX(${clamp(p).toFixed(4)})`;
}

export function blink(t, rate = 2.0) {
  return Math.sin(t * Math.PI * 2 * rate) > 0 ? 1 : 0;
}

export function draw(el, p) {
  const len = Number(el.dataset.len || el.getTotalLength?.() || 0);
  if (!len) return;
  el.style.strokeDashoffset = String((1 - clamp(p)) * len);
}

export function chrome(start, t) {
  const bar = document.getElementById("progress");
  if (bar) bar.style.width = `${(((start + t) / TOTAL) * 100).toFixed(3)}%`;
}

export function pageReady() {
  return document.fonts.ready.then(() =>
    Promise.all(
      Array.from(document.images).map((img) =>
        img.complete
          ? Promise.resolve()
          : new Promise((resolve) => {
              img.onload = resolve;
              img.onerror = resolve;
            })
      )
    )
  );
}

/* A fixed, seeded point field. Positions never depend on t. */
export function seededPoints(count, seed = 7) {
  let s = seed >>> 0;
  const rand = () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let x = s;
    x = Math.imul(x ^ (x >>> 15), x | 1);
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
  return Array.from({ length: count }, () => ({ x: rand(), y: rand(), s: rand() }));
}
