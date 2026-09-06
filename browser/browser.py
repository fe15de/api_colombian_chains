from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def get_auth_header(url : str, url_substring: str, settle_ms: int = 10_000, nav_timeout_ms : int = 60_000) -> str | None:
    from playwright.sync_api import sync_playwright

    captured: dict[str, str] = {}

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        def on_request(request):
            auth = request.headers.get('authorization')
            if auth and url_substring in request.url:
                captured.setdefault('token', auth)

        page.on('request', on_request)
        page.goto(url, wait_until='domcontentloaded', timeout= nav_timeout_ms)
        page.wait_for_timeout(settle_ms)
        browser.close()

    return captured.get('token')
