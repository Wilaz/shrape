from typing import Any
import os
from patchright.sync_api import sync_playwright
from pydantic import HttpUrl
from classes import Token


def generate_token(url: HttpUrl) -> Token:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=str(input("Enter the path to Chromium: ")),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--ignore-gpu-blocklist=false",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        page = context.new_page()
        page.goto(str(url))
        page.wait_for_timeout(10000)
        playwright_cookies = context.cookies()
        headers: dict[str, Any] = {"User-Agent": page.evaluate("navigator.userAgent")}
        cookies = {cookie["name"]: cookie["value"] for cookie in playwright_cookies}
        browser.close()

    return Token(cookies, headers)
