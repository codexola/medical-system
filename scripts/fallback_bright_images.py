#!/usr/bin/env python3
"""Copy/fallback: map missing bright-* images to existing bright or stock images."""

import shutil
from pathlib import Path

IMG = Path(__file__).resolve().parent.parent / "frontend" / "public" / "images"

# target -> source (first existing wins)
FALLBACKS = {
    "bright-usage-line.jpg": ["bright-feature-chat.jpg", "usage-line.jpg", "feature-ai-chat.jpg"],
    "bright-usage-booking.jpg": ["bright-feature-reservation.jpg", "usage-booking.jpg"],
    "bright-login.jpg": ["bright-dashboard-greeting.jpg", "login-bg.jpg"],
    "bright-hospital.jpg": ["bright-feature-hospital.jpg", "hospital-banner.jpg"],
    "bright-pricing.jpg": ["bright-dashboard-greeting.jpg", "pricing-hero.jpg"],
    "bright-symptom.jpg": ["bright-consultation.jpg", "symptom-check.jpg"],
    "bright-recovery.jpg": ["bright-patient-hope.jpg", "bright-hero.jpg"],
    "bright-bg-pattern.jpg": ["japanese-pattern.jpg"],
    "bright-feature-rag.jpg": ["feature-rag.jpg", "bright-feature-chat.jpg"],
    "bright-feature-health.jpg": ["feature-health.jpg", "bright-dashboard-greeting.jpg"],
    "bright-feature-reservation.jpg": ["feature-reservation.jpg", "bright-feature-chat.jpg"],
    "bright-team.jpg": ["bright-hero.jpg", "bright-doctor.jpg"],
}


def main():
    for target, sources in FALLBACKS.items():
        dest = IMG / target
        if dest.exists():
            continue
        for src_name in sources:
            src = IMG / src_name
            if src.exists():
                shutil.copy2(src, dest)
                print(f"  {target} <- {src_name}")
                break
        else:
            print(f"  MISSING: {target}")


if __name__ == "__main__":
    main()
