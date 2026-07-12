from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.routers import products, forecast
import traceback

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

# 1. CORS Setup - Add all allowed origins clearly
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://agro-link-fqzf-rcytpnece-krishan2001.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Include Routers
app.include_router(products.router)
app.include_router(forecast.router)

# 3. Global Exception Handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # This will print the error in your terminal, preventing silent 400s
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )

# 4. Clean Root Routes
@app.get("/")
async def root():
    return {
        "status": "online", 
        "system": "AgroLink AI Enterprise Engine Gateway",
        "docs": "http://127.0.0.1:8000/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 to ensure it is accessible in containerized/networked environments
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)