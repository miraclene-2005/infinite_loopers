# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, SessionLocal
from . import crud

from .routers import incidents
from .routers import resources
from .routers import hospitals
from .routers import routes
from .routers import evacuation
from .routers import alerts
from .routers import replanning


Base.metadata.create_all(bind=engine)

# Seed initial database state if empty
db = SessionLocal()
try:
    crud.seed_database_if_empty(db)
finally:
    db.close()

app = FastAPI(
    title="Industrial Crisis Command AI",
    version="1.0.0",
    description="Multi-Agent Industrial Accident Crisis Command Backend"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(incidents.router)
app.include_router(resources.router)
app.include_router(hospitals.router)
app.include_router(routes.router)
app.include_router(evacuation.router)
app.include_router(alerts.router)
app.include_router(replanning.router)


# pyrefly: ignore [missing-import]
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Industrial Crisis Command</title>
        <style>
            body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; }
            iframe { width: 100%; height: 100%; border: none; }
        </style>
    </head>
    <body>
        <iframe src="http://localhost:3000" allow="fullscreen; autoplay; clipboard-write; encrypted-media; picture-in-picture"></iframe>
    </body>
    </html>
    """