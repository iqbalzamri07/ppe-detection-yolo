import uvicorn
from fastapi import FastAPI
from app.api.routes import router

# 1. Initialize FastAPI app
app = FastAPI(title="PPE Detection API")

# 2. Include your routes
app.include_router(router)

# 3. This allows you to run it directly via Python if you want
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)