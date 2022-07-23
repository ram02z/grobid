# noqa: D100
from dataclasses import dataclass
from typing import Any


@dataclass
class File:
    """Represents the PDF file used as input."""

    payload: bytes
    file_name: str | None = None
    mime_type: str | None = None

    def to_tuple(self) -> tuple[str | None, bytes, str | None]:
        """Return a tuple for httpx mutlipart/form-data encoding."""
        return self.file_name, self.payload, self.mime_type


@dataclass
class Form:
    """Represents form data accepted by GROBID's processFulltextDocument endpoint."""

    file: File
    segment_sentences: bool | None = None
    consolidate_header: int | None = None
    consolidate_citations: int | None = None
    include_raw_citations: bool | None = None
    include_raw_affiliations: bool | None = None
    tei_coordinates: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary for multipart/form-data."""
        form_dict: dict[str, Any] = {}

        form_dict["input"] = self.file.to_tuple()

        if self.segment_sentences:
            form_dict["segmentSentences"] = "1"

        match self.consolidate_header:
            case (0 | 1 | 2):
                form_dict["consolidateHeader"] = str(self.consolidate_header)

        match self.consolidate_citations:
            case (0 | 1 | 2):
                form_dict["consolidateCitations"] = str(self.consolidate_citations)

        if self.include_raw_citations is not None:
            form_dict["includeRawCitations"] = self.include_raw_citations

        if self.include_raw_affiliations is not None:
            form_dict["includeRawAffiliations"] = self.include_raw_affiliations

        if self.tei_coordinates is not None:
            form_dict["teiCoordinates"] = self.tei_coordinates

        return form_dict
