# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import products, forecast

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

origins = [
    "http://localhost:3000",      # React Localhost URL
    "http://127.0.0.1:3000",
]

# CORS Setup for secure cross-origin resource access
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(forecast.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "online", "system": "AgroLink AI Enterprise Engine Gateway"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)