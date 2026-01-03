from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, select
from dotenv import load_dotenv
import os
from .models import MediaType 

load_dotenv()
MEDIA_CONFIG = [
    # (Shortcut, TG_Attr, DB_ID)
    ('gif', 'animation', 1),
    ('mp3', 'audio',     2),
    ('png', 'photo',     3),
    ('mp4', 'video',     4),
    ('sti', 'sticker',   5),
    ('doc', 'document',  6),
]

sql_url = os.getenv("DB_URL")

engine = create_async_engine(sql_url, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

@asynccontextmanager
async def get_session():
   async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await seed_media_types()

async def seed_media_types():
    async with async_session_maker() as session:
        for shortcut, fullcut, db_id in MEDIA_CONFIG:
            result = await session.execute(
                select(MediaType).where(
                    MediaType.short_version == shortcut
                )
            )
            existing = result.scalars().first()
            if not existing:
                mt_data = {
                    "id": db_id,
                    "short_version": shortcut,
                    "tg_version"   : fullcut,
                }
                media_type = MediaType(**mt_data)
                session.add(media_type)
        
        await session.commit()