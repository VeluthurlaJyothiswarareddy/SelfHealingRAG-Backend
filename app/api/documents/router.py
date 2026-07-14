from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_db
from app.schemas import DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter()


@router.get("/{chat_id}", response_model=list[DocumentResponse])
async def list_documents(chat_id: str, db=Depends(get_db)):
    service = DocumentService(db)
    return await service.list_chat_documents(chat_id)


@router.delete("/{document_id}")
async def delete_document(document_id: str, user_id: str, db=Depends(get_db)):
    service = DocumentService(db)
    await service.delete_document(document_id, user_id)
    return {"detail": "Document deleted"}


@router.post("/admin/upload")
async def admin_upload_global_document(
    file: UploadFile = File(...),
    admin_key: str = Form(...),
    db=Depends(get_db),
):
    from app.config import get_settings

    settings = get_settings()
    expected_key = getattr(settings, "admin_key", None) or "admin-secret"
    if admin_key != expected_key:
        from app.utils.errors import UnauthorizedError
        raise UnauthorizedError("Invalid admin key")

    content = await file.read()
    service = DocumentService(db)
    return await service.process_upload(file.filename, content, user_id=None, chat_id=None)
