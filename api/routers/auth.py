"""Inicio de sesión con JWT."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from api import schemas
from api.deps import current_user, get_db
from api.security import authenticate, create_token

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/login", response_model=schemas.TokenOut, summary="Iniciar sesión")
def login(body: schemas.LoginIn) -> schemas.TokenOut:
    user = authenticate(get_db(), body.usuario.strip(), body.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contraseña incorrectos.")
    return schemas.TokenOut(access_token=create_token(user), user=schemas.User(**user))


@router.get("/me", response_model=schemas.User, summary="Usuario de la sesión")
def me(user: dict = Depends(current_user)) -> schemas.User:
    return schemas.User(**user)
