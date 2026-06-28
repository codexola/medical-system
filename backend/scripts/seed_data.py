"""Seed initial data for Kenko AI platform."""

import asyncio
import uuid
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import get_settings
from app.database.base import Base
from app.models import AdminUser, Doctor, DoctorSchedule, FAQ, Hospital, KnowledgeDocument
from app.models.media import StoredAsset  # noqa: F401 — register table
from app.services.auth import AuthService

settings = get_settings()

HOSPITALS = [
    {
        "name": "東京大学医学部附属病院",
        "name_en": "The University of Tokyo Hospital",
        "address": "東京都文京区本郷7-3-1",
        "prefecture": "東京都",
        "city": "文京区",
        "latitude": 35.7126,
        "longitude": 139.7622,
        "phone": "03-3815-5411",
        "hospital_type": "general",
        "departments": ["internal_medicine", "cardiology", "neurology", "emergency", "pediatrics"],
        "emergency_available": True,
        "languages": ["ja", "en"],
        "is_partner": True,
        "rating": 4.5,
    },
    {
        "name": "聖路加国際病院",
        "name_en": "St. Luke's International Hospital",
        "address": "東京都中央区明石町9-1",
        "prefecture": "東京都",
        "city": "中央区",
        "latitude": 35.6667,
        "longitude": 139.7733,
        "phone": "03-3541-5151",
        "hospital_type": "general",
        "departments": ["internal_medicine", "cardiology", "dermatology", "emergency", "ophthalmology"],
        "emergency_available": True,
        "languages": ["ja", "en", "zh"],
        "is_partner": True,
        "rating": 4.7,
    },
    {
        "name": "順天堂大学医学部附属順天堂医院",
        "name_en": "Juntendo University Hospital",
        "address": "東京都文京区本郷3-1-3",
        "prefecture": "東京都",
        "city": "文京区",
        "latitude": 35.7083,
        "longitude": 139.7517,
        "phone": "03-3813-3111",
        "hospital_type": "general",
        "departments": ["internal_medicine", "orthopedics", "neurology", "emergency"],
        "emergency_available": True,
        "languages": ["ja", "en"],
        "is_partner": False,
        "rating": 4.3,
    },
    {
        "name": "がん研有明病院",
        "name_en": "National Cancer Center Hospital",
        "address": "東京都江東区有明3-8-31",
        "prefecture": "東京都",
        "city": "江東区",
        "latitude": 35.6400,
        "longitude": 139.7944,
        "phone": "03-3520-0111",
        "hospital_type": "specialty",
        "departments": ["oncology", "internal_medicine"],
        "emergency_available": False,
        "languages": ["ja", "en"],
        "is_partner": True,
        "rating": 4.6,
    },
    {
        "name": "東京歯科大学附属病院",
        "name_en": "Tokyo Dental College Hospital",
        "address": "東京都文京区湯島1-5-45",
        "prefecture": "東京都",
        "city": "文京区",
        "latitude": 35.7089,
        "longitude": 139.7694,
        "phone": "03-5803-5800",
        "hospital_type": "dental",
        "departments": ["dentistry", "oral_surgery"],
        "emergency_available": False,
        "languages": ["ja"],
        "is_partner": False,
        "rating": 4.2,
    },
]

FAQS = [
    {
        "question": "診療時間を教えてください",
        "question_en": "What are your opening hours?",
        "answer": "平日 9:00-18:00、土曜 9:00-13:00 です。日曜・祝日は休診です。",
        "answer_en": "Weekdays 9:00-18:00, Saturday 9:00-13:00. Closed on Sundays and holidays.",
        "category": "hours",
    },
    {
        "question": "保険は使えますか？",
        "question_en": "Can I use health insurance?",
        "answer": "はい、国民健康保険・社会保険・後期高齢者医療制度をご利用いただけます。",
        "answer_en": "Yes, we accept National Health Insurance, Employee Health Insurance, and Late-stage Elderly Healthcare System.",
        "category": "insurance",
    },
    {
        "question": "予約なしで受診できますか？",
        "question_en": "Can I visit without an appointment?",
        "answer": "予約優先制ですが、急な症状の場合はお電話またはLINEでご相談ください。",
        "answer_en": "We operate on an appointment-first basis, but please call or message us via LINE for urgent symptoms.",
        "category": "reservation",
    },
    {
        "question": "英語対応は可能ですか？",
        "question_en": "Is English support available?",
        "answer": "はい、英語対応可能なスタッフがおります。AIアシスタントも英語でご利用いただけます。",
        "answer_en": "Yes, we have English-speaking staff. The AI assistant also supports English.",
        "category": "language",
    },
]

