/**
 * Editorial animation layer.
 * All effects are opt-in via <body data-anim-...="1"> flags read from SiteSettings.
 * Everything self-disables under `prefers-reduced-motion: reduce` and on touch devices
 * where appropriate (cursor follower, magnetic buttons).
 */

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const TOUCH = window.matchMedia("(hover: none), (pointer: coarse)").matches;
const body = document.body;
const flag = (name) => body.dataset[name] === "1";

/* ----------------------------------------------------------------
 *  1. Scroll-triggered fade-up + stagger
 *     Any element with [data-reveal] fades in.
 *     A parent with [data-reveal-stagger] staggers its direct children.
 * ---------------------------------------------------------------- */
function initScrollReveal() {
  if (REDUCED || !flag("animScrollReveal")) return;

  const allHidden = [];

  document.querySelectorAll("[data-reveal-stagger]").forEach((group) => {
    const items = group.querySelectorAll(":scope > *");
    if (!items.length) return;
    gsap.set(items, { opacity: 0, y: 32 });
    items.forEach((it) => allHidden.push(it));
    ScrollTrigger.batch(items, {
      start: "top 92%",
      onEnter: (els) =>
        gsap.to(els, {
          opacity: 1, y: 0, duration: 0.9, ease: "power3.out",
          stagger: 0.1, overwrite: true,
        }),
    });
  });

  document.querySelectorAll("[data-reveal]:not([data-reveal-stagger] > *)").forEach((el) => {
    gsap.set(el, { opacity: 0, y: 36 });
    allHidden.push(el);
    ScrollTrigger.create({
      trigger: el, start: "top 92%", once: true,
      onEnter: () => gsap.to(el, { opacity: 1, y: 0, duration: 0.9, ease: "power3.out" }),
    });
  });

  // Force a layout refresh after images/fonts load (heights change → triggers shift).
  window.addEventListener("load", () => ScrollTrigger.refresh());

  // Failsafe: if anything is still invisible 2.5s after init, force it visible.
  setTimeout(() => {
    allHidden.forEach((el) => {
      if (parseFloat(getComputedStyle(el).opacity) < 0.05) {
        gsap.to(el, { opacity: 1, y: 0, duration: 0.6, ease: "power2.out", overwrite: true });
      }
    });
  }, 2500);
}

/* ----------------------------------------------------------------
 *  2. Kinetic hero typography
 *     Element with [data-kinetic-text]: each word animates in;
 *     words wrapped in **double asterisks** get a soft underline accent.
 * ---------------------------------------------------------------- */
function initKineticHero() {
  if (!flag("animKineticHero")) return;
  const targets = document.querySelectorAll("[data-kinetic-text]");
  if (!targets.length) return;

  targets.forEach((target) => {
    const raw = target.dataset.kineticText || target.textContent || "";
    target.textContent = "";
    const words = raw.split(/\s+/).filter(Boolean);
    const wordEls = words.map((w) => {
      const span = document.createElement("span");
      span.className = "kinetic-word";
      if (w.startsWith("**") && w.endsWith("**")) {
        span.classList.add("kinetic-accent");
        span.textContent = w.slice(2, -2);
      } else {
        span.textContent = w;
      }
      target.appendChild(span);
      target.appendChild(document.createTextNode(" "));
      return span;
    });
    if (REDUCED) {
      gsap.set(wordEls, { opacity: 1, y: 0 });
      return;
    }
    gsap.set(wordEls, { opacity: 0, y: "0.6em", rotateX: -55, transformOrigin: "50% 100%" });
    gsap.to(wordEls, {
      opacity: 1,
      y: 0,
      rotateX: 0,
      duration: 1.1,
      ease: "power3.out",
      stagger: 0.12,
      delay: 0.2,
    });
  });
}

/* ----------------------------------------------------------------
 *  3. Magnetic buttons — pulls towards the cursor while hovering.
 * ---------------------------------------------------------------- */
function initMagneticButtons() {
  if (REDUCED || TOUCH || !flag("animMagnetic")) return;
  const STRENGTH = 0.4;
  document.querySelectorAll("[data-magnetic], .btn.variant-primary").forEach((btn) => {
    let rect = null;
    const onEnter = () => {
      rect = btn.getBoundingClientRect();
      gsap.to(btn, { scale: 1.05, duration: 0.3, ease: "power3.out" });
    };
    const onMove = (e) => {
      if (!rect) return;
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      gsap.to(btn, { x: x * STRENGTH, y: y * STRENGTH, duration: 0.35, ease: "power3.out" });
    };
    const onLeave = () => {
      rect = null;
      gsap.to(btn, { x: 0, y: 0, scale: 1, duration: 0.7, ease: "elastic.out(1, 0.4)" });
    };
    btn.addEventListener("mouseenter", onEnter);
    btn.addEventListener("mousemove", onMove);
    btn.addEventListener("mouseleave", onLeave);
  });
}

/* ----------------------------------------------------------------
 *  4. Cursor follower — small inner dot + larger trailing ring.
 *     Ring grows over interactive elements.
 * ---------------------------------------------------------------- */
function initCursorFollower() {
  if (REDUCED || TOUCH || !flag("animCursor")) return;

  const dot = document.createElement("div");
  dot.className = "cursor-dot";
  const ring = document.createElement("div");
  ring.className = "cursor-ring";
  document.body.append(dot, ring);

  let mx = window.innerWidth / 2;
  let my = window.innerHeight / 2;
  let rx = mx;
  let ry = my;

  window.addEventListener("mousemove", (e) => {
    mx = e.clientX;
    my = e.clientY;
    dot.style.transform = `translate3d(${mx}px, ${my}px, 0) translate(-50%, -50%)`;
  });

  const tick = () => {
    rx += (mx - rx) * 0.18;
    ry += (my - ry) * 0.18;
    ring.style.transform = `translate3d(${rx}px, ${ry}px, 0) translate(-50%, -50%)`;
    requestAnimationFrame(tick);
  };
  tick();

  const grow = () => ring.classList.add("is-hover");
  const shrink = () => ring.classList.remove("is-hover");
  document.querySelectorAll("a, button, [role='button'], input, textarea, select, [data-magnetic]").forEach((el) => {
    el.addEventListener("mouseenter", grow);
    el.addEventListener("mouseleave", shrink);
  });
}

/* ----------------------------------------------------------------
 *  5. View Transitions API for same-origin link navigation.
 *     Browsers without support fall back to standard navigation.
 * ---------------------------------------------------------------- */
function initPageTransitions() {
  if (REDUCED || !flag("animPageTransitions")) return;
  if (!document.startViewTransition) return;

  document.addEventListener("click", (e) => {
    const link = e.target.closest("a[href]");
    if (!link) return;
    if (link.target === "_blank") return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (e.button !== 0) return;
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin) return;
    if (url.hash && url.pathname === location.pathname) return;
    if (link.hasAttribute("data-no-transition")) return;
    if (link.getAttribute("href").startsWith("#")) return;

    e.preventDefault();
    document.startViewTransition(() => {
      window.location.href = url.href;
    });
  });
}

export function initAnimations() {
  const start = () => {
    initKineticHero();
    initScrollReveal();
    initMagneticButtons();
    initCursorFollower();
    initPageTransitions();
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  } else {
    start();
  }
}
