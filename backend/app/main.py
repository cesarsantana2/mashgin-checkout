from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.menu import router as menu_router
from app.api.routes.orders import router as orders_router

app = FastAPI(title="Mashgin Checkout API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(menu_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
