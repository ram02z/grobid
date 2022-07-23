"""Represents a citation, including all the relevant information."""
from dataclasses import dataclass, field

try:
    from mashumaro.mixins.json import DataClassJSONMixin
except ImportError:
    from grobid.models.misc import DataClassJSONMixin


@dataclass
class PageRange(DataClassJSONMixin):
    """Represents the 'to' and 'from' attributes in <biblScope/> XML tag."""

    from_page: int
    to_page: int


@dataclass
class Scope(DataClassJSONMixin):
    """Represents the <biblScope/> XML tag."""

    volume: int | None = None
    pages: PageRange | None = None

    def is_empty(self) -> bool:
        """Return True if the default values are the same."""
        return all(attr is None for attr in self.__dict__.values())


@dataclass
class Date(DataClassJSONMixin):
    """Represents the 'when' attribute in the <date/> XML tag."""

    year: str
    month: str | None = None
    day: str | None = None


@dataclass
class PersonName(DataClassJSONMixin):
    """Represents the <persName/> XML tag."""

    surname: str
    first_name: str | None = None
    # middle_name: str | None = None
    # title: str | None = None

    def to_string(self) -> str:
        """Return string representation of object."""
        if self.first_name:
            return f"{self.first_name} {self.surname}"
        else:
            return f"{self.surname}"


@dataclass
class Affiliation(DataClassJSONMixin):
    """Represents the <affiliation> XML tag."""

    # key: str
    department: str | None = None
    institution: str | None = None
    laboratory: str | None = None
    # address: Address | None = None

    def is_empty(self) -> bool:
        """Return True if the default values are the same."""
        return all(attr is None for attr in self.__dict__.values())


@dataclass
class Author(DataClassJSONMixin):
    """Represents the <author> XML tag."""

    person_name: PersonName
    affiliations: list[Affiliation] = field(default_factory=list)
    email: str | None = None


@dataclass
class CitationIDs(DataClassJSONMixin):
    """Represents the <idno> XML tag."""

    DOI: str | None = None
    arXiv: str | None = None  # noqa: N815
    # issn: str | None = None
    # pii: str | None = None
    # other: str | None = None

    def is_empty(self) -> bool:
        """Return True if the default values are the same."""
        return all(attr is None for attr in self.__dict__.values())


@dataclass
class Citation(DataClassJSONMixin):
    """Represents the <biblStruct> XML tag."""

    title: str
    authors: list[Author] = field(default_factory=list)
    date: Date | None = None
    ids: CitationIDs | None = None
    target: str | None = None
    publisher: str | None = None
    journal: str | None = None
    series: str | None = None
    scope: Scope | None = None
    # meeting: str | None = None
    # phone: str | None = None
