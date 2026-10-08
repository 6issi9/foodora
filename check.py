import sys
import re
import requests
from playwright.sync_api import sync_playwright

URL = "https://www.foodora.at/subscription"
CODE = "ВАШ_КОД"
TOKEN = "ВАШ_ТОКЕН"
CHAT_ID = "ВАШ_CHAT_ID"

def tg(text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": text}, timeout=30)

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 430, "height": 900})
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # 1. Закрываем баннер куки
        try:
            page.locator("#cookie-comply, .cookie-comply, button:has-text('Accept'), button:has-text('Akzeptieren'), button:has-text('Allow')").first.click(timeout=3000)
        except Exception:
            pass

        # 2. Переходим к форме ввода кода (если поля еще нет на экране)
        if page.locator("input[placeholder*='Gutschein'], input[placeholder*='Voucher'], input[placeholder*='Code']").count() == 0:
            # Кликаем по первой подходящей кнопке или ссылке на стартовой странице
            start_btn = page.locator("button:visible, a:visible").first
            if start_btn.count() > 0:
                start_btn.click(force=True)
                page.wait_for_timeout(3000)

        # 3. Находим поле ввода кода (Gutscheincode)
        inp = page.locator("input[placeholder*='Gutschein'], input[placeholder*='Voucher'], input[placeholder*='Code'], input[placeholder*='code'], input[type='text']").first
        inp.fill(CODE)

        # 4. Нажимаем кнопку применения (Anwenden / Apply)
        btn_apply = page.locator("button:has-text('Anwenden'), button:has-text('Apply'), button:has-text('Submit')").first
        if btn_apply.count() > 0:
            btn_apply.click(force=True)
        else:
            inp.press("Enter")

        # 5. Ожидаем появления информации о тарифах
        page.wait_for_timeout(4000)
        text = page.inner_text("body")

    except Exception as e:
        page.screenshot(path="debug.png", full_page=True)
        b.close()
        print("ERROR:", e)
        sys.exit(1)

    b.close()

# Проверка наличия тарифов
plans = len(re.findall(r"Monatliches Abo|Monthly subscription|Abo", text, re.IGNORECASE))
soon = len(re.findall(r"Benachrichtige mich|Notify me|Out of stock|скоро", text, re.IGNORECASE))
print(f"тарифов: {plans}, 'скоро в наличии': {soon}")

if plans > 0 and soon < plans:
    tg(f"🔔 Что-то появилось в наличии! ({plans - soon} из {plans})\n{URL}\nКод: {CODE}")
