from os import listdir
from pydantic import HttpUrl
from classes import Thread

BASE = "https://soyjak.st"

def convert() -> dict[str, list[Thread]]:
    data: dict[str, list[Thread]] = {"keyed": []}

    for folder in listdir("./out"):
        data["keyed"].append(
            Thread(
                HttpUrl(
                    f"{BASE}/{folder.split()[0][1:-1]}/thread/{folder.split()[1][1:-1]}.html"
                ),
            )
        )

    return data


def get_thread_by_url(url: HttpUrl, thread_list: list[Thread]) -> Thread | None:
    for thread in thread_list:
        if thread.url == url:
            return thread
    return None
