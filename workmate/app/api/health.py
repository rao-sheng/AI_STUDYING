from fastapi import APIRouter


router = APIRouter(tags=["system"])


@router.get("/health")
def get_health() -> dict[str, str]:
    """Return a lightweight process health signal."""
    return {"status": "ok"}

