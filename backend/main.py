import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.conrumbo import router as conrumbo_router

app = FastAPI(title="ConRumbo API", version="1.0.0")

# Habilitar CORS para todas las rutas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(conrumbo_router, prefix="/api/conrumbo")

@app.get("/")
async def root():
    return {"message": "ConRumbo API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

