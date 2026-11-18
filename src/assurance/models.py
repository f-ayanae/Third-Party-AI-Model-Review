"""Typed records for the review. Ratings and statuses use the SCOPE.md vocabulary."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

BANNED = ("non-compliant", "noncompliant", "audit", "certified", "validated by us", "assurance opinion")


class Status(str, Enum):
    adequate = "Publicly available and adequate"
    inadequate = "Available but inadequate"
    not_public = "Not publicly available"
    not_applicable = "Not applicable"
    not_due = "Not yet due"
    mainkai = "Mainkai-side"


class Rating(str, Enum):
    critical = "Critical"
    high = "High"
    medium = "Medium"
    low = "Low"
    none = "None"


RATING_ORDER = {Rating.critical: 0, Rating.high: 1, Rating.medium: 2, Rating.low: 3, Rating.none: 4}


class Finding(BaseModel):
    id: str
    title: str
    element: str            # crosswalk element or obligation id
    status: Status
    rating: Rating
    basis: str              # "fact" or "assessment"
    observation: str
    why_it_matters: str
    condition: str          # condition or request to close
    owner: str
    deadline: str
    requests: list[str]
    sources: list[str]
    residual_risk: str
    escalation: Optional[str] = None

    @field_validator("observation", "why_it_matters", "condition")
    @classmethod
    def _tone(cls, v: str) -> str:
        low = v.lower()
        for word in BANNED:
            if word in low:
                raise ValueError(f"banned wording '{word}' in finding text")
        if "\u2014" in v:
            raise ValueError("em dash in finding text")
        return v


class CrosswalkRow(BaseModel):
    element: str
    name: str
    core: bool              # core element under outcome rule 3
    anchors: str
    expected: str
    public_evidence: str
    lab: str
    status: Status
    ratable: bool           # can the element be rated on public evidence?
    findings: list[str]
    # Ratability test: a core element is ratable only if some RESULT is visible (a reported figure, a published
    # table, a stated review conclusion), not just the existence of a process. Empty string = no visible result.
    visible_result: str = ""

    @model_validator(mode="after")
    def _ratability_test(self):
        if self.core and self.ratable != bool(self.visible_result.strip()):
            raise ValueError(f"element {self.element}: core elements are ratable if and only if a visible result is recorded")
        return self


class Request(BaseModel):
    id: str
    item: str
    why: str
    test: str
    findings: list[str]
    deadline: str
    owner: str
