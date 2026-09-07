"""Worker entry point - `uv run python -m opsgaurdian_api.workers.main`."""

from opsgaurdian_api.workers.investigate import main as investigate_main


def main() -> None:
    import asyncio

    asyncio.run(investigate_main())


if __name__ == "__main__":
    main()
