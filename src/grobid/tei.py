"""GROBID annotation guidelines compliant parser module.

Example::

    from grobid.tei import Parser

    xml_content: bytes
    parser = Parser(xml_content)
    article = parser.parse()
    article.to_json()  # throws RuntimeError if extra require 'json' not installed

"""
import string
from typing import Generator

from bs4 import BeautifulSoup
from bs4.element import NavigableString, PageElement, Tag

from grobid.models import (
    Affiliation,
    Article,
    Author,
    Citation,
    CitationIDs,
    Date,
    PageRange,
    PersonName,
    Ref,
    RefText,
    Scope,
    Section,
    Table,
)
from grobid.models.section import Marker


class GrobidParserError(BaseException):
    """Exception for Parser class."""

    pass


# NOTE: shouldn't TEI methods be static?
class Parser:
    """Methods used to parse TEI XML into serializable objects."""

    soup: BeautifulSoup

    def __init__(self, stream: bytes) -> None:
        """TEI class constructor.

        Args:
            stream: XML bytes
        """
        self.soup = BeautifulSoup(stream, "lxml-xml")

    def __parse_date(self, date: str) -> Date | None:
        # Naive ISO 8601 date parser
        tokens = date.split(sep="-")
        tokens = list(filter(None, tokens))

        match len(tokens):
            case 0:
                return
            case 1:
                year = tokens[0]
                return Date(year)
            case 2:
                year, month = tokens
                return Date(year, month)
            case _:
                year, month, day = tokens[0:3]
                return Date(year, month, day)

    def __text_and_refs(
        self,
        source_tag: Tag,
    ) -> Generator[PageElement, str, None]:
        # Generator with both NavigableStrings and ref Tags
        for descendant in source_tag.descendants:
            descendant_type = type(descendant)
            if descendant_type is Tag and descendant.name == "ref":  # type: ignore
                yield descendant
            elif descendant_type is NavigableString:
                yield descendant

    def parse(self) -> Article:
        """Attempt to parse the XML into Article object.

        Parsing is strict (fails if fields are missing)

        Returns:
            Article object

        Raises:
            GrobidParserError: Article could not be parsed
        """
        body = self.soup.body

        if not isinstance(body, Tag):
            raise GrobidParserError("Missing body")

        abstract: Section | None = self.section(self.soup.abstract, title="Abstract")

        sections: list[Section] = []
        for div in body.find_all("div"):
            if (section := self.section(div)) is not None:
                sections.append(section)

        tables: dict[str, Table] = {}
        for table_tag in body.find_all("figure", {"type": "table"}):
            if isinstance(table_tag, Tag):
                if "xml:id" in table_tag.attrs:
                    name = table_tag.attrs["xml:id"]
                    if (table_obj := self.table(table_tag)) is not None:
                        tables[name] = table_obj

        if (source := self.soup.find("sourceDesc")) is None:
            raise GrobidParserError("Missing source description")

        biblstruct_tag = source.find("biblStruct")
        if not isinstance(biblstruct_tag, Tag):
            raise GrobidParserError("Missing bibliography")

        bibliography = self.citation(biblstruct_tag)
        keywords = self.keywords(self.soup.keywords)

        listbibl_tag = self.soup.find("listBibl")
        if not isinstance(listbibl_tag, Tag):
            raise GrobidParserError("Missing citations")

        citations = {}
        for struct_tag in listbibl_tag.find_all("biblStruct"):
            if isinstance(struct_tag, Tag):
                name = struct_tag.get("xml:id")
                citations[name] = self.citation(struct_tag)

        return Article(
            abstract=abstract,
            sections=sections,
            tables=tables,
            bibliography=bibliography,
            keywords=keywords,
            citations=citations,
        )

    def citation(self, source_tag: Tag) -> Citation:
        """Parse citation.

        Args:
            source_tag : biblStruct XML Tag

        Returns:
            Citation object
        """
        title = self.title(source_tag, attrs={"type": "main"})
        if not title:
            # Use meeting as the main title
            title = self.title(source_tag, attrs={"level": "m"})
        citation = Citation(title=title)
        citation.authors = self.authors(source_tag)
        ids = CitationIDs(
            DOI=self.idno(source_tag, attrs={"type": "DOI"}),
            arXiv=self.idno(source_tag, attrs={"type": "arXiv"}),
        )
        if not ids.is_empty():
            citation.ids = ids

        citation.date = self.date(source_tag)
        citation.target = self.target(source_tag)
        citation.publisher = self.publisher(source_tag)
        citation.scope = self.scope(source_tag)
        if journal := self.title(source_tag, attrs={"level": "j"}):
            if journal != citation.title:
                citation.journal = journal
        if series := self.title(source_tag, attrs={"level": "s"}):
            if series != citation.title:
                citation.series = series

        return citation

    def title(self, source_tag: Tag | None, attrs: dict[str, str] = {}) -> str:
        """Parse title tag text.

        Args:
            source_tag : XML tag
            attrs: dictionary of filters on attribute values. Default is empty dict.

        Returns:
            Text in title tag if it exists
        """
        title: str = ""
        if source_tag is not None:
            if (title_tag := source_tag.find("title", attrs=attrs)) is not None:
                title = title_tag.text

        return title

    def target(self, source_tag: Tag | None) -> str | None:
        """Parse ptr tag target.

        Args:
            source_tag : XML tag

        Returns:
            Target location in ptr tag if it exists
        """
        if source_tag is not None:
            if (ptr_tag := source_tag.ptr) is not None:
                if "target" in ptr_tag.attrs:
                    # TODO: validate URL
                    return ptr_tag.attrs["target"]

    def idno(self, source_tag: Tag | None, attrs: dict[str, str] = {}) -> str | None:
        """Parse idno tag.

        Args:
            source_tag : XML tag
            attrs: dictionary of filters on attribute values. Default is empty dict.

        Returns:
            Text content of idno_tag if it exists
        """
        if source_tag is not None:
            if (idno_tag := source_tag.find("idno", attrs=attrs)) is not None:
                return idno_tag.text or None

    def keywords(self, source_tag: Tag | None) -> set[str]:
        """Parse all term tags.

        Args:
            source_tag : XML tag

        Returns:
            Set of keywords
        """
        keywords: set[str] = set()

        if source_tag is not None:
            for term_tag in source_tag.find_all("term"):
                if term_tag.text:
                    if clean_keyword := self.clean_title_string(term_tag.text):
                        keywords.add(clean_keyword)

        return keywords

    def publisher(self, source_tag: Tag | None) -> str | None:
        """Parse publisher tag text.

        Args:
            source_tag : XML tag

        Returns:
            Text in publisher tag if it exists
        """
        if source_tag is not None:
            if (publisher_tag := source_tag.find("publisher")) is not None:
                return publisher_tag.text or None

    def date(self, source_tag: Tag | None) -> Date | None:
        """Parse date tag.

        Args:
            source_tag : XML tag

        Returns:
            Date object if date tag is valid
        """
        if source_tag is not None:
            if (date_tag := source_tag.date) is not None:
                if "when" in date_tag.attrs:
                    when = date_tag.attrs["when"]

                    return self.__parse_date(when)

    def scope(self, source_tag: Tag | None) -> Scope | None:
        """Parse all biblScope tags.

        Args:
            source_tag : XML tag

        Returns:
            Scope object if biblScope tags exist
        """
        if source_tag is not None:
            scope = Scope()
            for scope_tag in source_tag.find_all("biblScope"):
                match scope_tag.attrs["unit"]:
                    case "page":
                        try:
                            if "from" in scope_tag.attrs and "to" in scope_tag.attrs:
                                from_page = int(scope_tag["from"])
                                to_page = int(scope_tag["to"])
                            elif scope_tag.text:
                                from_page = int(scope_tag.text)
                                to_page = from_page
                            else:
                                continue

                            scope.pages = PageRange(
                                from_page=from_page, to_page=to_page
                            )
                        except ValueError:
                            continue
                    case "volume":
                        try:
                            volume = int(scope_tag.text)
                            scope.volume = volume
                        except ValueError:
                            continue

            if not scope.is_empty():
                return scope

    def authors(self, source_tag: Tag | None) -> list[Author]:
        """Parse all author tags.

        Args:
            source_tag : XML tag

        Returns:
            List of Author objects
        """
        authors: list[Author] = []
        if source_tag is not None:
            for author in source_tag.find_all("author"):
                author_obj: Author | None = None
                if (persname := author.find("persName")) is not None:
                    if (surname_tag := persname.find("surname")) is not None:
                        person_name = PersonName(surname=surname_tag.text)
                        if forename_tag := persname.find("forename", {"type": "first"}):
                            person_name.first_name = forename_tag.text

                        author_obj = Author(person_name=person_name)
                        authors.append(author_obj)

                        if email_tag := author.find("email"):
                            author_obj.email = email_tag.text

                        for affiliation_tag in author.find_all("affiliation"):
                            affiliation_obj = Affiliation()
                            for orgname_tag in affiliation_tag.find_all("orgName"):
                                match orgname_tag["type"]:
                                    case "institution":
                                        affiliation_obj.institution = orgname_tag.text
                                    case "department":
                                        affiliation_obj.department = orgname_tag.text
                                    case "laboratory":
                                        affiliation_obj.laboratory = orgname_tag.text

                            if not affiliation_obj.is_empty():
                                author_obj.affiliations.append(affiliation_obj)

        return authors

    def section(self, source_tag: Tag | None, title: str = "") -> Section | None:
        """Parse div tag with head tag.

        Capitalizes title if not already.

        Section can have an empty body.

        Args:
            source_tag : XML tag
            title: forces the parsing of the section. Default is empty string (false)

        Returns:
            Section object if valid section.
        """
        if source_tag is not None:
            head = source_tag.find("head")
            if isinstance(head, Tag):
                head_text: str = head.get_text()
                if "n" in head.attrs or head_text[0] in string.ascii_letters:
                    if head_text.isupper() or head_text.islower():
                        head_text = head_text.capitalize()

                section = Section(title=head_text)
            elif title:
                section = Section(title=title)
            else:
                return

            paragraphs = source_tag.find_all("p")
            for p in paragraphs:
                if p and (ref_text := self.ref_text(p)) is not None:
                    section.paragraphs.append(ref_text)

            return section

    def ref_text(self, source_tag: Tag | None) -> RefText | None:
        """Parse text with ref tags.

        Args:
            source_tag : XML tag

        Returns:
            RefText object
        """
        if source_tag is not None:
            text_and_refs = self.__text_and_refs(source_tag)
            start = 0
            ref_text = RefText(text="")
            for el in text_and_refs:
                start = len(ref_text.text)
                if isinstance(el, Tag):
                    end = start + len(el.text)
                    ref = Ref(start=start, end=end)
                    if (el_type := el.attrs.get("type")) is not None:
                        try:
                            ref.marker = Marker[el_type]
                        except KeyError:
                            pass

                    # NOTE: if target[0] is '#', check for citation
                    if (el_target := el.attrs.get("target")) is not None:
                        ref.target = el_target

                    ref_text.refs.append(ref)
                else:
                    ref_text.text += str(el)

            return ref_text

    def table(self, source_tag: Tag | None) -> Table | None:
        """Parse <figure> with table type.

        Args:
            source_tag : XML tag

        Returns:
            Table object
        """
        if source_tag is not None:
            if (head_tag := source_tag.find("head")) is not None:
                if head_text := head_tag.get_text():
                    table = Table(heading=head_text)
                    if (desc_tag := source_tag.find("figDesc")) is not None:
                        table.description = desc_tag.get_text()
                    rows = source_tag.find_all("row")
                    for row in rows:
                        row_list = []
                        for cell in row.find_all("cell"):
                            row_list.append(cell.get_text())
                        table.rows.append(row_list)

                    return table

    @staticmethod
    def clean_title_string(s: str) -> str:
        """Remove non-alpha leading characters from string.

        Args:
            s : title string

        Returns:
            Clean title string
        """
        s = s.strip()

        while s and not s[0].isalpha():
            s = s[1:]

        return s.capitalize()
