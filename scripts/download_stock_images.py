#!/usr/bin/env python3
"""Download curated healthcare images from Unsplash (free to use)."""

import httpx
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "frontend" / "public" / "images"
OUTPUT.mkdir(parents=True, exist_ok=True)

# Unsplash direct URLs (healthcare / medical themed)
STOCK = {
    "hero-healthcare.jpg": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1792&q=80",
    "login-bg.jpg": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1792&q=80",
    "hospital-banner.jpg": "https://images.unsplash.com/photo-1586773866498-0402e229bb93?w=1792&q=80",
    "medical-devices.jpg": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1792&q=80",
    "feature-health.jpg": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=1792&q=80",
    "feature-hospital.jpg": "https://images.unsplash.com/photo-1587351021759-3e566b6f9755?w=1792&q=80",
    "feature-ai-chat.jpg": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1792&q=80",
    "feature-reservation.jpg": "https://images.unsplash.com/photo-1629909613654-28e377c37b09?w=1792&q=80",
    "feature-rag.jpg": "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=1792&q=80",
    "usage-line.jpg": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=1792&q=80",
    "usage-booking.jpg": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=1792&q=80",
    "pricing-hero.jpg": "https://images.unsplash.com/photo-1576765608535-5f04a1e0e98a?w=1792&q=80",
    "dashboard-hero.jpg": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1792&q=80",
    "symptom-check.jpg": "https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf?w=1792&q=80",
    "ai-mascot.jpg": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=1024&q=80",
}


def main():
    for name, url in STOCK.items():
        path = OUTPUT / name
        print(f"Downloading {name}...")
        try:
            r = httpx.get(url, timeout=60, follow_redirects=True)
            r.raise_for_status()
            path.write_bytes(r.content)
            print(f"  OK {len(r.content) // 1024}KB")
        except Exception as e:
            print(f"  FAIL: {e}")


if __name__ == "__main__":
    main()
