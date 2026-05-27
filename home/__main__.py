"""Entry point.

  python -m home          → launch the home (default)
  python -m home brief    → build the daily brief + push to Apple Notes
  python -m home brief --no-push → build + write file only
"""

import sys


def main() -> None:
    argv = sys.argv[1:]
    if argv and argv[0] == "brief":
        from .brief import main_cli
        raise SystemExit(main_cli(argv[1:]))
    if argv and argv[0] == "scan":
        from .scan import main_cli as scan_cli
        raise SystemExit(scan_cli(argv[1:]))
    from .app import CosHome
    CosHome().run()


if __name__ == "__main__":
    main()
