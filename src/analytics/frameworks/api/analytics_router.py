"""Router base del BC Analytics — sin endpoints todavía (los agrega `US-4.1.2`)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])