KNOWLEDGE = [
    {
        "title": "クリニック診療時間",
        "category": "hours",
        "content": "当クリニックの診療時間は平日9:00-18:00、土曜9:00-13:00です。日曜・祝日は休診です。急患の場合は119番または最寄りの救急病院をご利用ください。",
    },
    {
        "title": "保険適用について",
        "category": "insurance",
        "content": "国民健康保険、社会保険、後期高齢者医療制度に対応しています。保険証をお持ちください。自費診療（美容皮膚科等）は保険適用外です。",
    },
    {
        "title": "内科診療について",
        "category": "treatment",
        "content": "風邪、発熱、生活習慣病、定期健診など内科全般に対応しています。発熱38度以上が2日以上続く場合、呼吸困難がある場合は早めの受診をお勧めします。",
    },
    {
        "title": "美容皮膚科",
        "category": "treatment",
        "content": "レーザー治療、ボトックス、ヒアルロン酸注入、シミ・しわ治療などを提供しています。初回カウンセリングは無料です。",
    },
    {
        "title": "医療ガイドライン - 発熱",
        "category": "guideline",
        "content": "38度以上の発熱が3日以上続く場合、呼吸困難、意識障害がある場合は速やかに医療機関を受診してください。小児の場合は38度以上で早めの受診を推奨します。",
    },
    {
        "title": "市販薬ガイド - 発熱・風邪",
        "category": "medication",
        "content": "【発熱】アセトアミノフェン（解熱剤）500mgを1日3回まで。イブプロフェンは食後に200mg。38度以上が3日続く場合は受診。【風邪・咳】去痰剤・鎮咳剤、のど飴、抗ヒスタミン薬。3日以上改善しない場合は受診。",
    },
    {
        "title": "市販薬ガイド - 頭痛・腹痛",
        "category": "medication",
        "content": "【頭痛】アセトアミノフェン500mgまたはイブプロフェン200mg（食後）。突然の激しい頭痛は受診。【腹痛】軽症は制酸剤・整腸剤。血便・激痛・24時間以上続く場合は受診。",
    },
    {
        "title": "市販薬ガイド - 皮膚症状",
        "category": "medication",
        "content": "【かゆみ・発疹】抗ヒスタミン薬（ロラタジン等）。患部を清潔に保つ。顔・口の腫れ、全身に広がる発疹はアレルギー疑いで速やかに受診。",
    },
]


async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        staff_accounts = [
            {
                "email": "hiroki.kodan2025@gmail.com",
                "password": "hiroki.kodan2025",
                "name": "開発者",
                "role": "developer",
            },
            {
                "email": "hiroki.kodan20251@gmail.com",
                "password": "hiroki.kodan20251",
                "name": "管理者",
                "role": "admin",
            },
            {
                "email": "admin@kenko-ai.jp",
                "password": "admin123",
                "name": "管理者",
                "role": "admin",
            },
        ]
        for account in staff_accounts:
            existing = await db.execute(select(AdminUser).where(AdminUser.email == account["email"]))
            if not existing.scalar_one_or_none():
                db.add(
                    AdminUser(
                        email=account["email"],
                        password_hash=AuthService.hash_password(account["password"]),
                        name=account["name"],
                        role=account["role"],
                    )
                )

        # Platform settings defaults
        from app.services.platform_settings import PlatformSettingsService

        await PlatformSettingsService(db).ensure_defaults()

        # Hospitals
        for h_data in HOSPITALS:
            existing = await db.execute(select(Hospital).where(Hospital.name == h_data["name"]))
            if not existing.scalar_one_or_none():
                db.add(Hospital(**h_data))

        await db.flush()

        # Doctors
        result = await db.execute(select(Hospital).limit(2))
        hospitals = result.scalars().all()
        for i, hospital in enumerate(hospitals):
            doctor = Doctor(
                hospital_id=hospital.id,
                name="鈴木 健一" if i == 0 else "田中 誠",
                name_en="Dr. Kenichi Suzuki" if i == 0 else "Dr. Makoto Tanaka",
                specialty="internal_medicine",
                specialty_en="Internal Medicine",
                bio="教授・内科部長 | 28年の臨床経験 | 総合内科・生活習慣病",
                languages=["ja", "en"],
            )
            db.add(doctor)
            await db.flush()
            for day in range(5):
                db.add(DoctorSchedule(
                    doctor_id=doctor.id,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(17, 0),
                    slot_duration_minutes=30,
                ))

        # FAQs
        for faq_data in FAQS:
            existing = await db.execute(select(FAQ).where(FAQ.question == faq_data["question"]))
            if not existing.scalar_one_or_none():
                db.add(FAQ(**faq_data))

        # Knowledge documents (text stored in DB)
        for k_data in KNOWLEDGE:
            existing = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.title == k_data["title"]))
            if not existing.scalar_one_or_none():
                db.add(KnowledgeDocument(**k_data))

        # Platform images → database
        from pathlib import Path

        from app.services.seed_media import seed_platform_images

        images_dir = Path(__file__).resolve().parents[2] / "frontend" / "public" / "images"
        image_count = await seed_platform_images(db, images_dir)
        print(f"Stored {image_count} platform images in database")

        await db.commit()
        print("Seed data created successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
