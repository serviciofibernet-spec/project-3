from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.routes import api_router

APP_VERSION = "0.1.0"


def create_app() -> FastAPI:
    app = FastAPI(title="OLT C300 V2 Admin Panel", version=APP_VERSION)

    # API
    app.include_router(api_router, prefix="/api")

    # Serve minimal SPA from web/
    static_dir = Path(__file__).parent / "web"
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="web")

    return app


app = create_app()


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Run OLT C300 V2 Admin Panel")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    uvicorn.run("olt_panel.main:app", host=args.host, port=args.port, reload=False)
