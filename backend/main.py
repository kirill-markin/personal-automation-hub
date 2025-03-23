from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.webhooks.notion import router as notion_router

app = FastAPI(title="Personal Automation Hub")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notion_router, prefix="/api/v1/webhooks", tags=["webhooks"])


@app.get("/")
async def root():
    return {"message": "Welcome to Personal Automation Hub"} 