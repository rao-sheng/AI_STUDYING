from fastapi import APIRouter

router=APIRouter(tags=["system"])

@router.get("/")
def get_api_info() ->dict[str,str]:
    return {
  "name": "WorkMate API",
  "version": "0.1.0",
  "docs": "/docs"
}