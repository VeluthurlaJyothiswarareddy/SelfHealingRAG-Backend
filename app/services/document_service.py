import logging
from pathlib import Path

from bson import ObjectId

from app.config import get_settings
from app.models.helpers import serialize_document, utcnow
from app.services.chunking_service import chunk_text
from app.services.embedding_service import get_embedding_service
from app.services.extraction_service import extract_text
from app.utils.errors import AppError, NotFoundError

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, db):
        self.db = db
        self.settings = get_settings()

    async def process_upload(
        self,
        filename: str,
        content: bytes,
        user_id: str | None,
        chat_id: str | None,
    ) -> dict:
        max_bytes = self.settings.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise AppError(f"File exceeds maximum size of {self.settings.max_upload_mb}MB", status_code=400)

        text_content = extract_text(filename, content)
        file_type = Path(filename).suffix.lower().lstrip(".")

        doc = {
            "user_id": user_id,
            "chat_id": chat_id,
            "file_name": filename,
            "file_type": file_type,
            "text_content": text_content,
            "upload_time": utcnow(),
        }
        result = await self.db.documents.insert_one(doc)
        document_id = str(result.inserted_id)
        doc["_id"] = result.inserted_id

        chunks = chunk_text(text_content)
        if not chunks:
            raise AppError("Document contains no extractable text", status_code=400)

        embedding_service = get_embedding_service()
        embeddings = await embedding_service.embed_texts(chunks)

        vector_docs = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_docs.append(
                {
                    "document_id": document_id,
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "chunk_text": chunk,
                    "embedding": embedding,
                    "source_file": filename,
                    "chunk_number": idx,
                    "metadata": {
                        "document_id": document_id,
                        "file_type": file_type,
                        "chunk_number": idx,
                    },
                }
            )

        if vector_docs:
            await self.db.vector_documents.insert_many(vector_docs)

        return serialize_document(doc)

    async def list_chat_documents(self, chat_id: str) -> list[dict]:
        cursor = self.db.documents.find({"chat_id": chat_id}).sort("upload_time", -1)
        return [serialize_document(doc) async for doc in cursor]

    async def get_uploaded_filenames(self, chat_id: str) -> list[str]:
        cursor = self.db.documents.find({"chat_id": chat_id}, {"file_name": 1})
        return [doc["file_name"] async for doc in cursor]

    async def delete_document(self, document_id: str, user_id: str | None = None) -> None:
        if not ObjectId.is_valid(document_id):
            raise NotFoundError("Document not found")

        query = {"_id": ObjectId(document_id)}
        if user_id:
            query["user_id"] = user_id

        doc = await self.db.documents.find_one(query)
        if not doc:
            raise NotFoundError("Document not found")

        await self.db.documents.delete_one({"_id": ObjectId(document_id)})
        await self.db.vector_documents.delete_many({"document_id": document_id})
