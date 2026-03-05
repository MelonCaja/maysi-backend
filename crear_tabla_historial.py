"""
Script de un solo uso: crea la tabla historial_rendicion si no existe.
Ejecutar desde la carpeta maysi-backend:
    python crear_tabla_historial.py
"""
from app.database import engine, Base
from app import models  # registra todos los modelos incluido HistorialRendicion

Base.metadata.create_all(bind=engine)
print("✓ Tablas creadas/verificadas correctamente.")
