import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app import models, schemas
from app.deps import get_db, get_current_user
from app.config import settings

# Configurar Cloudinary si las variables de entorno están presentes
_cloudinary_enabled = bool(settings.CLOUDINARY_CLOUD_NAME)
if _cloudinary_enabled:
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
    )

router = APIRouter(prefix="/rendiciones", tags=["rendiciones"])


@router.get("", response_model=schemas.ApiResponse[List[schemas.RendicionOut]])
def listar(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    # Admin ve todas las rendiciones; colaborador solo las suyas
    q = db.query(models.Rendicion)
    if current_user.rol != "admin":
        q = q.filter(models.Rendicion.usuario_id == current_user.id)
    rendiciones = q.order_by(models.Rendicion.id.desc()).all()
    return schemas.ApiResponse(success=True, data=rendiciones)


@router.get("/{rendicion_id}", response_model=schemas.ApiResponse[schemas.RendicionOut])
def obtener(
    rendicion_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    q = db.query(models.Rendicion).filter(models.Rendicion.id == rendicion_id)
    if current_user.rol != "admin":
        q = q.filter(models.Rendicion.usuario_id == current_user.id)
    rendicion = q.first()
    if not rendicion:
        return schemas.ApiResponse(success=False, message="Rendicion no encontrada.")
    return schemas.ApiResponse(success=True, data=rendicion)


@router.post("", response_model=schemas.ApiResponse[schemas.RendicionOut])
def crear(
    payload: schemas.NuevaRendicionPayload,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    ultimo = (
        db.query(models.Rendicion)
        .order_by(models.Rendicion.nro_rendicion.desc())
        .first()
    )
    nro = (ultimo.nro_rendicion + 1) if ultimo else 1
    total = sum(float(d.subtotal) for d in payload.documentos)

    rendicion = models.Rendicion(
        nro_rendicion=nro,
        fecha=payload.fecha,
        descripcion=payload.descripcion,
        solicitud_fondo=payload.solicitud_fondo,
        estado="pendiente",
        total=total,
        usuario_id=current_user.id,
    )
    db.add(rendicion)
    db.flush()

    for doc in payload.documentos:
        documento = models.Documento(
            rendicion_id=rendicion.id,
            tipo=doc.tipo,
            proveedor=doc.proveedor,
            ot=doc.ot,
            folio=doc.folio,
            fecha=doc.fecha,
            subtotal=float(doc.subtotal),
            observaciones=doc.observaciones,
        )
        db.add(documento)

    db.commit()
    db.refresh(rendicion)
    return schemas.ApiResponse(success=True, data=rendicion)


@router.post("/{rendicion_id}/archivo", response_model=schemas.ApiResponse[dict])
def subir_archivo(
    rendicion_id: int,
    doc_id: int = Query(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    rendicion = db.query(models.Rendicion).filter(
        models.Rendicion.id == rendicion_id,
        models.Rendicion.usuario_id == current_user.id,
    ).first()
    if not rendicion:
        return schemas.ApiResponse(success=False, message="Rendicion no encontrada.")

    documento = db.query(models.Documento).filter(
        models.Documento.id == doc_id,
        models.Documento.rendicion_id == rendicion_id,
    ).first()
    if not documento:
        return schemas.ApiResponse(success=False, message="Documento no encontrado.")

    if _cloudinary_enabled:
        # Subir a Cloudinary — URL permanente, no depende del servidor
        result = cloudinary.uploader.upload(
            archivo.file,
            public_id=f"maysi/comp_{rendicion_id}_{doc_id}",
            overwrite=True,
            resource_type="image",
        )
        url = result["secure_url"]
    else:
        # Fallback local (solo desarrollo)
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        filename = f"comp_{rendicion_id}_{doc_id}.jpg"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(archivo.file, f)
        url = f"/uploads/{filename}"

    documento.archivo_url = url
    db.commit()

    return schemas.ApiResponse(success=True, data={"url": url})


@router.patch("/{rendicion_id}", response_model=schemas.ApiResponse[schemas.RendicionOut])
def editar(
    rendicion_id: int,
    payload: schemas.EditarRendicionPayload,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    rendicion = db.query(models.Rendicion).filter(
        models.Rendicion.id == rendicion_id,
        models.Rendicion.usuario_id == current_user.id,
    ).first()
    if not rendicion:
        return schemas.ApiResponse(success=False, message="Rendicion no encontrada.")

    estado_str = str(rendicion.estado.value if hasattr(rendicion.estado, "value") else rendicion.estado)
    if estado_str != "rechazado":
        return schemas.ApiResponse(success=False, message="Solo se pueden editar rendiciones rechazadas.")

    # Actualizar campos principales
    rendicion.descripcion = payload.descripcion
    rendicion.solicitud_fondo = payload.solicitud_fondo
    rendicion.estado = "pendiente"
    rendicion.observaciones = None  # limpiar motivo de rechazo anterior

    # Reemplazar documentos
    db.query(models.Documento).filter(models.Documento.rendicion_id == rendicion_id).delete()
    total = 0.0
    for doc in payload.documentos:
        documento = models.Documento(
            rendicion_id=rendicion.id,
            tipo=doc.tipo,
            proveedor=doc.proveedor,
            ot=doc.ot,
            folio=doc.folio,
            fecha=doc.fecha,
            subtotal=float(doc.subtotal),
            observaciones=doc.observaciones,
        )
        db.add(documento)
        total += float(doc.subtotal)
    rendicion.total = total
    db.flush()

    # Registrar en historial
    hist = models.HistorialRendicion(
        rendicion_id=rendicion.id,
        estado_anterior="rechazado",
        estado_nuevo="pendiente",
        observaciones="Reenviada tras correcciones",
        actor_id=current_user.id,
        actor_nombre=current_user.nombre,
    )
    db.add(hist)
    db.commit()
    db.refresh(rendicion)
    return schemas.ApiResponse(success=True, data=rendicion)


@router.patch("/{rendicion_id}/estado", response_model=schemas.ApiResponse[schemas.RendicionOut])
def actualizar_estado(
    rendicion_id: int,
    payload: schemas.ActualizarEstadoPayload,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden cambiar el estado.")

    estados_validos = {"aprobado", "rechazado", "pendiente"}
    if payload.estado not in estados_validos:
        return schemas.ApiResponse(success=False, message="Estado invalido.")

    rendicion = db.query(models.Rendicion).filter(models.Rendicion.id == rendicion_id).first()
    if not rendicion:
        return schemas.ApiResponse(success=False, message="Rendicion no encontrada.")

    estado_anterior = str(rendicion.estado.value if hasattr(rendicion.estado, "value") else rendicion.estado)
    rendicion.estado = payload.estado
    if payload.observaciones is not None:
        rendicion.observaciones = payload.observaciones
    db.commit()

    # Registrar en historial
    hist = models.HistorialRendicion(
        rendicion_id=rendicion.id,
        estado_anterior=estado_anterior,
        estado_nuevo=payload.estado,
        observaciones=payload.observaciones,
        actor_id=current_user.id,
        actor_nombre=current_user.nombre,
    )
    db.add(hist)
    db.commit()
    db.refresh(rendicion)

    # Notificar al dueño de la rendición via push
    owner = db.query(models.Usuario).filter(models.Usuario.id == rendicion.usuario_id).first()
    if owner and owner.push_token:
        from app.push import send_push
        if payload.estado == "aprobado":
            titulo = "Rendición aprobada ✓"
            cuerpo = f"Tu rendición Nro. {rendicion.nro_rendicion} fue aprobada correctamente."
        else:
            titulo = "Rendición rechazada"
            motivo = f" Motivo: {payload.observaciones}" if payload.observaciones else ""
            cuerpo = f"Tu rendición Nro. {rendicion.nro_rendicion} fue rechazada.{motivo}"
        send_push(owner.push_token, titulo, cuerpo, {"rendicion_id": rendicion.id})

    return schemas.ApiResponse(success=True, data=rendicion)
