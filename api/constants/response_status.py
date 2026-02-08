from enum import Enum

class ResponseStatus(Enum):
    SUCCESS = (1, "Success")
    ERROR = (0, "Error")

    def __init__(self, code, text):
        self.code = code
        self.text = text
