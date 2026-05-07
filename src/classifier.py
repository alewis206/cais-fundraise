"""Phase 1 stub classifier.

Replaced in Phase 2 by an Anthropic-backed implementation. The point of the
stub is to wire the pipeline shape correctly before any LLM cost accrues.
"""

import hashlib
from pathlib import Path
from typing import Optional

from src.config import get_settings
from src.models import ClassifierOutput, Prospect

STUB_MODEL_NAME = "stub-1"


def prompt_version() -> str:
    """Hash of prompts/classifier.md, or 'stub' if it doesn't exist yet."""
    settings = get_settings()
    path: Path = settings.classifier_prompt_path
    if not path.exists():
        return "stub"
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:12]


def classify(prospect: Prospect, *, model: Optional[str] = None) -> ClassifierOutput:
    """Return a fixed mid-tier scoring. Same shape as the real classifier."""
    return ClassifierOutput(
        services_thesis_fit=3,
        ai_literacy=3,
        operator_depth=3,
        check_size_fit=3,
        warm_intro_accessibility=3,
        composite_score=15,
        tier="2",
        rationale="stub classification (Phase 1)",
        flags=["stub"],
        confidence="low",
    )
