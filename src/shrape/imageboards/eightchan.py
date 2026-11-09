import os
from datetime import UTC, datetime
from pathlib import Path

import bs4
from questionary import confirm
from curl_cffi import get
from rich import print
from rich.markup import escape
from pickledb import PickleDB
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TextColumn
)
from shrape.classes import Thread, Token
from shrape.db import get_powblock_token, dump_powblock_token
from shrape.utility import generate_token, print_info


SLID = "File not found"
BASE = "https://8chan.moe"
CAPTCHA = "POWBlock Check…"
TOS = "Terms of Service"
WORKERS = 16

def process(file) -> tuple[str, Path, str] | None:
    block: str = file.find("a", class_="originalNameLink")
    if block.get('href') is None:
        return None
    hashed_name = Path(
        block.get('href').split("/")[2]
    )

    return block.get("href"), hashed_name, block.get("download")


def download(thread: Thread, unattended: bool) -> Thread:
    url = thread.url
    assert url.path

    board = url.path.split("/")[1]
    id = url.path.split("/")[3].split(".")[0]
    path: Path = Path(f"./out/8chan_moe/[{board}] ({id})/")

    contents = None
    manifest = PickleDB(path / "manifest.json").load()

    while True:
        token: Token = get_powblock_token()

        if not hasattr(token, "cookies"):
            dump_powblock_token(generate_token(url))
            continue

        contents = bs4.BeautifulSoup(
            get(
                str(url),
                impersonate="chrome",
                cookies=token.cookies,
                headers=token.headers,
            ).text,
            "html.parser",
        )

        assert contents.title
        if contents.title.string == CAPTCHA or contents.title.string == TOS:
            dump_powblock_token(generate_token(url))
        else:
            break

    if contents.title.string == SLID:
        print(f"Thread #{id} on board '{board}' has slid")
        if unattended:
            thread.slid = True
            return thread
        if confirm("Do you want to move it to locked?").ask():
            thread.slid = True
            return thread

    filelist: bs4.ResultSet[bs4.element.PageElement | bs4.Tag] = contents(
        class_="originalNameLinkWrapper"
    )

    existing: int = 0
    new_dupes: int = 0
    old_dupes: int = 0
    errors: int = 0
    files: list[bs4.element.PageElement] = []
    locations: list[Path] = []

    # Dupe check
    for file in filelist:
        try:
            href, hashed_name, name = process(file)
        except Exception as _:
            errors += 1
            continue

        assert name

        manifest.set(str(hashed_name), name)

        location = path / hashed_name

        if os.path.exists(location):
            if location in locations:
                old_dupes += 1
            else:
                locations.append(location)
                existing += 1
        else:
            if location in locations:
                new_dupes += 1
            else:
                locations.append(location)
                files.append(file)

    file_count = len(files)

    print_info("8chan.moe", id, board, file_count, new_dupes, old_dupes, existing, errors)

    if not unattended:
        if not confirm("Do you want to continue?").ask():
            return thread

    if not os.path.exists(path):
        os.makedirs(path)

    manifest.save()

    if file_count > 0:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("[cyan]Downloading images...", total=file_count)

            with ThreadPoolExecutor(max_workers=WORKERS) as executor:
                futures = {
                    executor.submit(download_file, file, url, path, token)
                    for file in files
                }

                for future in as_completed(futures):
                    try:
                        future.result()  # Will raise exceptions if any occurred inside download_file
                    except Exception as exc:
                        print(f"Task generated an exception: {exc}")
                    finally:
                        progress.advance(task)


    if not isinstance(thread.name, str):
        subject = contents.find(class_="subject")

        if subject:
            thread.name = subject.getText()

    if not isinstance(thread.first_scraped, datetime):
        thread.first_scraped = datetime.now(UTC)

    thread.last_scraped = datetime.now(UTC)

    print()

    return thread


def download_file(file, url, path, token) -> None:
    href, hashed_name, _ = process(file)
    location = path / hashed_name
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": str(url),
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }

    img_response = get(
        BASE + href,
        impersonate="chrome",
        timeout=None,
        cookies=token.cookies,
        headers=headers,
    )
    
    if len(img_response.content) < 300:
        print(f"[red]Error downloading {escape(location.name)}[/red]")
        return None

    with open(location, "wb") as file:
        file.write(img_response.content)
    print(f"[green]Downloaded {escape(location.name)}[/green]")
    return None