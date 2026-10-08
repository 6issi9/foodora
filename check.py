import os, sys, re, requests
from playwright.sync_api import sync_playwright

URL = "https://checkout.cycle.eco/registration?storeId=e4921b6a-a8b5-4e37-92eb-c438188e293a"
CODE = os.environ["ACCESS_CODE"]
TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT_ID"]

def tg(text):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": text}, timeout=30)

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 430, "height": 900})
    try:
        page.goto(URL, wait_until="networkidle", timeout=60000)
        inp = page.locator("input[type='text']:visible, input[type='password']:visible, input:not([type='radio']):visible").first
        inp.fill(CODE)
        inp.press("Enter")
        page.wait_for_timeout(1500)
            # Закрываем баннер куки, если он появился
    try:
        page.locator("#cookie-comply, .cookie-comply, button:has-text('Accept'), button:has-text('Akzeptieren')").first.click(timeout=3000)
    except Exception:
        pass
 # если Enter не сработал, жмём кнопку
    if page.locator("text=Monatliches Abo").count() == 0:
        btn = page.locator("button:visible").first
        if btn.count():
            btn.click(force=True)
        page.wait_for_selector("text=Monatliches Abo", timeout=30000)
        page.wait_for_timeout(2000)
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
    tg(f"🚲 Что-то появилось в наличии! ({plans - soon} из {plans})\n{URL}\nКод: {CODE}")
