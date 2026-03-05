from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Date, Text, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id         = Column(Integer, primary_key=True, index=True)
    nombre     = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    cargo      = Column(String(100), nullable=False)
    rol        = Column(Enum("admin", "colaborador", name="rol_enum"), nullable=False, default="colaborador")
    avatar     = Column(String(2), nullable=False)
    push_token = Column(String(255), nullable=True)
    bloqueado  = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    rendiciones = relationship("Rendicion", back_populates="usuario")


class Rendicion(Base):
    __tablename__ = "rendiciones"

    id              = Column(Integer, primary_key=True, index=True)
    nro_rendicion   = Column(Integer, nullable=False)
    fecha           = Column(Date, nullable=False)
    descripcion     = Column(String(255), nullable=False)
    solicitud_fondo = Column(String(100), nullable=True)
    estado          = Column(Enum("pendiente", "aprobado", "rechazado", name="estado_enum"), nullable=False, default="pendiente")
    total           = Column(Numeric(12, 2), nullable=False, default=0)
    observaciones   = Column(Text, nullable=True)
    usuario_id      = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    usuario     = relationship("Usuario", back_populates="rendiciones")
    documentos  = relationship("Documento", back_populates="rendicion", cascade="all, delete-orphan")
    historial   = relationship("HistorialRendicion", back_populates="rendicion",
                               cascade="all, delete-orphan", order_by="HistorialRendicion.created_at")


class HistorialRendicion(Base):
    __tablename__ = "historial_rendicion"

    id              = Column(Integer, primary_key=True, index=True)
    rendicion_id    = Column(Integer, ForeignKey("rendiciones.id", ondelete="CASCADE"), nullable=False, index=True)
    estado_anterior = Column(String(20), nullable=False)
    estado_nuevo    = Column(String(20), nullable=False)
    observaciones   = Column(Text, nullable=True)
    actor_id        = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    actor_nombre    = Column(String(100), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    rendicion = relationship("Rendicion", back_populates="historial")


class Documento(Base):
    __tablename__ = "documentos"

    id           = Column(Integer, primary_key=True, index=True)
    rendicion_id = Column(Integer, ForeignKey("rendiciones.id", ondelete="CASCADE"), nullable=False)
    tipo         = Column(String(50), nullable=False)
    proveedor    = Column(String(150), nullable=False)
    ot           = Column(String(50), nullable=False, default="")
    folio        = Column(String(50), nullable=False, default="")
    fecha        = Column(Date, nullable=False)
    subtotal     = Column(Numeric(12, 2), nullable=False, default=0)
    observaciones = Column(Text, nullable=False, default="")
    archivo_url  = Column(String(500), nullable=True)

    rendicion = relationship("Rendicion", back_populates="documentos")
