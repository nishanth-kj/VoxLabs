from pydantic import BaseModel


class GenerateScriptRequest(BaseModel):
    regenerate: bool = False
    background: bool = True
