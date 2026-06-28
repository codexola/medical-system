#!/usr/bin/env python3
"""Generate bright, hopeful healthcare images for Kenko AI."""

import argparse
import base64
import os
import sys
from pathlib import Path

import httpx
from openai import OpenAI

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BRIGHT_STYLE = (
    "Bright cheerful lighting, soft pastel colors, warm sunshine atmosphere, "
    "high key photography, optimistic hopeful mood, clean modern Japanese healthcare, "
    "professional but warm and welcoming, 4K quality"
)

IMAGES = [
    (
        "bright-hero.jpg",
        f"Smiling young Japanese female doctor in elegant light blue medical coat warmly greeting a smiling Japanese woman patient in soft coral blouse, bright sunlit modern clinic with large windows white walls cherry blossoms outside, hopeful healing atmosphere, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-mascot.jpg",
        f"Portrait of cheerful Japanese female healthcare assistant character, warm genuine smile, elegant light mint green and soft pink uniform, holding tablet, bright soft studio lighting white background, friendly trustworthy, {BRIGHT_STYLE}",
        "1024x1024",
    ),
    (
        "bright-dashboard-greeting.jpg",
        f"Smiling Japanese woman in bright yellow cardigan opening health app on phone at sunny breakfast table, morning light through window plants flowers, feeling hopeful about her health journey, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-doctor.jpg",
        f"Confident smiling Japanese female doctor in pristine white coat and soft sky blue scrubs, stethoscope, standing in bright airy hospital corridor with natural light, reassuring kind expression, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-patient-hope.jpg",
        f"Smiling Japanese woman patient in soft peach sweater looking hopeful and relieved after good medical news, bright clinic waiting area with plants, warm encouraging atmosphere you can overcome illness, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-consultation.jpg",
        f"Kind Japanese female doctor in light blue attire gently consulting smiling female patient across bright desk, tablet showing health chart, trust and care, sunlit consultation room, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-team.jpg",
        f"Diverse team of smiling Japanese healthcare workers in fine bright colored uniforms mint blue coral white, standing together in bright hospital lobby, teamwork hope healing, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-feature-chat.jpg",
        f"Smiling Japanese woman using smartphone LINE app for friendly AI health chat at home, bright living room soft colors, comfortable reassuring telehealth, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-feature-rag.jpg",
        f"Bright medical information illustration, smiling female nurse pointing at clear health guide on bright screen, soft blue pink palette, easy to understand caring, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-feature-reservation.jpg",
        f"Smiling Japanese woman booking doctor appointment on bright tablet calendar app, elegant light clothing, sunny clinic reception, smooth easy process, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-feature-hospital.jpg",
        f"Smiling Japanese woman finding hospital on bright phone map app, standing on sunny Tokyo street, helpful navigation to care, soft cheerful colors, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-feature-health.jpg",
        f"Smiling Japanese woman recording wellness check-in on bright health app, mood sleep vitals charts in soft mint and peach colors, positive self-care morning routine, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-usage-line.jpg",
        f"Bright infographic style: smiling Japanese woman following 3 easy steps on LINE for health consultation, soft pastel icons mint coral sky blue, friendly onboarding, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-usage-booking.jpg",
        f"Bright step illustration smiling patient booking appointment with kind AI assistant, confirmed reservation celebration, soft cheerful healthcare app, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-login.jpg",
        f"Serene bright Japanese healing garden with cherry blossoms morning sunshine seen through clinic window, soft warm light peaceful hope renewal, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-hospital.jpg",
        f"Bright modern Japanese hospital entrance with smiling female receptionist in elegant light blue uniform welcoming patient, sunny day green plants, welcoming omotenashi, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-pricing.jpg",
        f"Happy Japanese family mother daughter smiling using health app together in bright living room, soft warm colors hope for family wellness, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-symptom.jpg",
        f"Kind Japanese female doctor gently asking about symptoms to smiling reassured patient, bright examination room soft colors, caring triage not scary, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-recovery.jpg",
        f"Joyful smiling Japanese woman walking outdoors in sunshine after recovery, light floral dress, cherry blossoms, symbol of overcoming illness hope new beginning, {BRIGHT_STYLE}",
        "1536x1024",
    ),
    (
        "bright-bg-pattern.jpg",
        f"Very subtle bright soft watercolor pattern light sky blue and peach petals, seamless gentle background texture for healthcare website, extremely light airy, {BRIGHT_STYLE}",
        "1536x1024",
    ),
]


def generate_one(client: OpenAI, filename: str, prompt: str, size: str, force: bool) -> bool:
    path = OUTPUT_DIR / filename
    if path.exists() and not force:
        print(f"  skip {filename}")
        return True

    print(f"  generating {filename}...")
    valid = ("1024x1024", "1536x1024", "1024x1536")
    gen_size = size if size in valid else "1536x1024"

    try:
        response = client.images.generate(model="gpt-image-1", prompt=prompt, size=gen_size, n=1)
        b64 = getattr(response.data[0], "b64_json", None)
        url = response.data[0].url
        if b64:
            data = base64.b64decode(b64)
        elif url:
            data = httpx.get(url, timeout=180).content
        else:
            return False
        path.write_bytes(data)
        print(f"  saved {path} ({len(data) // 1024}KB)")
        return True
    except Exception as e:
        print(f"  error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()

    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        print("Set OPENAI_API_KEY")
        sys.exit(1)

    client = OpenAI(api_key=key)
    targets = IMAGES
    if args.only:
        names = set(args.only)
        targets = [i for i in IMAGES if i[0] in names]

    ok = sum(generate_one(client, f, p, s, args.force) for f, p, s in targets)
    print(f"\nDone: {ok}/{len(targets)}")


if __name__ == "__main__":
    main()
