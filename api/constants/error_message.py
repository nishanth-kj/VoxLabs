from .baseEnum import BaseEnum

class ErrorMessage(BaseEnum):
    INTERNAL_SERVER_ERROR = (500, "Internal Server Error")
    BAD_REQUEST = (400, "Bad Request")
    NOT_FOUND = (404, "Not Found")
    UNAUTHORIZED = (401, "Unauthorized")
    VALIDATION_ERROR = (422, "Validation Error")
    
    def __init__(self, code, text):
        self.code = code
        self.text = text
