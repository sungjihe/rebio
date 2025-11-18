from fastapi import FastAPI
from backend.api.routes_rebio import router as rebio_router

app = FastAPI(title="ReBio Multi-Agent API")

# Register ReBio Multi-Agent Workflow Route
app.include_router(rebio_router, prefix="/rebio")  # prefix 넣는 걸 추천

@app.get("/")
def root():
    return {"message": "ReBio Multi-Agent API is running."}
