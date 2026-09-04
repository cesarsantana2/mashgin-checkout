from fastapi import FastAPI

from app.api.routes.menu import router as menu_router


app = FastAPI(
    title="Mashgin Checkout API",
    version="0.1.0",
)

app.include_router(menu_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}