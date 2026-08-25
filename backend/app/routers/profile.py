import json

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Profile
from app.models.profile import ProfileResponse, ProfileUpdateRequest, StructuredProfile
from app.services.profile_builder import build_structured_profile
from app.services.resume_parser import extract_resume_text

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _to_response(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        raw_resume_text=profile.raw_resume_text,
        background_text=profile.background_text,
        behavioral_answers=json.loads(profile.behavioral_answers_json),
        structured_profile=StructuredProfile.model_validate_json(profile.structured_json),
        us_only=profile.us_only,
        preferred_states=json.loads(profile.preferred_states_json),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.post("/upload", response_model=ProfileResponse)
def upload_profile(
    resume_file: UploadFile,
    background_text: str = Form(""),
    behavioral_answers: list[str] = Form([]),
    us_only: bool = Form(True),
    preferred_states: list[str] = Form([]),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    file_bytes = resume_file.file.read()
    try:
        raw_resume_text = extract_resume_text(resume_file.filename or "", file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    structured = build_structured_profile(raw_resume_text, background_text, behavioral_answers)

    profile = db.query(Profile).first()
    if profile is None:
        profile = Profile()
        db.add(profile)

    profile.raw_resume_text = raw_resume_text
    profile.background_text = background_text
    profile.behavioral_answers_json = json.dumps(behavioral_answers)
    profile.structured_json = structured.model_dump_json()
    profile.us_only = us_only
    profile.preferred_states_json = json.dumps(preferred_states)
    db.commit()
    db.refresh(profile)

    return _to_response(profile)


@router.get("", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)) -> ProfileResponse:
    profile = db.query(Profile).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile has been uploaded yet.")
    return _to_response(profile)


@router.put("", response_model=ProfileResponse)
def update_profile(payload: ProfileUpdateRequest, db: Session = Depends(get_db)) -> ProfileResponse:
    profile = db.query(Profile).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile has been uploaded yet.")

    needs_restructure = False
    if payload.background_text is not None:
        profile.background_text = payload.background_text
        needs_restructure = True
    if payload.behavioral_answers is not None:
        profile.behavioral_answers_json = json.dumps(payload.behavioral_answers)
        needs_restructure = True
    if payload.us_only is not None:
        profile.us_only = payload.us_only
    if payload.preferred_states is not None:
        profile.preferred_states_json = json.dumps(payload.preferred_states)

    if needs_restructure:
        structured = build_structured_profile(
            profile.raw_resume_text,
            profile.background_text,
            json.loads(profile.behavioral_answers_json),
        )
        profile.structured_json = structured.model_dump_json()
    db.commit()
    db.refresh(profile)

    return _to_response(profile)
