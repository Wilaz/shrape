from datetime import datetime
from typing import Any, Self

import typed_argparse as tap
from pydantic import HttpUrl


class Thread:
    url: HttpUrl
    name: str | None = None
    first_scraped: datetime | None = None
    last_scraped: datetime | None = None
    slid: bool = False

    def to_dict(self) -> dict[str, Any]:
        thread_dict: dict[str, Any] = {"url": str(self.url)}

        if type(self.name) is str:
            thread_dict["name"] = self.name

        if type(self.first_scraped) is datetime:
            thread_dict["first_scraped"] = self.first_scraped

        if type(self.last_scraped) is datetime:
            thread_dict["last_scraped"] = self.last_scraped

        return thread_dict

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any], slid: bool = False) -> Self:
        assert "url" in dictionary

        thread = cls(HttpUrl(dictionary["url"]), slid=slid)

        if "name" in dictionary:
            thread.name = dictionary["name"]

        if "first_scraped" in dictionary:
            thread.first_scraped = dictionary["first_scraped"]

        if "last_scraped" in dictionary:
            thread.last_scraped = dictionary["last_scraped"]

        return thread

    def __init__(self, url: HttpUrl, slid: bool = False) -> None:
        self.url = url
        self.slid = slid


class Token:
    cookies: str
    headers: dict[str, str]

    def to_dict(self):
        return {"token": {"cookies": self.cookies, "headers": self.headers}}

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> Self:
        return cls(dictionary["token"]["cookies"], dictionary["token"]["headers"])

    def __init__(self, cookies: str, headers: dict[str, str]) -> None:
        self.cookies = cookies
        self.headers = headers


class Args(tap.TypedArgs):
    url: list[HttpUrl] = tap.arg(
        positional=True,
        help="thread url",
        nargs="*",
    )

    reload: bool = tap.arg(
        "-r", "--reload", help="rescrapes every keyed thread in toml db"
    )
    unattended: bool = tap.arg("-y", "--yes", help="assume yes")
