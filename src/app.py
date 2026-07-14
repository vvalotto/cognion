from fastapi import FastAPI

app = FastAPI(title="Cognion", version="0.1.0")


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
