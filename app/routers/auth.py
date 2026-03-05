from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.deps import get_db
from app.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.ApiResponse[schemas.AuthResponse])
def login(payload: schemas.LoginPayload, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(
        models.Usuario.email == payload.email.lower()
    ).first()

    if not usuario or not verify_password(payload.password, usuario.password_hash):
        return schemas.ApiResponse(success=False, message="Correo o contraseña incorrectos.")

    token = create_access_token({"sub": str(usuario.id)})
    return schemas.ApiResponse(
        success=True,
        data=schemas.AuthResponse(
            token=token,
            usuario=schemas.UsuarioOut.model_validate(usuario),
        ),
    )
