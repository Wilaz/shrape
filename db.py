from pathlib import Path
from typing import Any

from rtoml import load, dump

from classes import Thread, Token
from utility import get_thread_by_url

THREADS = Path("./threads.toml")
TOKEN = Path("./turnstile.toml")


def get_threads() -> list[Thread]:
    return [Thread.from_dict(thread) for thread in load(THREADS)["keyed"]]


def dump_threads(new_threads: list[Thread]) -> None:
    data = load(THREADS)
    threads: list[Thread] = []
    result: dict[str, list[dict[str, Any]]] = {"keyed": [], "locked": []}

    if "keyed" in data:
        threads.extend(
            [Thread.from_dict(thread, slid=False) for thread in data["keyed"]]
        )

    if "locked" in data:
        threads.extend(
            [Thread.from_dict(thread, slid=True) for thread in data["locked"]]
        )

    for thread in new_threads:
        try:
            threads.remove(get_thread_by_url(thread.url, threads))
        except ValueError:
            pass
        threads.append(thread)

    for thread in threads:
        if thread.slid:
            result["locked"].append(thread.to_dict())
        else:
            result["keyed"].append(thread.to_dict())

    _ = dump(
        {key: value for key, value in result.items() if value not in [[]]},
        THREADS,
    )


def get_token() -> Token:
    return Token.from_dict(load(TOKEN))


def dump_token(token: Token) -> None:
    _ = dump(token.to_dict(), TOKEN)
