"""One-time helper: fill locale/uk/django.po with Ukrainian by inverting the
old locale/en/django.po (uk msgid -> en msgstr). Run inside the web container
after `makemessages -l uk`. Requires polib (dev-only): pip install polib."""
import polib

OLD_EN = "locale/en/LC_MESSAGES/django.po"
NEW_UK = "locale/uk/LC_MESSAGES/django.po"

# 9 strings that had no English in old en.po: English (new msgid) -> Ukrainian.
GAP = {
    "Site type. Used by the apply_preset command to fill defaults.":
        "Тип сайту. Використовується командою apply_preset для заповнення дефолтів.",
    'Show prices, "Add to cart" buttons and the cart page. Enabled by the "Shop" preset. Orders arrive in the "Orders" section.':
        "Показувати ціни, кнопки «У кошик» і сторінку кошика. Вмикається пресетом «Магазин». Замовлення надходять у розділ «Замовлення».",
    'Small text above the large heading (e.g., "Official distributor · 2026").':
        "Малий текст над великим заголовком (напр., \"Офіційний дистриб'ютор · 2026\").",
    "Replaces the default. For the kinetic effect, emphasize a word with **word**.":
        "Замінює дефолтний. Для kinetic-ефекту можна підкреслити слово через **слово**.",
    "View Transitions API. Works in Chrome/Edge/Safari; no animation in Firefox.":
        "View Transitions API. Працює в Chrome/Edge/Safari; у Firefox без анімації.",
    "Strong effect; not for every brand. Disabled automatically on touch devices.":
        "Сильний ефект; не для всіх брендів. Вимикається на тач-пристроях автоматично.",
    "One click renames the whole site to the chosen vertical (theme, menu labels, terms, hero, vacancy sections).":
        "Один клік — і весь сайт перейменовується під обрану вертикаль (тема, лейбли меню, терміни, hero, секції вакансій).",
    "The preset rewrites menu labels, terms, hero and theme. The site name, logo and content (products/news) stay.":
        "Пресет переписує лейбли меню, терміни, hero і тему. Назва сайту, лого та контент (товари/новини) залишаться.",
    "A catalog that delivers the product without noise. A contact request in two clicks.":
        "Каталог, який доносить продукт без зайвого шуму. Запит на зв'язок — у два кліки.",
}

# Ukrainian plural forms (3) for the one plural entry.
PLURAL_UK = ("%(counter)s оголошення", "%(counter)s оголошення", "%(counter)s оголошень")

old = polib.pofile(OLD_EN)
eng_to_ukr = {}
for e in old:
    if e.obsolete or not e.msgid:
        continue
    if e.msgstr:
        eng_to_ukr[e.msgstr] = e.msgid

uk = polib.pofile(NEW_UK)
filled = missing = 0
for e in uk:
    if e.msgid_plural:
        e.msgstr_plural = {0: PLURAL_UK[0], 1: PLURAL_UK[1], 2: PLURAL_UK[2]}
        filled += 1
        continue
    val = eng_to_ukr.get(e.msgid) or GAP.get(e.msgid)
    if val:
        e.msgstr = val
        filled += 1
    elif e.msgid:
        missing += 1
        print("MISSING:", repr(e.msgid))
uk.save(NEW_UK)
print(f"filled={filled} missing={missing}")
