from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/ready")
async def readiness_check():
    # Currently only reports basic application readiness.
    # Future: Check DB, OCR services, etc.
    return {"status": "ready"}

