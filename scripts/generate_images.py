#!/usr/bin/env python3
"""Generate Kenko AI platform images via OpenAI DALL-E 3."""

import argparse
import os
import sys
from pathlib import Path

try:
    import httpx
    from openai import OpenAI
except ImportError:
    print("Run: pip install openai httpx")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# filename, prompt, size
IMAGES = [
    (
        "hero-healthcare.jpg",
        "Photorealistic modern Japanese healthcare clinic with warm lighting, cherry blossoms outside windows, digital AI hologram assistant greeting elderly patient, navy blue and soft pink palette, professional medical photography, welcoming omotenashi atmosphere",
        "1792x1024",
    ),
    (
        "ai-mascot.jpg",
        "Friendly Japanese healthcare AI assistant character design, cute professional female nurse mascot with soft smile, white and navy uniform with sakura pink accents, holding tablet, flat illustration style suitable for medical app, transparent clean background feel, full body character sheet",
        "1024x1024",
    ),
    (
        "feature-ai-chat.jpg",
        "Illustration of patient using smartphone LINE app chatting with AI medical receptionist, speech bubbles with health icons, modern Japanese clinic aesthetic, soft blue and pink colors, clean UI illustration",
        "1792x1024",
    ),
    (
        "feature-rag.jpg",
        "Medical knowledge database visualization, floating documents insurance FAQ treatment guides connected to AI brain, Japanese clinic setting, elegant infographic style illustration",
        "1792x1024",
    ),
    (
        "feature-reservation.jpg",
        "Calendar appointment booking interface with doctor schedule, Google Calendar integration concept, Japanese patient selecting morning slot on tablet, clean healthcare UI illustration",
        "1792x1024",
    ),
    (
        "feature-hospital.jpg",
        "Tokyo map with hospital location pins, ambulance and medical cross icons, patient finding nearest clinic on phone, modern healthcare navigation illustration",
        "1792x1024",
    ),
    (
        "feature-health.jpg",
        "Health timeline dashboard showing mood sleep blood pressure charts, daily wellness check-in, Japanese aesthetic with matcha green and sakura pink accents, modern medical app UI",
        "1792x1024",
    ),
    (
        "usage-line.jpg",
        "Step by step infographic: how to use LINE for medical consultation, 4 steps with icons, Japanese healthcare app onboarding, clean flat design",
        "1792x1024",
    ),
    (
        "usage-booking.jpg",
        "Step by step medical appointment booking flow illustration, patient AI chat to confirmed reservation, 3 steps, Japanese clinic, friendly instructional design",
        "1792x1024",
    ),
    (
        "medical-devices.jpg",
        "Modern medical devices flat lay: stethoscope, digital thermometer, blood pressure monitor, tablet with health app, on clean white surface with subtle Japanese pattern border, professional product photography style",
        "1792x1024",
    ),
    (
        "login-bg.jpg",
        "Serene Japanese healing garden view from clinic window, soft morning light, cherry blossoms, peaceful healthcare atmosphere, blurred background suitable for login page overlay",
        "1792x1024",
    ),
    (
        "hospital-banner.jpg",
        "Panoramic view of modern Japanese hospital exterior with traditional garden elements, blue sky, welcoming entrance, professional architectural photography",
        "1792x1024",
    ),
    (
        "pricing-hero.jpg",
        "Premium healthcare subscription concept, family using health app together, Japanese home setting, warm trustworthy feeling, soft illustration photography hybrid",
        "1792x1024",
    ),
    (
        "dashboard-hero.jpg",
        "Patient health dashboard on large screen in cozy Japanese home, wellness metrics visible, morning tea, calm productive healthcare lifestyle photography",
        "1792x1024",
    ),
    (
        "japanese-pattern.jpg",
        "Seamless traditional Japanese seigaiha wave pattern texture, deep navy blue and gold, elegant minimalist background for website overlay",
        "1792x1024",
    ),
    (
        "symptom-check.jpg",
        "AI symptom assessment illustration, patient describing fever to friendly digital assistant, temperature icon, triage flow diagram, Japanese medical app style",
        "1792x1024",
    ),
]


def generate_one(client: OpenAI, filename: str, prompt: str, size: str, force: bool) -> bool:
    output_path = OUTPUT_DIR / filename
    if output_path.exists() and not force:
        print(f"  skip {filename}")
        return True

    print(f"  generating {filename}...")
    models = ["gpt-image-1", "dall-e-3", "dall-e-2"]
    sizes_dalle2 = {"1792x1024": "1024x1024", "1024x1024": "1024x1024"}

    for model in models:
        try:
            gen_size = sizes_dalle2.get(size, size) if model == "dall-e-2" else size
            if model == "dall-e-2" and gen_size not in ("256x256", "512x512", "1024x1024"):
                gen_size = "1024x1024"

            kwargs = {"model": model, "prompt": prompt, "n": 1}
            if model == "gpt-image-1":
                kwargs["size"] = gen_size if gen_size in ("1024x1024", "1536x1024", "1024x1536") else "1536x1024"
            else:
                kwargs["size"] = gen_size
                kwargs["quality"] = "standard" if model == "dall-e-3" else None
                if kwargs["quality"] is None:
                    del kwargs["quality"]

            response = client.images.generate(**{k: v for k, v in kwargs.items() if v is not None})
            url = response.data[0].url
            b64 = getattr(response.data[0], "b64_json", None)

            if b64:
                import base64
                data = base64.b64decode(b64)
            elif url:
                data = httpx.get(url, timeout=120).content
            else:
                continue

            output_path.write_bytes(data)
            print(f"  saved {output_path} via {model} ({len(data) // 1024}KB)")
            return True
        except Exception as e:
            print(f"  {model} failed: {e}")
            continue

    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--only", nargs="*", help="Generate only these filenames")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("Set OPENAI_API_KEY environment variable")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    targets = IMAGES
    if args.only:
        names = set(args.only)
        targets = [i for i in IMAGES if i[0] in names]

    ok = 0
    for filename, prompt, size in targets:
        if generate_one(client, filename, prompt, size, args.force):
            ok += 1

    print(f"\nDone: {ok}/{len(targets)} images in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
