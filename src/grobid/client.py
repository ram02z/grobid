"""GROBID client module.

Example::

    import
    from grobid.models.form import Form
    from grobid.models.response import Response

    pdf_file = path.Path("<your-academic-article>.pdf")
    with open(pdf_file, "rb") as file:
        form = Form(
            file=File(
                payload=file.read(),
                file_name=pdf_file.name,
                mime_type="application/pdf",
            )
        )
        c = Client(base_url="<base-url>", form=form)
        try:
            c.sync_request().content  # TEI XML file
        except GrobidClientError as e:
            print(e)

"""
from dataclasses import dataclass
from typing import Any

import httpx

from grobid.models.form import Form
from grobid.models.response import Response


class GrobidClientError(BaseException):
    """Exception for Client class."""

    pass


@dataclass
class Client:
    """Client for GROBID's processFulltextDocument endpoint."""

    base_url: str
    form: Form
    timeout: int = 15

    def __build_request(self) -> dict[str, Any]:
        """Build request dictionary."""
        # FIXME: api url is hardcoded
        url = f"{self.base_url}/api/processFulltextDocument"
        return dict(url=url, files=self.form.to_dict(), timeout=self.timeout)

    def __build_response(self, response: httpx.Response) -> Response:
        """Build Response object.

        Raises:
            httpx.HTTPError: if response has 203, 400, 503 or 500 status code
        """
        res = Response(
            status_code=response.status_code,
            content=response.content,
            headers=response.headers,
        )
        res.raise_for_status()

        return res

    async def asyncio_request(self) -> Response:
        """Request client asynchronously.

        Raises:
            GrobidClientError: if httpx.RequestError or httpx.HTTPError is raised
        """
        kwargs = self.__build_request()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(**kwargs)
                return self.__build_response(response)
            except httpx.RequestError as exc:
                raise GrobidClientError(
                    f"An error occurred while requesting {exc.request.url!r}."
                )
            except httpx.HTTPError as exc:
                raise GrobidClientError(exc)

    def sync_request(self) -> Response:
        """Request client synchronously.

        Raises:
            GrobidClientError: if httpx.RequestError or httpx.HTTPError is raised
        """
        kwargs = self.__build_request()
        try:
            response = httpx.post(**kwargs)
            return self.__build_response(response)
        except httpx.RequestError as exc:
            raise GrobidClientError(
                f"An error occurred while requesting {exc.request.url!r}."
            )
        except httpx.HTTPError as exc:
            raise GrobidClientError(exc)
