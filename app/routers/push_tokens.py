from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.deps import get_db, get_current_user

router = APIRouter(tags=["push-tokens"])


@router.post("/push-token", response_model=schemas.ApiResponse[None])
def guardar_push_token(
    payload: schemas.PushTokenPayload,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    current_user.push_token = payload.token
    db.commit()
    return schemas.ApiResponse(success=True)
