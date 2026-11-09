from typed_argparse import Parser
from shrape.classes import Args, Thread
from shrape.db import dump_threads, get_threads
from shrape.utility import get_thread_by_url
import shrape.imageboards.soyjak as soyjak
import shrape.imageboards.eightchan as eightchan


def runner(args: Args) -> None:
    threads_process: list[Thread] = []
    threads_done: list[Thread] = []
    threads_existing: list[Thread] = get_threads()

    for url in args.url:
        if get_thread_by_url(url, threads_existing) is None:
            threads_process.append(Thread(url))
        else:
            thread = get_thread_by_url(url, threads_existing)
            threads_process.append(thread)
            threads_existing.remove(thread)

    if args.reload:
        threads_process += threads_existing

    for thread in threads_process:
        parts = str(thread.url).split("/")
        base_url = f"{parts[0]}//{parts[2]}"
        match base_url:
            case soyjak.BASE:
                threads_done.append(soyjak.download(thread, args.unattended))
            case eightchan.BASE:
                threads_done.append(eightchan.download(thread, args.unattended))

    dump_threads(threads_done)


def main() -> None:
    Parser(Args).bind(runner).run()


if __name__ == "__main__":
    main()
