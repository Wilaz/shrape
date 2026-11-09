import os
from datetime import UTC, datetime
from pathlib import Path

import bs4
from questionary import confirm
from curl_cffi import get
from rich import print
from rich.progress import track
from rich.markup import escape
from pickledb import PickleDB


from shrape.classes import Thread, Token
from shrape.db import get_cf_token, dump_cf_token
from shrape.utility import generate_token, print_info


SLID = "404 - Not found"
BASE = "https://soyjak.st"
CAPTCHA = "Just a moment..."


def process(file) -> tuple[str, Path, str]:
    block: str = file.find("a", class_="filename-download-link")
    hashed_name = Path(
        f"{file.find('span', attrs={'class': 'filehash'}).getText()}.{block.get('href').split('.')[-1]}"
    )

    return block.get("href"), hashed_name, block.get("download")


def download(thread: Thread, unattended: bool) -> Thread:
    url = thread.url
    assert url.path

    board = url.path.split("/")[1]
    id = url.path.split("/")[3].split(".")[0]
    path: Path = Path(f"./out/[{board}] ({id})/")

    contents = None
    manifest = PickleDB(path / "manifest.json").load()

    while True:
        token: Token = get_cf_token()

        if not hasattr(token, "cookies"):
            dump_cf_token(generate_token(url))
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
        if contents.title.string == CAPTCHA:
            dump_cf_token(generate_token(url))
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
        class_="fileinfo"
    )

    existing: int = 0
    new_dupes: int = 0
    old_dupes: int = 0
    files: list[bs4.element.PageElement] = []
    locations: list[Path] = []

    # Dupe check
    for file in filelist:
        href, hashed_name, name = process(file)
        assert name

        manifest.set(href.split("/")[3], (name, str(hashed_name)))

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

    print_info("Soyjak Party", id, board, file_count, new_dupes, old_dupes, existing)

    if not unattended:
        if not confirm("Do you want to continue?").ask():
            return thread

    if not os.path.exists(path):
        os.makedirs(path)

    manifest.save()

    if file_count > 0:
        for file in track(files, description="Downloading Images..."):
            href, hashed_name, _ = process(file)
            location = path / hashed_name

            img_response = get(
                BASE + href,
                impersonate="chrome",
                timeout=None,
                cookies=token.cookies,
                headers=token.headers,
            )
            with open(location, "wb") as file:
                file.write(img_response.content)
            print(f"[green]Downloaded {escape(location.name)}[/green]")

    if not isinstance(thread.name, str):
        subject = contents.find(class_="subject")

        if subject:
            thread.name = subject.getText()

    if not isinstance(thread.first_scraped, datetime):
        thread.first_scraped = datetime.now(UTC)

    thread.last_scraped = datetime.now(UTC)

    print()

    return thread
