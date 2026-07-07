/**
 * Animated page backgrounds (admin constructor, PageBackground.kind).
 *
 * CSS kinds (gradient / aurora / waves) animate purely in tailus.css; this
 * module boots the particle kinds (particles / bubbles / snow / stars /
 * custom JSON config) and exposes `window.__adaBackground.apply(state)` so the
 * admin live preview can swap the background at runtime without a reload.
 * tsparticles is loaded lazily — pages without a particle background never
 * download it.
 */

const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const PARTICLE_KINDS = ["particles", "bubbles", "snow", "stars", "custom"];

let engine = null; // tsParticles once loaded
let container = null; // active particles container
let configOverride = null; // custom JSON pushed by the admin preview

function cssVar(el, name, fallback) {
  const value = getComputedStyle(el).getPropertyValue(name).trim();
  if (!value) return fallback;
  // Theme vars are "R G B" triplets; custom colours are #rrggbb(aa).
  return value.startsWith("#") ? value : `rgb(${value})`;
}

function hostColors(host) {
  const root = document.documentElement;
  return [
    cssVar(host, "--bg-c1", cssVar(root, "--primary-400", "#60a5fa")),
    cssVar(host, "--bg-c2", cssVar(root, "--primary-600", "#2563eb")),
    cssVar(host, "--bg-c3", cssVar(root, "--primary-300", "#93c5fd")),
  ];
}

const BASE_OPTIONS = {
  fullScreen: { enable: false },
  fpsLimit: 60,
  detectRetina: true,
};

/* Built-in particle presets. `speed` is a 0.1..3 factor from the admin. */
const KIND_OPTIONS = {
  particles: (colors, speed) => ({
    particles: {
      number: { value: 60, density: { enable: true } },
      color: { value: colors },
      links: { enable: true, color: colors[1], distance: 150, opacity: 0.35 },
      move: { enable: true, speed: 1.2 * speed, outModes: { default: "out" } },
      opacity: { value: { min: 0.25, max: 0.7 } },
      size: { value: { min: 1, max: 3.5 } },
    },
    interactivity: {
      detectsOn: "window",
      events: { onHover: { enable: true, mode: "grab" } },
      modes: { grab: { distance: 160, links: { opacity: 0.5 } } },
    },
  }),
  bubbles: (colors, speed) => ({
    particles: {
      number: { value: 30, density: { enable: true } },
      color: { value: colors },
      move: {
        enable: true,
        direction: "top",
        speed: 1.5 * speed,
        outModes: { default: "out", top: "out", bottom: "out" },
      },
      opacity: { value: { min: 0.15, max: 0.45 } },
      size: { value: { min: 6, max: 22 } },
    },
  }),
  snow: (colors, speed) => ({
    particles: {
      number: { value: 90, density: { enable: true } },
      color: { value: colors },
      move: {
        enable: true,
        direction: "bottom",
        speed: 1.4 * speed,
        straight: false,
        outModes: { default: "out", bottom: "out" },
      },
      opacity: { value: { min: 0.35, max: 0.85 } },
      size: { value: { min: 1, max: 4 } },
    },
  }),
  stars: (colors, speed) => ({
    particles: {
      number: { value: 120, density: { enable: true } },
      color: { value: colors },
      move: { enable: true, speed: 0.15 * speed, outModes: { default: "out" } },
      opacity: {
        value: { min: 0.1, max: 0.9 },
        animation: { enable: true, speed: 0.9 * speed, sync: false },
      },
      size: { value: { min: 0.5, max: 2.5 } },
    },
  }),
};

function readCustomConfig() {
  if (configOverride) return configOverride;
  const script = document.getElementById("bg-custom-config");
  if (!script) return null;
  try {
    // json_script stores the config as a JSON-encoded string → parse twice.
    return JSON.parse(JSON.parse(script.textContent));
  } catch (e) {
    console.warn("Custom background config is not valid JSON", e);
    return null;
  }
}

function buildOptions(host) {
  const kind = host.dataset.bgKind || "particles";
  if (kind === "custom") {
    const custom = readCustomConfig();
    return custom ? { ...BASE_OPTIONS, ...custom } : null;
  }
  const speed =
    Math.max(10, Math.min(300, parseInt(host.dataset.speed, 10) || 100)) / 100;
  const build = KIND_OPTIONS[kind] || KIND_OPTIONS.particles;
  return { ...BASE_OPTIONS, ...build(hostColors(host), speed) };
}

async function mount(host) {
  if (REDUCED) return;
  if (!engine) {
    const [{ tsParticles }, { loadSlim }] = await Promise.all([
      import("@tsparticles/engine"),
      import("@tsparticles/slim"),
    ]);
    await loadSlim(tsParticles);
    engine = tsParticles;
  }
  if (container) {
    container.destroy();
    container = null;
  }
  host.innerHTML = "";
  const options = buildOptions(host);
  if (!options) return;
  container = await engine.load({ element: host, options });
}

/**
 * Admin live preview: replace the background with `state`
 * { kind, colors: [c1,c2,c3], speed, dim, config } — kind ""/"none"/"image"
 * removes the animated layer entirely.
 */
function apply(state) {
  let host = document.getElementById("animated-bg");
  const kind = state && state.kind;
  if (container) {
    container.destroy();
    container = null;
  }
  if (!kind || kind === "image" || kind === "none") {
    if (host) host.remove();
    return;
  }
  if (!host) {
    host = document.createElement("div");
    host.id = "animated-bg";
    host.setAttribute("aria-hidden", "true");
    document.body.prepend(host);
  }
  host.innerHTML = "";
  host.className = `anim-bg anim-bg-${kind}`;
  host.dataset.bgKind = kind;
  host.dataset.speed = state.speed || 100;
  const isParticles = PARTICLE_KINDS.includes(kind);
  if (isParticles) host.setAttribute("data-particles", "");
  else host.removeAttribute("data-particles");
  const colors = state.colors || [];
  host.style.cssText =
    `--bg-speed-factor: calc(100 / ${state.speed || 100});` +
    `--bg-dim: ${state.dim == null ? 40 : state.dim};` +
    colors.map((c, i) => (c ? `--bg-c${i + 1}: ${c};` : "")).join("");
  configOverride = state.config || null;
  if (isParticles) mount(host);
}

export function initBackgrounds() {
  window.__adaBackground = { apply };
  const host = document.querySelector("#animated-bg[data-particles]");
  if (host) mount(host);
}
