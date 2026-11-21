"""Worker entry point - `uv run python -m coral_sync_api.workers.main`."""

from coral_sync_api.workers.investigate import main as investigate_main


def main() -> None:
    import asyncio

    asyncio.run(investigate_main())


if __name__ == "__main__":
    main()
