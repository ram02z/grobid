"""Represents the text sections in a scholarly article."""
from dataclasses import dataclass, field

try:
    from mashumaro.mixins.json import DataClassJSONMixin
except ImportError:
    from grobid.models.misc import DataClassJSONMixin

from enum import Enum


class Marker(str, Enum):
    """Represents the callouts to structures.

    <https://grobid.readthedocs.io/en/latest/training/fulltext/#markers-callouts-to-structures>
    """

    bibr = "bibr"
    figure = "figure"
    table = "table"
    box = "box"
    formula = "formula"


@dataclass
class Ref(DataClassJSONMixin):
    """Represents <ref> XML tag.

    Stores the start and end positions of the reference rather than the text.
    """

    start: int
    end: int
    marker: Marker | None = None
    target: str | None = None


@dataclass
class RefText(DataClassJSONMixin):
    """Represents the <p> XML tag.

    Supports embedded <ref> XML tags.
    """

    text: str
    refs: list[Ref] = field(default_factory=list)

    @property
    def plain_text(self) -> str:
        """Return text without any references.

        Trailing whitespace is removed.
        """
        if len(self.refs) == 0:
            return self.text

        ranges = [(ref.start, ref.end) for ref in self.refs]
        text = ""
        left_bound = 0
        for start, end in ranges:
            text += self.text[left_bound:start].rstrip()
            left_bound = end
        text += self.text[ranges[-1][1] :].rstrip()
        return text


@dataclass
class Section(DataClassJSONMixin):
    """Represents <div> tag with <head> tag."""

    title: str
    paragraphs: list[RefText] = field(default_factory=list)

    def to_str(self) -> str:
        """Return paragraphs in plain text format."""
        text = ""
        for paragraph in self.paragraphs:
            text += paragraph.plain_text

        return text
