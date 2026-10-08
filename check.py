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
    page = b.new_page(viewport={"width": 1280, "height": 800})
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)

        # Пробуем кликнуть по куки
        for selector in ["#cookie-comply", ".cookie-comply", "button:has-text('Accept')", "button:has-text('Akzeptieren')"]:
            if page.locator(selector).count() > 0:
                try:
                    page.locator(selector).first.click(timeout=2000)
                except Exception:
                    pass

        # Делаем скриншот, чтобы точно увидеть, что на экране
        page.screenshot(path="debug.png", full_page=True)

        # Ждем только видимые поля
        inp = page.locator("input:visible").first
        inp.fill(CODE, timeout=5000)
        inp.press("Enter")
        page.wait_for_timeout(2000)

        if page.locator("text=Monatliches Abo").count() == 0:
            btn = page.locator("button:visible").first
            if btn.count():
                btn.click(force=True)

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
