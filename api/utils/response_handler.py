from typing import Optional, Any
from fastapi.responses import JSONResponse
from fastapi import status
from constants.response_status import ResponseStatus
from constants.error_message import ErrorMessage
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
        """
        try:
            code = self.status_code or status.HTTP_400_BAD_REQUEST
            error_info = None
            
            if self.error_obj:
                if isinstance(self.error_obj, ErrorMessage):
                    error_info = {
                        "status": self.error_obj.code,
                        "message": self.error_obj.text
                    }
                    if not self.status_code:
                        code = self.error_obj.code
                else:
                    error_info = {
                        "status": 500,
                        "message": str(self.error_obj)
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
