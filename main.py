from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from models import init_db
from routes import lists_router, tasks_router

My_TodoAPI = FastAPI(title="My Todo API", description="A simple API for managing todo lists and tasks", version="1.0.0")

@My_TodoAPI.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

init_db()

My_TodoAPI.include_router(tasks_router)
My_TodoAPI.include_router(lists_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(My_TodoAPI, host="0.0.0.0", port=8000)