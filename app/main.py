from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
from app.routers import auth, rendiciones, usuarios, push_tokens
from app.database import engine, Base
from app.deps import get_db
from app import models  # registra todos los modelos


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea tablas faltantes al arrancar (seguro: no borra datos existentes)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Maysi API", version="1.0.0", lifespan=lifespan)

# CORS — permite peticiones desde Expo Go y la app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos locales (solo en desarrollo sin Cloudinary)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routers
app.include_router(auth.router)
app.include_router(rendiciones.router)
app.include_router(usuarios.router)
app.include_router(push_tokens.router)


@app.get("/")
def health():
    return {"status": "ok", "app": "Maysi API"}


@app.post("/seed-admin")
def seed_admin(db: Session = Depends(get_db)):
    from passlib.context import CryptContext
    existing = db.query(models.Usuario).filter(models.Usuario.email == "admin@maysi.com").first()
    if existing:
        return {"message": "Admin ya existe"}
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = models.Usuario(
        nombre="Admin",
        email="admin@maysi.com",
        password_hash=pwd.hash("admin123"),
        rol="admin",
        activo=True,
    )
    db.add(user)
    db.commit()
    return {"message": "Admin creado", "email": "admin@maysi.com", "password": "admin123"}
