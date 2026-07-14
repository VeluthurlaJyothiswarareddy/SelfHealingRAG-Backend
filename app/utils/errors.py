class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class EmbeddingError(AppError):
    def __init__(self, message: str = "Failed to process document embeddings"):
        super().__init__(message, status_code=502)


class VectorSearchError(AppError):
    def __init__(self, message: str = "Search temporarily unavailable"):
        super().__init__(message, status_code=503)


class LLMError(AppError):
    def __init__(self, message: str = "AI service timeout"):
        super().__init__(message, status_code=504)


class DatabaseError(AppError):
    def __init__(self, message: str = "Database service unavailable"):
        super().__init__(message, status_code=503)
