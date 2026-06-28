#!/usr/bin/env python3
"""Generate photorealistic slider images for homepage sections."""

import argparse
import base64
import os
import sys
from pathlib import Path

import httpx
from openai import OpenAI

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PHOTO = (
    "Ultra photorealistic professional healthcare photography, real people and real places, "
    "natural soft lighting, sharp detail, Japanese modern clinic or hospital setting, "
    "warm welcoming mood, editorial medical stock photo, absolutely NO text NO numbers "
    "NO logos NO watermarks NO UI overlays"
)

SECTION_PROMPTS: dict[str, list[tuple[str, str, str]]] = {
    "hero": [
        ("slide-hero-01.webp", f"Japanese female doctor in white coat warmly greeting woman patient in bright sunlit clinic lobby with glass windows and plants, {PHOTO}", "1536x1024"),
        ("slide-hero-02.webp", f"Close-up real stethoscope and tablet on desk while Japanese nurse talks kindly to smiling woman patient in examination room, {PHOTO}", "1536x1024"),
        ("slide-hero-03.webp", f"Japanese woman receptionist at modern medical front desk with computer monitor and appointment screen, patient checking in, clean hospital interior, {PHOTO}", "1536x1024"),
        ("slide-hero-04.webp", f"Two Japanese women in consultation room, doctor showing health chart on real tablet device, comfortable private clinic, {PHOTO}", "1536x1024"),
        ("slide-hero-05.webp", f"Wide shot bright Japanese hospital atrium with female medical staff and patients walking, real architecture glass and white walls, {PHOTO}", "1536x1024"),
    ],
    "hope": [
        ("slide-hope-01.webp", f"Japanese woman patient sitting with female doctor after choosing treatment plan, relieved hopeful expression, real consultation room with medical equipment, courageous self-care moment, {PHOTO}", "1536x1024"),
        ("slide-hope-02.webp", f"Japanese woman holding doctor's hand supportively in bright clinic, emotional comfort real people, tissues and water on table, healing decision, {PHOTO}", "1536x1024"),
        ("slide-hope-03.webp", f"Japanese woman reading treatment brochure with nurse explaining options, real pamphlets and clinic wall, empowered patient making health choice, {PHOTO}", "1536x1024"),
        ("slide-hope-04.webp", f"Japanese woman patient smiling softly in sunny clinic waiting area with green plants and wooden chairs, feeling safe to seek care, {PHOTO}", "1536x1024"),
        ("slide-hope-05.webp", f"Japanese female physician kneeling to speak eye-level with anxious woman patient who begins to smile, compassionate real interaction, {PHOTO}", "1536x1024"),
    ],
    "feature-ai": [
        ("slide-feature-ai-01.webp", f"Japanese woman using smartphone health chat app on sofa at home, real phone screen glow, telemedicine AI reception, cozy living room, {PHOTO}", "1536x1024"),
        ("slide-feature-ai-02.webp", f"Japanese woman with earbuds talking to tablet on kitchen table for online symptom consultation, real devices laptop and phone, {PHOTO}", "1536x1024"),
        ("slide-feature-ai-03.webp", f"Close-up woman's hands typing health question on smartphone LINE-style chat, blurred clinic-themed background, real mobile device, {PHOTO}", "1536x1024"),
        ("slide-feature-ai-04.webp", f"Japanese woman at desk video call with female doctor on laptop screen, home office telehealth AI assisted reception, real webcam setup, {PHOTO}", "1536x1024"),
        ("slide-feature-ai-05.webp", f"Young Japanese woman receiving friendly AI health guidance on phone while sitting in bright cafe, real beverage and phone, {PHOTO}", "1536x1024"),
    ],
    "feature-rag": [
        ("slide-feature-rag-01.webp", f"Japanese female doctor showing medical knowledge on large monitor to woman patient, real hospital computer workstation and charts, {PHOTO}", "1536x1024"),
        ("slide-feature-rag-02.webp", f"Japanese woman nurse pointing at anatomy poster and digital tablet with verified medical FAQ content in education room, real medical posters, {PHOTO}", "1536x1024"),
        ("slide-feature-rag-03.webp", f"Library corner in Japanese clinic with woman reading health guide booklet, real bookshelves medical references, soft reading light, {PHOTO}", "1536x1024"),
        ("slide-feature-rag-04.webp", f"Japanese pharmacist woman explaining medication leaflet to customer at real pharmacy counter with shelves of medicine boxes, {PHOTO}", "1536x1024"),
        ("slide-feature-rag-05.webp", f"Doctor and woman patient reviewing printed and digital evidence-based treatment information on tablet together, real clinic desk, {PHOTO}", "1536x1024"),
    ],
    "feature-reservation": [
        ("slide-feature-reservation-01.webp", f"Japanese woman booking doctor appointment on smartphone calendar app at clinic reception desk, real receptionist computer in background, {PHOTO}", "1536x1024"),
        ("slide-feature-reservation-02.webp", f"Close-up real clinic scheduling monitor and woman's hand selecting time slot on tablet at front desk, smart reservation system, {PHOTO}", "1536x1024"),
        ("slide-feature-reservation-03.webp", f"Japanese woman receiving appointment confirmation on phone while standing in modern hospital corridor, real signage and seating, {PHOTO}", "1536x1024"),
        ("slide-feature-reservation-04.webp", f"Female staff at Japanese clinic reception checking digital schedule on dual monitors while patient waits comfortably, real furniture, {PHOTO}", "1536x1024"),
        ("slide-feature-reservation-05.webp", f"Woman using kiosk touchscreen to book medical appointment in bright Japanese hospital entrance, real automatic door and lobby, {PHOTO}", "1536x1024"),
    ],
    "feature-hospital": [
        ("slide-feature-hospital-01.webp", f"Japanese woman using smartphone map app to find hospital while standing on Tokyo street, real urban buildings and crosswalk, {PHOTO}", "1536x1024"),
        ("slide-feature-hospital-02.webp", f"Exterior photograph modern Japanese hospital building glass facade sunny day woman walking toward entrance, real architecture, {PHOTO}", "1536x1024"),
        ("slide-feature-hospital-03.webp", f"Japanese woman comparing nearby clinics on phone screen sitting in taxi, city medical district visible through window, real interior car, {PHOTO}", "1536x1024"),
        ("slide-feature-hospital-04.webp", f"Night photograph illuminated Japanese emergency hospital entrance with woman arriving, real ambulance bay lights and signage without readable text, {PHOTO}", "1536x1024"),
        ("slide-feature-hospital-05.webp", f"Aerial-style street view woman walking path to suburban Japanese clinic surrounded by trees cherry blossoms, real small medical building, {PHOTO}", "1536x1024"),
    ],
    "feature-health": [
        ("slide-feature-health-01.webp", f"Japanese woman recording daily health check on smartwatch and phone app at morning kitchen table, real devices water bottle journal, wellness timeline, {PHOTO}", "1536x1024"),
        ("slide-feature-health-02.webp", f"Woman reviewing sleep and mood charts on tablet health dashboard, real couch home environment soft morning light, {PHOTO}", "1536x1024"),
        ("slide-feature-health-03.webp", f"Japanese woman measuring blood pressure with home monitor writing notes in health diary, real medical device on desk, {PHOTO}", "1536x1024"),
        ("slide-feature-health-04.webp", f"Woman doing gentle stretching while glancing at fitness health app on phone, bright apartment window real yoga mat, {PHOTO}", "1536x1024"),
        ("slide-feature-health-05.webp", f"Close-up woman's hand scrolling health timeline graph on smartphone with medication reminder notification, real phone screen abstract blur, {PHOTO}", "1536x1024"),
    ],
    "feature-subscription": [
        ("slide-feature-subscription-01.webp", f"Japanese mother and adult daughter reviewing family health subscription plan on laptop together in bright living room, real furniture, {PHOTO}", "1536x1024"),
        ("slide-feature-subscription-02.webp", f"Woman at kitchen island entering payment details for medical membership on tablet, real coffee cup modern home, {PHOTO}", "1536x1024"),
        ("slide-feature-subscription-03.webp", f"Japanese care coordinator woman shaking hands with new member patient in clinic lounge membership welcome, real sofas plants, {PHOTO}", "1536x1024"),
        ("slide-feature-subscription-04.webp", f"Three generations Japanese women grandmother mother daughter smiling together holding single health plan brochure, real home interior, {PHOTO}", "1536x1024"),
        ("slide-feature-subscription-05.webp", f"Woman receiving premium health card and welcome packet at clinic front desk, real counter brochures pens computer, {PHOTO}", "1536x1024"),
    ],
    "team": [
        ("slide-team-01.webp", f"Group of smiling Japanese female doctors and nurses in colorful scrubs standing together in bright hospital lobby, real medical team portrait, {PHOTO}", "1536x1024"),
        ("slide-team-02.webp", f"Japanese women healthcare workers in mint blue and coral uniforms welcoming patient at reception, real clinic entrance teamwork, {PHOTO}", "1536x1024"),
        ("slide-team-03.webp", f"Medical team huddle Japanese female surgeons nurses reviewing chart in hospital corridor, real stethoscopes ID badges, {PHOTO}", "1536x1024"),
        ("slide-team-04.webp", f"Pediatric care team Japanese women staff in friendly uniforms with toys in bright children's clinic wing, real facility, {PHOTO}", "1536x1024"),
        ("slide-team-05.webp", f"Wide photo diverse Japanese women clinic staff smiling arms relaxed in sunlit atrium with plants, real hospital building interior, {PHOTO}", "1536x1024"),
    ],
    "guide": [
        ("slide-guide-01.webp", f"Japanese woman registering on health website using laptop at home, real keyboard screen glow signup form blur no readable text, {PHOTO}", "1536x1024"),
        ("slide-guide-02.webp", f"Japanese woman having gentle AI health chat on smartphone sitting on bed morning light, real phone cozy bedroom, onboarding step, {PHOTO}", "1536x1024"),
        ("slide-guide-03.webp", f"Woman in video consultation with doctor on laptop at dining table, real telehealth setup headphones tea cup, {PHOTO}", "1536x1024"),
        ("slide-guide-04.webp", f"Japanese woman confirming medical appointment on phone calendar while leaving clinic building exterior, real street sidewalk, {PHOTO}", "1536x1024"),
        ("slide-guide-05.webp", f"Follow-up scene woman receiving health check message on phone smiling on park bench after visit, real outdoor recovery walk, {PHOTO}", "1536x1024"),
    ],
    "recovery": [
        ("slide-recovery-01.webp", f"Joyful Japanese woman walking in sunny park path after recovery wearing light dress, real trees lens flare hope, {PHOTO}", "1536x1024"),
        ("slide-recovery-02.webp", f"Japanese woman laughing with friend over herbal tea at outdoor cafe terrace celebrating health milestone, real cups table, {PHOTO}", "1536x1024"),
        ("slide-recovery-03.webp", f"Woman stretching arms on seaside boardwalk morning jog recovery wellness, real ocean horizon, {PHOTO}", "1536x1024"),
        ("slide-recovery-04.webp", f"Japanese woman cycling on tree-lined path smiling confident post-treatment vitality, real bicycle helmet, {PHOTO}", "1536x1024"),
        ("slide-recovery-05.webp", f"Woman reading book on garden bench surrounded by hydrangeas peaceful recovery day, real flowers sunshine, {PHOTO}", "1536x1024"),
    ],
}


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
        # Remove legacy png with same stem
        stem = path.stem
        for old in OUTPUT_DIR.glob(f"{stem}.*"):
            if old.suffix.lower() != path.suffix.lower():
                old.unlink(missing_ok=True)
        path.write_bytes(data)
        print(f"  saved {path} ({len(data) // 1024}KB)")
        return True
    except Exception as e:
        print(f"  error {filename}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--section", nargs="*")
    args = parser.parse_args()

    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        print("Set OPENAI_API_KEY")
        sys.exit(1)

    client = OpenAI(api_key=key)
    sections = SECTION_PROMPTS
    if args.section:
        sections = {k: v for k, v in SECTION_PROMPTS.items() if k in args.section}

    total = sum(len(v) for v in sections.values())
    ok = 0
    for name, items in sections.items():
        print(f"\n[{name}]")
        for filename, prompt, size in items:
            if generate_one(client, filename, prompt, size, args.force):
                ok += 1

    print(f"\nDone: {ok}/{total}")


if __name__ == "__main__":
    main()
