# noqa: D100
from dataclasses import dataclass, field

from grobid.models.citation import Citation
from grobid.models.json import DataClassJSONMixin
from grobid.models.section import Section


@dataclass
class Table(DataClassJSONMixin):
    """Represents the <figure> XML tag of type table."""

    heading: str
    description: str | None = None
    rows: list[list[str]] = field(default_factory=list)


@dataclass
class Article(DataClassJSONMixin):
    """Represents the scholarly article."""

    bibliography: Citation
    keywords: set[str]
    citations: dict[str, Citation]
    sections: list[Section]
    tables: dict[str, Table]
    abstract: Section | None = None
