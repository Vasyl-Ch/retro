/**
 * Автокомпліт для полів пошуку (марка авто, місто).
 *
 * Розмітка:
 *   <input data-autocomplete="/url/" data-autocomplete-hidden="#brand-slug">
 *   <input type="hidden" id="brand-slug" name="brand">
 *
 * Бекенд повертає { "results": [{ "name": "...", "value": "..." }] }.
 * При виборі: видимий інпут отримує name; якщо вказано data-autocomplete-hidden —
 * прихований інпут отримує value (slug). Без прихованого поля у видимий пишеться value
 * (для міста name === value), тобто можна й частково ввести текст вручну.
 */

const DEBOUNCE_MS = 200;
const MIN_CHARS = 1;

class Autocomplete {
  constructor(input) {
    this.input = input;
    this.url = input.dataset.autocomplete;
    this.hidden = input.dataset.autocompleteHidden
      ? document.querySelector(input.dataset.autocompleteHidden)
      : null;
    this.items = [];
    this.activeIndex = -1;
    this.timer = null;

    this.list = document.createElement("ul");
    this.list.className =
      "absolute z-30 left-0 right-0 mt-1 max-h-60 overflow-auto rounded-xl " +
      "bg-ui text-body shadow-lg border border-[color:var(--ui-border-color)] " +
      "py-1 hidden";
    // Поле обгорнуте контейнером .relative у шаблоні.
    this.input.insertAdjacentElement("afterend", this.list);

    this.input.setAttribute("autocomplete", "off");
    this.input.addEventListener("input", () => this.onInput());
    this.input.addEventListener("keydown", (e) => this.onKeydown(e));
    this.input.addEventListener("focus", () => {
      if (this.items.length) this.open();
    });
    document.addEventListener("click", (e) => {
      if (!this.list.contains(e.target) && e.target !== this.input) this.close();
    });
  }

  onInput() {
    // Користувач почав редагувати → раніше обраний slug більше не валідний.
    if (this.hidden) this.hidden.value = "";
    const query = this.input.value.trim();
    clearTimeout(this.timer);
    if (query.length < MIN_CHARS) {
      this.close();
      return;
    }
    this.timer = setTimeout(() => this.fetch(query), DEBOUNCE_MS);
  }

  async fetch(query) {
    try {
      const res = await fetch(`${this.url}?q=${encodeURIComponent(query)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!res.ok) return;
      const data = await res.json();
      this.items = Array.isArray(data.results) ? data.results : [];
      this.render();
    } catch {
      this.close();
    }
  }

  render() {
    this.list.innerHTML = "";
    this.activeIndex = -1;
    if (!this.items.length) {
      this.close();
      return;
    }
    this.items.forEach((item, index) => {
      const li = document.createElement("li");
      li.textContent = item.name;
      li.className =
        "px-3 py-2 text-sm text-body cursor-pointer hover:bg-primary-500/15";
      li.addEventListener("mousedown", (e) => {
        e.preventDefault();
        this.select(index);
      });
      this.list.appendChild(li);
    });
    this.open();
  }

  select(index) {
    const item = this.items[index];
    if (!item) return;
    this.input.value = item.name;
    if (this.hidden) this.hidden.value = item.value;
    else this.input.value = item.value;
    this.close();
  }

  highlight(next) {
    const lis = this.list.querySelectorAll("li");
    if (!lis.length) return;
    this.activeIndex = (this.activeIndex + next + lis.length) % lis.length;
    lis.forEach((li, i) => {
      li.classList.toggle("bg-primary-500/15", i === this.activeIndex);
    });
  }

  onKeydown(e) {
    if (this.list.classList.contains("hidden")) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      this.highlight(1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      this.highlight(-1);
    } else if (e.key === "Enter" && this.activeIndex >= 0) {
      e.preventDefault();
      this.select(this.activeIndex);
    } else if (e.key === "Escape") {
      this.close();
    }
  }

  open() {
    this.list.classList.remove("hidden");
  }

  close() {
    this.list.classList.add("hidden");
  }
}

export function initAutocomplete() {
  document
    .querySelectorAll("[data-autocomplete]")
    .forEach((input) => new Autocomplete(input));
}
