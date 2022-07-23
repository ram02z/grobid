# noqa: D100
from dataclasses import dataclass

from httpx import Headers, HTTPError


@dataclass
class Response:
    """Represents the response from GROBID's processFulltextDocument endpoint."""

    status_code: int
    content: bytes
    headers: Headers

    def raise_for_status(self):
        """Only considers GROBID's documented status codes as HTTP errors."""
        http_error_msg = ""

        match self.status_code:
            case 203:
                error_msg = "Content couldn't be extracted"
            case 400:
                error_msg = "Wrong request, missing parameters, missing header"
            case 500:
                error_msg = "Internal service error"
            case 503:
                error_msg = "Service not available"
            case _:
                return

        http_error_msg = f"{self.status_code}: {error_msg}"
        raise HTTPError(http_error_msg)
