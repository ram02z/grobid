# noqa: D100
import httpx
import pytest
import respx

from grobid.client import Client, GrobidClientError
from grobid.models.form import File, Form


class TestClient:
    """Unit tests for Client class."""

    import fitz

    with fitz.open(filetype="pdf") as test_pdf:
        # Required to save pdf
        test_pdf.new_page()
        test_obj: bytes = test_pdf.tobytes()

    form = Form(
        file=File(
            payload=test_obj,
            file_name="Test",
            mime_type="application/pdf",
        )
    )

    timeout = 15

    @respx.mock
    def test_sync_request_status_codes(self):
        """Test GROBID's documented HTTP errors synchronously."""
        base_url = "http://validurl:8070"
        c = Client(base_url=base_url, form=self.form, timeout=self.timeout)

        # 203
        respx.mock.post(base_url).mock(return_value=httpx.Response(203))
        with pytest.raises(GrobidClientError, match="Content couldn't be extracted"):
            c.sync_request()

        # 400
        respx.mock.post(base_url).mock(return_value=httpx.Response(400))
        with pytest.raises(
            GrobidClientError,
            match="Wrong request, missing parameters, missing header",
        ):
            c.sync_request()

        # 500
        respx.mock.post(base_url).mock(return_value=httpx.Response(500))
        with pytest.raises(
            GrobidClientError,
            match="Internal service error",
        ):
            c.sync_request()

        # 503
        respx.mock.post(base_url).mock(return_value=httpx.Response(503))
        with pytest.raises(
            GrobidClientError,
            match="Service not available",
        ):
            c.sync_request()

        # 200
        respx.mock.post(base_url).mock(return_value=httpx.Response(200))
        assert c.sync_request().status_code == 200

    def test_sync_invalid_request(self):
        """Test invalid URL synchronously."""
        base_url = "http://invalidurl:8070"
        c = Client(base_url=base_url, form=self.form, timeout=self.timeout)
        with pytest.raises(
            GrobidClientError, match=r"An error occurred while requesting .*"
        ):
            c.sync_request()

    @respx.mock
    @pytest.mark.asyncio
    async def test_asyncio_request_status_codes(self):
        """Test GROBID's documented HTTP errors asynchronously."""
        base_url = "http://validurl:8070"
        c = Client(base_url=base_url, form=self.form, timeout=self.timeout)

        # 203
        respx.mock.post(base_url).mock(return_value=httpx.Response(203))
        with pytest.raises(GrobidClientError, match="Content couldn't be extracted"):
            await c.asyncio_request()

        # 400
        respx.mock.post(base_url).mock(return_value=httpx.Response(400))
        with pytest.raises(
            GrobidClientError,
            match="Wrong request, missing parameters, missing header",
        ):
            await c.asyncio_request()

        # 500
        respx.mock.post(base_url).mock(return_value=httpx.Response(500))
        with pytest.raises(
            GrobidClientError,
            match="Internal service error",
        ):
            await c.asyncio_request()

        # 503
        respx.mock.post(base_url).mock(return_value=httpx.Response(503))
        with pytest.raises(
            GrobidClientError,
            match="Service not available",
        ):
            await c.asyncio_request()

        # 200
        respx.mock.post(base_url).mock(return_value=httpx.Response(200))
        r = await c.asyncio_request()
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_asyncio_invalid_request(self):
        """Test invalid URL asynchronously."""
        base_url = "http://invalidurl:8070"
        c = Client(base_url=base_url, form=self.form, timeout=self.timeout)
        with pytest.raises(
            GrobidClientError, match=r"An error occurred while requesting .*"
        ):
            await c.asyncio_request()
