from typing import Optional, Any
from fastapi.responses import JSONResponse
from fastapi import status
from constants.response_status import ResponseStatus
from constants.error_message import ErrorMessage
from exceptions.api_exception import ApiException
from utils.logger import logger

class ApiResponse:
    def __init__(
        self,
        data: Optional[Any] = None,
        error: Optional[Any] = None,
        status_code: Optional[int] = None
    ):
        self.data = data
        self.error_obj = error
        self.status_code = status_code
    
    def success(self) -> JSONResponse:
        """
        Returns a successful FastAPI JSONResponse.
        """
        try:
            code = self.status_code or status.HTTP_200_OK
            logger.debug(f"Response Success: status_code={code}")
            return JSONResponse(
                content={
                    "status": ResponseStatus.SUCCESS.code,
                    "data": self.data,
                    "error": None
                },
                status_code=code
            )
        except Exception as e:
            logger.error(f"Error formulating success response: {e}")
            raise

    def error(self) -> JSONResponse:
        """
        Returns an error FastAPI JSONResponse.

        error_obj may be an ApiException (preferred - carries code/message/field),
        an ErrorMessage enum member, a plain Exception, or a raw string.
        """
        try:
            code = self.status_code or status.HTTP_400_BAD_REQUEST
            error_info = None

            if self.error_obj is not None:
                if isinstance(self.error_obj, ApiException):
                    error_info = {
                        "code": self.error_obj.code,
                        "message": self.error_obj.message,
                        "field": self.error_obj.field
                    }
                    code = self.status_code or self.error_obj.code
                elif isinstance(self.error_obj, ErrorMessage):
                    error_info = {
                        "code": self.error_obj.code,
                        "message": self.error_obj.text,
                        "field": None
                    }
                    code = self.status_code or self.error_obj.code
                else:
                    error_info = {
                        "code": self.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": str(self.error_obj),
                        "field": None
                    }
                    if not self.status_code:
                        code = status.HTTP_500_INTERNAL_SERVER_ERROR

            logger.error(f"Response Error: status_code={code}, info={error_info}")
            return JSONResponse(
                content={
                    "status": ResponseStatus.ERROR.code,
                    "data": self.data,
                    "error": error_info
                },
                status_code=code
            )
        except Exception as e:
            logger.critical(f"Critical error in response formatting: {e}", exc_info=True)
            raise
