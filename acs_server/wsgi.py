import os
from waitress import serve

from .app import create_app


def main() -> None:
    app = create_app()
    port = int(os.environ.get("PORT", "7547"))
    host = os.environ.get("HOST", "0.0.0.0")
    threads = int(os.environ.get("THREADS", "8"))

    serve(app, host=host, port=port, threads=threads, ident="tr069-acs")


if __name__ == "__main__":
    main()
