#!/usr/bin/env python3
"""Seed global documents into MongoDB Atlas vector store."""

import argparse
import asyncio
from pathlib import Path

from app.db.client import get_database, close_client
from app.services.document_service import DocumentService


async def main(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise SystemExit(f"File not found: {file_path}")

    content = path.read_bytes()
    db = get_database()
    service = DocumentService(db)
    result = await service.process_upload(path.name, content, user_id=None, chat_id=None)
    print(f"Seeded global document: {result}")
    await close_client()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed a global document")
    parser.add_argument("file", help="Path to document file")
    args = parser.parse_args()
    asyncio.run(main(args.file))
