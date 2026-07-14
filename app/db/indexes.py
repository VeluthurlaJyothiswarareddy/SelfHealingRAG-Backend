VECTOR_INDEX_DEFINITION = {
    "name": "vector_index",
    "type": "vectorSearch",
    "definition": {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1536,
                "similarity": "cosine",
            },
            {"type": "filter", "path": "user_id"},
            {"type": "filter", "path": "chat_id"},
            {"type": "filter", "path": "source_file"},
        ]
    },
}


async def ensure_indexes(db) -> None:
    await db.users.create_index("email", unique=True)
    await db.chats.create_index([("user_id", 1), ("updated_at", -1)])
    await db.messages.create_index([("chat_id", 1), ("created_at", 1)])
    await db.documents.create_index([("user_id", 1), ("chat_id", 1)])
    await db.vector_documents.create_index("document_id")
    await db.vector_documents.create_index([("user_id", 1), ("chat_id", 1)])
