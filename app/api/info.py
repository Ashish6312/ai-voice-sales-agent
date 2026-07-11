from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/info")
def app_info():

    settings = get_settings()

    return {
        "app": settings.app_name,
        "version": settings.app_version
    }