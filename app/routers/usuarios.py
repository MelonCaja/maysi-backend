from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.deps import get_db, get_current_user
from app.security import hash_password, verify_password

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def require_admin(current_user: models.Usuario = Depends(get_current_user)):
    rol = current_user.rol
    rol_str = rol.value if hasattr(rol, "value") else str(rol)
    if rol_str != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores.")
    return current_user


@router.get("/me", response_model=schemas.ApiResponse[schemas.UsuarioOut])
def me(current_user: models.Usuario = Depends(get_current_user)):
    return schemas.ApiResponse(success=True, data=schemas.UsuarioOut.model_validate(current_user))


@router.patch("/me", response_model=schemas.ApiResponse[schemas.UsuarioOut])
def actualizar_perfil(
    payload: schemas.ActualizarPerfilPayload,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    nombre = payload.nombre.strip()
    if not nombre:
        return schemas.ApiResponse(success=False, message="El nombre no puede estar vacío.")
    current_user.nombre = nombre
    palabras = nombre.split()
    if len(palabras) >= 2:
        current_user.avatar = (palabras[0][0] + palabras[-1][0]).upper()
    else:
        current_user.avatar = palabras[0][:2].upper()
    db.commit()
    db.refresh(current_user)
    return schemas.ApiResponse(success=True, data=schemas.UsuarioOut.model_validate(current_user))


@router.patch("/me/password", response_model=schemas.ApiResponse[None])
def cambiar_password(
    payload: schemas.CambiarPasswordPayload,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    if not verify_password(payload.password_actual, current_user.password_hash):
        return schemas.ApiResponse(success=False, message="La contraseña actual es incorrecta.")
    current_user.password_hash = hash_password(payload.password_nueva)
    db.commit()
    return schemas.ApiResponse(success=True)


@router.get("", response_model=schemas.ApiResponse[List[schemas.UsuarioOut]])
def listar(
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(require_admin),
):
    usuarios = db.query(models.Usuario).order_by(models.Usuario.nombre).all()
    return schemas.ApiResponse(success=True, data=usuarios)


@router.put("/{usuario_id}", response_model=schemas.ApiResponse[schemas.UsuarioOut])
def actualizar(
    usuario_id: int,
    payload: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_admin),
):
    if usuario_id == current_user.id and payload.bloqueado is True:
        return schemas.ApiResponse(success=False, message="No puedes bloquearte a ti mismo.")
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        return schemas.ApiResponse(success=False, message="Usuario no encontrado.")
    if payload.cargo is not None:
        usuario.cargo = payload.cargo
    if payload.rol is not None:
        usuario.rol = payload.rol
    if payload.bloqueado is not None:
        usuario.bloqueado = payload.bloqueado
    db.commit()
    db.refresh(usuario)
    return schemas.ApiResponse(success=True, data=schemas.UsuarioOut.model_validate(usuario))


@router.delete("/{usuario_id}", response_model=schemas.ApiResponse[None])
def eliminar(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_admin),
):
    if usuario_id == current_user.id:
        return schemas.ApiResponse(success=False, message="No puedes eliminarte a ti mismo.")
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        return schemas.ApiResponse(success=False, message="Usuario no encontrado.")
    db.delete(usuario)
    db.commit()
    return schemas.ApiResponse(success=True)


@router.post("", response_model=schemas.ApiResponse[schemas.UsuarioOut])
def crear(
    payload: schemas.NuevoUsuarioPayload,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(require_admin),
):
    existe = db.query(models.Usuario).filter(models.Usuario.email == payload.email.lower()).first()
    if existe:
        return schemas.ApiResponse(success=False, message="Ya existe un usuario con ese correo.")

    usuario = models.Usuario(
        nombre=payload.nombre,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        cargo=payload.cargo,
        rol=payload.rol,
        avatar=payload.avatar,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return schemas.ApiResponse(success=True, data=schemas.UsuarioOut.model_validate(usuario))
