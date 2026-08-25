from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import jobs, match, profile

app = FastAPI(title="Job Match Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(jobs.router)
app.include_router(match.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
