from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


Tier = Literal["1", "2", "3", "drop"]
Confidence = Literal["high", "medium", "low"]
OutreachStatusEnum = Literal[
    "not_contacted",
    "outreach_sent",
    "replied",
    "meeting_scheduled",
    "pitched",
    "due_diligence",
    "committed",
    "passed",
    "do_not_contact",
]


class RawProspect(BaseModel):
    """Output of a source adapter, before enrichment or persistence."""

    full_name: str
    primary_org: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    crunchbase_url: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    source: str
    source_context: dict = Field(default_factory=dict)
    candidate_categories: list[str] = Field(default_factory=list)


class Prospect(BaseModel):
    id: int
    canonical_name: str
    display_name: str
    primary_org: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    email_confidence: Optional[float] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    crunchbase_url: Optional[str] = None
    bio: Optional[str] = None
    candidate_categories: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ClassifierOutput(BaseModel):
    services_thesis_fit: int = Field(ge=1, le=5)
    ai_literacy: int = Field(ge=1, le=5)
    operator_depth: int = Field(ge=1, le=5)
    check_size_fit: int = Field(ge=1, le=5)
    warm_intro_accessibility: int = Field(ge=1, le=5)
    composite_score: int = Field(ge=5, le=25)
    tier: Tier
    rationale: str
    flags: list[str] = Field(default_factory=list)
    confidence: Confidence


class WarmPath(BaseModel):
    path_type: Literal["client", "linkedin_1st", "youtube_sub", "advisor", "mutual_2nd"]
    path_detail: str
    confidence: Confidence


class OutreachStatus(BaseModel):
    status: OutreachStatusEnum = "not_contacted"
    last_touch_at: Optional[datetime] = None
    next_touch_at: Optional[datetime] = None
    notes: Optional[str] = None
