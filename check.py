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
        # Загружаем страницу
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # Закрываем баннер куки, если он есть
        try:
            page.locator("#cookie-comply, .cookie-comply, button:has-text('Accept'), button:has-text('Akzeptieren')").first.click(timeout=3000)
        except Exception:
            pass

        # Находим поле для ввода кода
        inp = page.locator("input[type='text']:visible, input[type='password']:visible, input:not([type='radio']):visible").first
        inp.fill(CODE)
        inp.press("Enter")
        page.wait_for_timeout(2000)

        # Если Enter не сработал, кликаем по кнопке с силой
        if page.locator("text=Monatliches Abo").count() == 0:
            btn = page.locator("button:visible").first
            if btn.count():
                btn.click(force=True)

        # Ждем появления результатов не более 10 секунд
        page.wait_for_selector("text=Monatliches Abo", timeout=10000)
        text = page.inner_text("body")

    except Exception as e:
        page.screenshot(path="debug.png", full_page=True)
        b.close()
        print("ERROR:", e)
        sys.exit(1)

    b.close()

plans = len(re.findall(r"Monatliches Abo", text))
soon = len(re.findall(r"Benachrichtige mich", text))
print(f"тарифов: {plans}, 'скоро в наличии': {soon}")

if plans > 0 and soon < plans:
    tg(f"🔔 Что-то появилось в наличии! ({plans - soon} из {plans})\n{URL}\nКод: {CODE}")
