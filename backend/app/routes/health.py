from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="État de santé de l'API",
    description="Vérifie que l'API répond. Utilisé par Docker et les sondes de supervision.",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}
