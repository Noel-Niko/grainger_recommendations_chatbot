from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"})


@router.get("/")
async def read_root():
    return {"message": "Welcome to the Grainger Recommendations API"}


@router.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={"message": "No favicon available"}, status_code=204)
