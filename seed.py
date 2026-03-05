"""
Crea usuarios de prueba en la base de datos.
Ejecutar UNA vez después de `alembic upgrade head`.

    python seed.py
"""
from app.database import SessionLocal
from app.models import Usuario
from app.security import hash_password


USUARIOS = [
    {"nombre": "Daniel Reyes",  "email": "daniel@maysi.cl", "cargo": "Técnico Senior",  "rol": "colaborador", "avatar": "DR"},
    {"nombre": "Renán Medina",  "email": "renan@maysi.cl",  "cargo": "Operaciones",     "rol": "colaborador", "avatar": "RM"},
    {"nombre": "Administrador", "email": "admin@maysi.cl",  "cargo": "Administrador",   "rol": "admin",       "avatar": "AD"},
]

PASSWORD = "1234"


def main():
    db = SessionLocal()
    try:
        for u in USUARIOS:
            existe = db.query(Usuario).filter(Usuario.email == u["email"]).first()
            if existe:
                print(f"  [skip] {u['email']} ya existe")
                continue
            usuario = Usuario(
                nombre=u["nombre"],
                email=u["email"],
                password_hash=hash_password(PASSWORD),
                cargo=u["cargo"],
                rol=u["rol"],
                avatar=u["avatar"],
            )
            db.add(usuario)
            print(f"  [ok]   {u['email']} creado")
        db.commit()
        print("\nSeed completado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
