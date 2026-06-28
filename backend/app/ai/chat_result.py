from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChatResult:
    reply: str
    hospitals: list[dict] = field(default_factory=list)
    pharmacies: list[dict] = field(default_factory=list)
    specialists: list[dict] = field(default_factory=list)
    suggested_department: Optional[str] = None
    cannot_diagnose: bool = False
    show_hospital_finder: bool = False
    show_pharmacy_finder: bool = False
    plan: Optional[str] = None
    features: list[str] = field(default_factory=list)
