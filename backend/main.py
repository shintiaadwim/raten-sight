import asyncio
from contextlib import asynccontextmanager
from threading import Event, Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.batch import BatchProcessor, BatchSettings


def create_app(settings: BatchSettings | None = None) -> FastAPI:
    processor = BatchProcessor(settings or BatchSettings.from_environment())

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        stop = Event()
        worker = Thread(target=processor.watch, args=(stop,), name="retensight-batch")
        worker.start()
        try:
            yield
        finally:
            stop.set()
            await asyncio.to_thread(worker.join)

    app = FastAPI(title="RetenSight", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["GET"],
    )

    def serve(section: str) -> JSONResponse:
        return JSONResponse(processor.state.response(section), headers={"Cache-Control": "no-store"})

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/dataset-summary")
    async def dataset_summary():
        return serve("dataset_summary")

    @app.get("/api/predictions")
    async def predictions():
        return serve("predictions")

    @app.get("/api/model-info")
    async def model_info():
        return serve("model_info")

    return app


app = create_app()
