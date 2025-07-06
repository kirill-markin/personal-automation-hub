from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.webhooks.notion import router as notion_router
from backend.api.v1.webhooks.google_calendar import router as google_calendar_router
from backend.api.v1.webhooks.gmail import router as gmail_router

app = FastAPI(title="Personal Automation Hub")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notion_router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(google_calendar_router, prefix="/api/v1/webhooks", tags=["webhooks", "google-calendar"])
app.include_router(gmail_router, prefix="/api/v1/webhooks", tags=["webhooks", "gmail"])


@app.get("/")
async def root():
    return {"message": "Welcome to Personal Automation Hub"} 