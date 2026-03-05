from __future__ import annotations
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel
from datetime import date, datetime

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None


# ── Auth ──────────────────────────────────────────────────────────
class LoginPayload(BaseModel):
    email: str
    password: str


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: str
    cargo: str
    rol: str
    avatar: str
    bloqueado: bool = False

    class Config:
        from_attributes = True


class UsuarioUpdate(BaseModel):
    cargo: Optional[str] = None
    rol: Optional[str] = None
    bloqueado: Optional[bool] = None


class AuthResponse(BaseModel):
    token: str
    usuario: UsuarioOut


# ── Documentos ────────────────────────────────────────────────────
class DocumentoOut(BaseModel):
    id: int
    tipo: str
    proveedor: str
    ot: str
    folio: str
    fecha: date
    subtotal: float
    observaciones: str
    archivo_url: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentoIn(BaseModel):
    tipo: str
    proveedor: str
    ot: str = ""
    folio: str = ""
    fecha: date
    subtotal: float
    observaciones: str = ""
    archivo_local: Optional[str] = None


# ── Usuario básico (embebido en rendiciones) ───────────────────────
class UsuarioBasico(BaseModel):
    id: int
    nombre: str
    avatar: str
    cargo: str

    class Config:
        from_attributes = True


# ── Historial de rendiciones ──────────────────────────────────────
class HistorialOut(BaseModel):
    id: int
    estado_anterior: str
    estado_nuevo: str
    observaciones: Optional[str] = None
    actor_nombre: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Rendiciones ───────────────────────────────────────────────────
class RendicionOut(BaseModel):
    id: int
    nro_rendicion: int
    fecha: date
    descripcion: str
    solicitud_fondo: Optional[str] = None
    estado: str
    total: float
    observaciones: Optional[str] = None
    usuario_id: int
    usuario: Optional[UsuarioBasico] = None
    documentos: List[DocumentoOut] = []
    historial: List[HistorialOut] = []

    class Config:
        from_attributes = True


class NuevaRendicionPayload(BaseModel):
    fecha: date
    descripcion: str
    solicitud_fondo: Optional[str] = None
    documentos: List[DocumentoIn]


class EditarRendicionPayload(BaseModel):
    descripcion: str
    solicitud_fondo: Optional[str] = None
    documentos: List[DocumentoIn]


# ── Admin: crear usuario ──────────────────────────────────────────
class NuevoUsuarioPayload(BaseModel):
    nombre: str
    email: str
    password: str
    cargo: str
    rol: str = "colaborador"
    avatar: str


# ── Admin: actualizar estado rendición ───────────────────────────
class ActualizarEstadoPayload(BaseModel):
    estado: str                    # 'aprobado' | 'rechazado'
    observaciones: Optional[str] = None


# ── Cambiar contraseña ────────────────────────────────────────────
class CambiarPasswordPayload(BaseModel):
    password_actual: str
    password_nueva: str


# ── Actualizar perfil ─────────────────────────────────────────────
class ActualizarPerfilPayload(BaseModel):
    nombre: str


# ── Push token ────────────────────────────────────────────────────
class PushTokenPayload(BaseModel):
    token: str
