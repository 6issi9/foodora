import sys
import re
import requests
from playwright.sync_api import sync_playwright

URL = "https://checkout.cycle.eco"
CODE = "ВАШ_ПРОМОКОД"  # Вставьте ваш код активации
TOKEN = "8776708258:AAGISUWyK9ClzaahcjVVpENMVxqcjKI6m70"
CHAT_ID = "1068573784"

def tg(text):
    res = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
        data={"chat_id": CHAT_ID, "text": text}, 
        timeout=30
    )
    print(f"Telegram status: {res.status_code}")

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 430, "height": 900})
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # 1. Принимаем куки
        try:
            page.locator("button:has-text('Accept'), button:has-text('Akzeptieren'), #cookie-comply").first.click(timeout=3000)
        except Exception:
            pass

        # 2. Выбор параметров на Шаге 1 (если есть селекты)
        selects = page.locator("select")
        if selects.count() > 0:
            for i in range(selects.count()):
                try:
                    selects.nth(i).select_option(index=1)
                except Exception:
                    pass
            page.wait_for_timeout(1000)

        # Нажимаем "Далее"
        next_btn = page.locator("button:has-text('Weiter'), button:has-text('Next'), button:has-text('Continue')").first
        if next_btn.count() > 0 and next_btn.is_visible():
            next_btn.click(force=True)
            page.wait_for_timeout(2000)

        # 3. Шаг 2: Ввод кода активации
        inp = page.locator("input[placeholder*='Gutschein'], input[placeholder*='Voucher'], input[placeholder*='Code'], input:visible").first
        inp.fill(CODE)

        btn_apply = page.locator("button:has-text('Anwenden'), button:has-text('Apply'), button[type='submit']").first
        if btn_apply.count() > 0 and btn_apply.is_visible():
            btn_apply.click(force=True)
        else:
            inp.press("Enter")

        # 4. Шаг 3: Чтение тарифов
        page.wait_for_timeout(5000)
        text = page.inner_text("body")

    except Exception as e:
        page.screenshot(path="debug.png", full_page=True)
        b.close()
        print("ERROR:", e)
        sys.exit(1)

    b.close()

# Подсчёт вариантов
plans = len(re.findall(r"Monatliches Abo|Monthly subscription|Abo", text, re.IGNORECASE))
soon = len(re.findall(r"Benachrichtige mich|Notify me|Out of stock|скоро", text, re.IGNORECASE))
available = plans - soon

print(f"Всего тарифов: {plans}, занято: {soon}, свободно: {available}")

# Отправка сообщений в Telegram при каждом запуске
if plans > 0 and soon < plans:
    tg(f"🔔 СРОЧНО! Появился велосипед! ({available} из {plans})\n{URL}\nКод: {CODE}")
else:
    tg(f"✅ Проверка выполнена.\nТарифов найдено: {plans}\nИз них недоступно: {soon}\nСвободных велосипедов нет.")
