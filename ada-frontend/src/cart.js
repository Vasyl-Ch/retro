/**
 * Кошик (режим магазину): додавання/зміна/видалення через AJAX + лічильник у навбарі.
 *
 * Використовує делегування подій на document (стійке до page-transitions / підміни DOM).
 * Розмітка:
 *   кнопка   <button data-add-to-cart="<id>">
 *   рядок    <div data-cart-row data-product-id="<id>"> … <span data-cart-subtotal> …
 *   к-сть    <input data-cart-qty data-product-id="<id>">
 *   видалити <button data-cart-remove data-product-id="<id>">
 *   бейдж    <span data-cart-count>   сума <span data-cart-total>
 */

const CART_BASE = "/cart";

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[2]) : null;
}

async function postCart(action, productId, body = {}) {
  const params = new URLSearchParams(body);
  const res = await fetch(`${CART_BASE}/${action}/${productId}/`, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCookie("csrftoken") || "",
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: params.toString(),
  });
  if (!res.ok) throw new Error(`cart ${action} failed: ${res.status}`);
  return res.json();
}

function updateBadge(count) {
  document.querySelectorAll("[data-cart-count]").forEach((el) => {
    el.textContent = count;
    el.classList.toggle("hidden", !count);
  });
}

function flashAdded(button) {
  const label = button.querySelector(".btn-label") || button;
  const original = label.textContent;
  label.textContent = "✓";
  button.disabled = true;
  setTimeout(() => {
    label.textContent = original;
    button.disabled = false;
  }, 1000);
}

async function onAdd(button) {
  const id = button.dataset.addToCart;
  try {
    const data = await postCart("add", id);
    updateBadge(data.count);
    flashAdded(button);
  } catch (e) {
    console.error(e);
  }
}

async function onRemove(button) {
  const id = button.dataset.productId;
  const data = await postCart("remove", id);
  updateBadge(data.count);
  const row = document.querySelector(`[data-cart-row][data-product-id="${id}"]`);
  if (row) row.remove();
  setCartTotal(data);
  if (!data.count) window.location.reload(); // показати порожній стан
}

async function onQtyChange(input) {
  const id = input.dataset.productId;
  const qty = Math.max(1, parseInt(input.value, 10) || 1);
  input.value = qty;
  const data = await postCart("update", id, { quantity: qty });
  updateBadge(data.count);
  setCartTotal(data);
  const row = document.querySelector(`[data-cart-row][data-product-id="${id}"]`);
  if (row && data.item_subtotal != null) {
    const sub = row.querySelector("[data-cart-subtotal]");
    if (sub) sub.textContent = `${data.item_subtotal} ${data.currency}`;
  }
}

function setCartTotal(data) {
  const total = document.querySelector("[data-cart-total]");
  if (total && data.total != null) total.textContent = data.total;
}

export function initCart() {
  document.addEventListener("click", (e) => {
    const addBtn = e.target.closest("[data-add-to-cart]");
    if (addBtn) {
      e.preventDefault();
      onAdd(addBtn);
      return;
    }
    const removeBtn = e.target.closest("[data-cart-remove]");
    if (removeBtn) {
      e.preventDefault();
      onRemove(removeBtn);
    }
  });

  document.addEventListener("change", (e) => {
    const qtyInput = e.target.closest("[data-cart-qty]");
    if (qtyInput) onQtyChange(qtyInput);
  });
}
