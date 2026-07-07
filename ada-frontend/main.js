import "./assets/css/tailus.css";
import Swiper from "swiper/bundle";
import { Pagination, Navigation, Thumbs } from "swiper/modules";
import "swiper/css/bundle";
import "swiper/css/pagination";
import "swiper/css/effect-cards";
import PhotoSwipeLightbox from "photoswipe/lightbox";
import "photoswipe/style.css";
import { initAnimations } from "./src/animations.js";
import { initAutocomplete } from "./src/autocomplete.js";
import { initBackgrounds } from "./src/backgrounds.js";
import { initCart } from "./src/cart.js";

initAnimations();
initAutocomplete();
initBackgrounds();
initCart();

const mainHeader = document.querySelector("#header");
const menuBtn = document.querySelector("#menu-btn");

if (mainHeader && menuBtn) {
  menuBtn.addEventListener("click", () => {
    mainHeader.dataset.state = mainHeader.dataset.state === "active" ? "" : "active";
  });
}

function openContactModal(subject) {
  const modal = document.getElementById("contactModal");
  if (!modal) return;
  const subjectInput = modal.querySelector("#modal-subject");
  if (subjectInput) subjectInput.value = subject || "general";
  modal.classList.remove("hidden");
  modal.classList.add("flex");
  document.body.style.overflow = "hidden";
  const firstInput = modal.querySelector("input:not([type=hidden]), textarea");
  if (firstInput) firstInput.focus();
}

function closeContactModal() {
  const modal = document.getElementById("contactModal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.classList.remove("flex");
  document.body.style.overflow = "";
}

window.openContactModal = openContactModal;
window.closeContactModal = closeContactModal;

const contactModal = document.getElementById("contactModal");
if (contactModal) {
  contactModal.addEventListener("click", (event) => {
    if (event.target === contactModal) closeContactModal();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !contactModal.classList.contains("hidden")) {
      closeContactModal();
    }
  });
}

if (document.querySelector(".productGallery")) {
  const thumb = document.querySelector(".productThumb")
    ? new Swiper(".productThumb", {
        slidesPerView: 4,
        spaceBetween: 8,
        freeMode: true,
        watchSlidesProgress: true,
      })
    : null;
  new Swiper(".productGallery", {
    modules: [Navigation, Pagination, Thumbs],
    thumbs: thumb ? { swiper: thumb } : undefined,
    navigation: {
      nextEl: ".productGallery-next",
      prevEl: ".productGallery-prev",
    },
    pagination: {
      el: ".productGallery-pagination",
      type: "fraction",
    },
    loop: false,
    keyboard: { enabled: true },
  });

  const lightbox = new PhotoSwipeLightbox({
    gallery: ".productGallery",
    children: "a.pswp-link",
    pswpModule: () => import("photoswipe"),
    showHideAnimationType: "fade",
    bgOpacity: 0.92,
    // Закриття по тапу/кліку будь-де (важливо для мобільних) + свайп вниз.
    tapAction: "close",
    imageClickAction: "close",
    bgClickAction: "close",
    closeOnVerticalDrag: true,
  });
  lightbox.init();
}

const brandsSliderEl = document.querySelector(".brandsSlider");
if (brandsSliderEl) {
  // Loop needs more slides than the widest slidesPerView, otherwise Swiper
  // warns and disables it — fall back to a static (non-looping) slider.
  const slideCount = brandsSliderEl.querySelectorAll(".swiper-slide").length;
  const enableLoop = slideCount > 6;
  new Swiper(".brandsSlider", {
    slidesPerView: 2,
    spaceBetween: 16,
    loop: enableLoop,
    grabCursor: true,
    autoplay: enableLoop
      ? { delay: 2200, disableOnInteraction: false, pauseOnMouseEnter: true }
      : false,
    breakpoints: {
      480: { slidesPerView: 3 },
      768: { slidesPerView: 4 },
      1024: { slidesPerView: 5 },
      1280: { slidesPerView: 6 },
    },
  });
}
