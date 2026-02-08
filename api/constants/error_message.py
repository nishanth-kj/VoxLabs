from enum import Enum

class ErrorMessage(Enum):
    INTERNAL_SERVER_ERROR = (500, "Internal Server Error")
    BAD_REQUEST = (400, "Bad Request")
    NOT_FOUND = (404, "Not Found")
    UNAUTHORIZED = (401, "Unauthorized")
    
    def __init__(self, code, text):
        self.code = code
        self.text = text
