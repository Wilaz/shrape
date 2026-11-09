from pydantic import HttpUrl
from shrape.classes import Thread
from typing import Any
from patchright.sync_api import sync_playwright
from shrape.classes import Token
from pathlib import Path
from pickledb import PickleDB
from rich.table import Table
from rich import print

STORAGE = Path("./storage.json")


def get_thread_by_url(url: HttpUrl, thread_list: list[Thread]) -> Thread | None:
    for thread in thread_list:
        if thread.url == url:
            return thread
    return None


def generate_token(url: HttpUrl) -> Token:
    browser_path: str = None
    with PickleDB(STORAGE) as db:
        browser_path = db.get("browser_path")
        if browser_path is None:
            browser_path = str(input("Enter the path to Chromium: "))
            db.set("browser_path", browser_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=browser_path,
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


def print_info(
    site: str,
    id: str,
    board: str,
    new_files: int,
    new_dupes: int,
    old_dupes: int,
    existing: int,
    errors: int = 0,
) -> None:
    table = Table(title=f"{board}#{id} ({site})", show_header=False, box=None, width=48)
    table.add_column("Label")
    table.add_column("Value", justify="right")
    table.add_row("New files:", f"{new_files} ({new_dupes} duplicates)")
    table.add_row("Existing files:", f"{existing} ({old_dupes} duplicates)")

    if errors != 0:
        table.add_row("Errors:", str(errors))

    print(table)
