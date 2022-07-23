"""Unit tests for the TEI class."""
import pytest

from grobid.models import (
    Affiliation,
    Article,
    Author,
    Citation,
    CitationIDs,
    Date,
    Marker,
    PageRange,
    PersonName,
    Ref,
    RefText,
    Scope,
    Section,
    Table,
)
from grobid.tei import GrobidParserError, Parser


class TestParse:
    """Unit tests for parse function."""

    @staticmethod
    def build_xml(article: Article) -> bytes:
        """Create XML from Article object."""
        tei_tags: list[bytes] = [b"<TEI>"]

        tei_tags.append(b"<sourceDesc>")
        tei_tags.append(TestCitation.build_xml(article.bibliography))
        tei_tags.append(b"</sourceDesc>")

        tei_tags.append(b"<body>")
        for section in article.sections:
            tei_tags.append(TestSection.build_xml(section))
        for xml_id, table in article.tables.items():
            tei_tags.append(TestTable.build_xml(table, xml_id))
        tei_tags.append(b"</body>")

        tei_tags.append(b"<listBibl>")
        for xml_id, citation in article.citations.items():
            tei_tags.append(TestCitation.build_xml(citation, xml_id=xml_id))
        tei_tags.append(b"</listBibl>")

        tei_tags.append(b"</TEI>")

        return b"".join(tei_tags)

    def test_no_body(self):  # noqa: D102
        xml = b"<TEI></TEI>"

        with pytest.raises(GrobidParserError, match="Missing body"):
            Parser(xml).parse()

    def test_no_sourcedesc(self):  # noqa: D102
        xml = b"<TEI><body></body></TEI>"

        with pytest.raises(GrobidParserError, match="Missing source description"):
            Parser(xml).parse()

    def test_no_biblstruct(self):  # noqa: D102
        xml = b"<TEI><sourceDesc></sourceDesc><body></body></TEI>"

        with pytest.raises(GrobidParserError, match="Missing bibliography"):
            Parser(xml).parse()

    def test_no_listbibl(self):  # noqa: D102
        xml = b"""
        <TEI><sourceDesc><biblStruct></biblStruct></sourceDesc><body></body></TEI>
        """

        with pytest.raises(GrobidParserError, match="Missing citations"):
            Parser(xml).parse()

    def test_valid_article(self):  # noqa: D102
        article = Article(
            bibliography=Citation(
                title="Test",
                authors=[
                    Author(
                        PersonName("Doe", "John"),
                    )
                ],
            ),
            keywords=set(),
            tables=dict(
                test=Table(
                    heading="Test", description="Lorem Ipsum", rows=[["Foo", "Bar"]]
                )
            ),
            sections=[Section("Introduction", [RefText("Lorem Ipsum")])],
            citations=dict(
                test=Citation(
                    title="Test2",
                    authors=[Author(PersonName("Doe", "Jane"))],
                )
            ),
        )

        tei = Parser(TestParse.build_xml(article))

        assert tei.parse() == article


class TestTitle:
    """Unit tests for the title function."""

    def test_valid_tag(self):  # noqa: D102
        title = "Test"
        xml = bytes(f"<title>{title}</title>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.title(tei.soup) == title

    def test_valid_title_attr(self):  # noqa: D102
        title = "Test"
        xml = bytes(
            f"<div><title><Invalid</title><title type='main'>{title}</></div>",
            encoding="utf-8",
        )
        tei = Parser(xml)

        assert tei.title(tei.soup, attrs={"type": "main"}) == title

    def test_invalid_tag(self):  # noqa: D102
        xml = b"<nottitle>Invalid</nottitle>"
        tei = Parser(xml)

        # NOTE: should it return empty string over None?
        assert tei.title(tei.soup) == ""


class TestTarget:
    """Unit tests for the target function."""

    def test_valid_tag(self):  # noqa: D102
        target = "http://avalidtarget.org"
        xml = bytes(f"<ptr target='{target}'/>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.target(tei.soup) == target

    def test_no_target(self):  # noqa: D102
        xml = b"<ptr/>"
        tei = Parser(xml)

        assert tei.target(tei.soup) is None

    def test_empty_tag(self):  # noqa: D102
        xml = b"<ptr/>"
        tei = Parser(xml)

        assert tei.target(tei.soup) is None


class TestIdno:
    """Unit tests for the idno function."""

    def test_valid_tag(self):  # noqa: D102
        idno = "test"
        xml = bytes(f"<idno>{idno}</idno>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.idno(tei.soup) == idno

    def test_valid_idno_attr(self):
        """Checks if attribute dictionary search is prioritised over empty tags."""
        idno = "test"
        type_ = "DOI"
        xml = bytes(
            f"<div><idno>Invalid</idno><idno type='{type_}'>{idno}</idno></div>",
            encoding="utf-8",
        )
        tei = Parser(xml)

        assert tei.idno(tei.soup, attrs={"type": type_}) == idno

    def test_empty_tag(self):  # noqa: D102
        xml = bytes("<idno></idno>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.idno(tei.soup) is None


class TestPublisher:
    """Unit tests for the publisher function."""

    def test_valid_tag(self):  # noqa: D102
        publisher = "Foo Bar"
        xml = bytes(f"<publisher>{publisher}</publisher>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.publisher(tei.soup) == publisher

    def test_empty_tag(self):  # noqa: D102
        xml = bytes("<publisher></publisher>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.publisher(tei.soup) is None


class TestKeywords:
    """Unit tests for the keywords function."""

    def test_valid_tags(self):  # noqa: D102
        keywords = {"Keywords", "Tags"}  # keywords are nouns
        term_tags: list[bytes] = [b"<keywords>"]
        for keyword in keywords:
            term_tags.append(bytes(f"<term>{keyword}</term>", encoding="utf-8"))

        term_tags.append(b"</keywords>")

        xml = b"".join(term_tags)
        tei = Parser(xml)

        assert tei.keywords(tei.soup) == keywords

    def test_empty_tag(self):  # noqa: D102
        xml = b"<term></term>"
        tei = Parser(xml)

        assert tei.keywords(tei.soup) == set()


class TestDate:
    """Unit tests for the date function."""

    def test_valid_tag_year(self):
        """Date with only the year."""
        year = "2022"
        date = Date(year=year)
        xml = bytes(f"<date when='{year}'/>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.date(tei.soup) == date

    def test_valid_tag_year_month(self):
        """Date with only the year and month."""
        year = "2022"
        month = "05"
        date = Date(year=year, month=month)
        xml = bytes(f"<date when='{year}-{month}'/>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.date(tei.soup) == date

    def test_valid_tag_full_date(self):
        """Date with year, month and day."""
        year = "2022"
        month = "05"
        day = "03"
        date = Date(year=year, month=month, day=day)
        xml = bytes(f"<date when='{year}-{month}-{day}'/>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.date(tei.soup) == date

    def test_empty_tag(self):  # noqa: D102
        xml = b"<date when=''/>"
        tei = Parser(xml)

        assert tei.date(tei.soup) is None


class TestCitation:
    """Unit tests for the citation function."""

    @staticmethod
    def build_xml(citation: Citation, xml_id: str | None = None) -> bytes:
        """Create XML from Citation object."""
        bibl_tags: list[bytes] = []
        if xml_id:
            bibl_tags.append(bytes(f"<biblStruct xml:id='{xml_id}'>", encoding="utf-8"))
        else:
            bibl_tags.append(b"<biblStruct>")

        bibl_tags.append(
            bytes(f"<title type='main'>{citation.title}</title>", encoding="utf-8")
        )

        bibl_tags.append(TestAuthors.build_xml(citation.authors))

        if citation.ids is not None:
            for k, v in citation.ids.__dict__.items():
                if v is None:
                    continue
                bibl_tags.append(
                    bytes(f"<idno type='{k}'>{v}</idno>", encoding="utf-8")
                )

        if citation.scope is not None:
            for k, v in citation.scope.__dict__.items():
                if v is None:
                    continue
                bibl_tags.append(
                    bytes(f"<biblScope unit='{k}'>{v}</biblScope>", encoding="utf-8")
                )

        if citation.target:
            bibl_tags.append(
                bytes(f"<ptr target='{citation.target}' />", encoding="utf-8")
            )

        if citation.publisher:
            bibl_tags.append(
                bytes(f"<publisher>{citation.publisher}</publisher>", encoding="utf-8")
            )

        if citation.series:
            bibl_tags.append(
                bytes(f"<title level='s'>{citation.series}</title>", encoding="utf-8")
            )

        if citation.journal:
            bibl_tags.append(
                bytes(f"<title level='j'>{citation.journal}</title>", encoding="utf-8")
            )

        bibl_tags.append(b"</biblStruct>")

        return b"".join(bibl_tags)

    def test_valid_tags(self):  # noqa: D102
        citation = Citation(
            title="Test",
            authors=[Author(PersonName(surname="Doe", first_name="John"))],
            ids=CitationIDs(DOI="10.1000/182", arXiv="arxivID"),
            target="http://citationtarget.org",
            publisher="FooBar",
            journal="Baz",
            series="Qux",
            scope=Scope(volume=1),
        )

        tei = Parser(TestCitation.build_xml(citation))

        assert tei.citation(tei.soup) == citation

        citation = Citation(
            title="Test2",
            authors=[Author(PersonName(surname="Doe", first_name="Jane"))],
            ids=CitationIDs(DOI="10.1000/183"),
            target="http://citationtarget.org",
            publisher="FooBar",
            scope=Scope(volume=1),
        )

        tei = Parser(TestCitation.build_xml(citation))

        assert tei.citation(tei.soup) == citation


class TestScope:
    """Unit tests for the scope function."""

    def test_valid_tag_volume(self):  # noqa: D102
        volume = 7
        scope = Scope(volume=volume)
        xml = bytes(f"<biblScope unit='volume'>{volume}</biblScope>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.scope(tei.soup) == scope

    def test_valid_tag_page(self):  # noqa: D102
        page = 1
        scope = Scope(pages=PageRange(page, page))
        xml = bytes(f"<biblScope unit='page'>{page}</biblScope>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.scope(tei.soup) == scope

    def test_valid_tag_page_range(self):  # noqa: D102
        from_page, to_page = 1, 2
        scope = Scope(pages=PageRange(from_page, to_page))
        xml = bytes(
            f"<biblScope unit='page' from='{from_page}' to='{to_page}'>",
            encoding="utf-8",
        )
        tei = Parser(xml)

        assert tei.scope(tei.soup) == scope

    def test_invalid_page_type(self):
        """Page should be of int."""
        page = "one"
        xml = bytes(f"<biblScope unit='page'>{page}</biblScope>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.scope(tei.soup) is None

    def test_empty_page(self):  # noqa: D102
        xml = b"<biblScope unit='page'></biblScope>"
        tei = Parser(xml)

        assert tei.scope(tei.soup) is None

    def test_invalid_volume_type(self):
        """Volume should be of int."""
        volume = "seven"
        xml = bytes(f"<biblScope unit='volume'>{volume}</biblScope>", encoding="utf-8")
        tei = Parser(xml)

        assert tei.scope(tei.soup) is None


class TestAuthors:
    """Unit tests for the authors function."""

    @staticmethod
    def build_xml(authors: list[Author]) -> bytes:
        """Create XML from list of author objects."""
        author_tags: list[bytes] = [b"<analytic>"]
        for author in authors:
            author_tags.append(b"<author>")
            author_tags.append(b"<persName>")
            if (first_name := author.person_name.first_name) is not None:
                author_tags.append(
                    bytes(
                        f"<forename type='first'>{first_name}</forename>",
                        encoding="utf-8",
                    )
                )
            author_tags.append(
                bytes(
                    f"<surname>{author.person_name.surname}</surname>",
                    encoding="utf-8",
                )
            )

            author_tags.append(b"</persName>")

            if (email := author.email) is not None:
                author_tags.append(bytes(f"<email>{email}</email>", encoding="utf-8"))

            author_tags.append(b"<affiliation>")
            for affiliation in author.affiliations:
                for k, v in affiliation.__dict__.items():
                    if v is None:
                        continue
                    author_tags.append(
                        bytes(f"<orgName type='{k}'>{v}</orgName>", encoding="utf-8")
                    )
            author_tags.append(b"</affiliation>")
            author_tags.append(b"</author>")

        author_tags.append(b"</analytic>")

        return b"".join(author_tags)

    def test_valid_tags(self):
        """Tests all supported tags."""
        authors = [
            Author(
                PersonName(surname="Smith", first_name="Jane"),
                email="jamesmith@gmail.com",
                affiliations=[Affiliation(department="English")],
            ),
            Author(
                PersonName(surname="Doe", first_name="John"),
                affiliations=[Affiliation(institution="University of Nottingham")],
            ),
            Author(
                PersonName(surname="Schmoe", first_name="Joe"),
                affiliations=[Affiliation(laboratory="Computer Lab")],
            ),
        ]

        tei = Parser(TestAuthors.build_xml(authors))

        assert tei.authors(tei.soup) == authors


class TestSection:
    """Unit tests for section function."""

    @staticmethod
    def build_xml(section: Section) -> bytes:
        """Create XML from Section object."""
        div_tags: list[bytes] = [b"<div>"]

        div_tags.append(bytes(f"<head>{section.title}</title>", encoding="utf-8"))

        for p in section.paragraphs:
            text_xml = p.text
            for ref in p.refs:
                marker = None
                if ref.marker:
                    marker = ref.marker.name
                ref_xml = f"<ref type='{marker}' target='{ref.target}'>{p.text[ref.start:ref.end]}</ref>"  # noqa: E501
                text_xml = text_xml[: ref.start] + ref_xml + text_xml[ref.end :]
            div_tags.append(bytes(f"<p>{text_xml}</p>", encoding="utf-8"))

        div_tags.append(b"</div>")

        return b"".join(div_tags)

    def test_valid_tag(self):  # noqa: D102
        text = "Lorem ipsum"
        section = Section(
            title="test",
            paragraphs=[
                RefText(
                    text=f"{text} [1]",
                    refs=[Ref(start=12, end=15, target="#1", marker=Marker.bibr)],
                )
            ],
        )

        for paragraph in section.paragraphs:
            assert paragraph.plain_text == text

        assert section.to_str() == text

        xml = TestSection.build_xml(section)
        tei = Parser(xml)
        # NOTE: woraround for forced capitalisation
        section.title = section.title.capitalize()

        assert tei.section(tei.soup) == section

    def test_valid_tag_no_ref(self):
        """Test for text that doesn't contain a reference."""
        text = "Lorem ipsum"
        section = Section(
            title="test",
            paragraphs=[
                RefText(
                    text=text,
                    refs=[],
                )
            ],
        )

        for paragraph in section.paragraphs:
            assert paragraph.plain_text == text

        assert section.to_str() == text

        xml = TestSection.build_xml(section)
        tei = Parser(xml)
        # NOTE: woraround for forced capitalisation
        section.title = section.title.capitalize()

        assert tei.section(tei.soup) == section

    def test_valid_tag_invalid_ref(self):
        """Test for text that contains a ref with an invalid marker (None)."""
        text = "Lorem ipsum"
        section = Section(
            title="test",
            paragraphs=[
                RefText(
                    text=f"{text} [1]",
                    refs=[Ref(start=12, end=15, target="#1", marker=None)],
                )
            ],
        )

        for paragraph in section.paragraphs:
            assert paragraph.plain_text == text

        assert section.to_str() == text

        xml = TestSection.build_xml(section)
        tei = Parser(xml)
        # NOTE: woraround for forced capitalisation
        section.title = section.title.capitalize()

        assert tei.section(tei.soup) == section

    def test_title_tag(self):
        """Test for divs that don't have <head> tag (i.e. <abstract>)."""
        title = "abstract"
        xml = bytes(f"<{title}></{title}>", encoding="utf-8")
        tei = Parser(xml)

        section = tei.section(tei.soup, title=title)

        assert section is not None
        assert section.title == title

    def test_empty_tag(self):  # noqa: D102
        xml = b"<div></div>"
        tei = Parser(xml)

        assert tei.section(tei.soup) is None


class TestTable:
    """Unit tests for table function."""

    @staticmethod
    def build_xml(table: Table, xml_id: str | None = None) -> bytes:
        """Create XML from Table object."""
        figure_tags: list[bytes] = []
        if xml_id:
            figure_tags.append(
                bytes(f"<figure xml:id='{xml_id}' type='table'>", encoding="utf-8")
            )
        else:
            figure_tags.append(b"<figure type='table'>")

        figure_tags.append(bytes(f"<head>{table.heading}</head>", encoding="utf-8"))

        if table.description is not None:
            figure_tags.append(
                bytes(f"<figDesc>{table.description}</figDesc>", encoding="utf-8")
            )

        for row in table.rows:
            figure_tags.append(b"<row>")
            for cell in row:
                figure_tags.append(bytes(f"<cell>{cell}</cell>", encoding="utf-8"))
            figure_tags.append(b"</row>")

        figure_tags.append(b"</figure>")

        return b"".join(figure_tags)

    def test_valid_tag(self):  # noqa: D102
        table = Table(heading="Test", description="Lorem Ipsum", rows=[["Foo", "Bar"]])
        xml = TestTable.build_xml(table)

        tei = Parser(xml)

        assert tei.table(tei.soup) == table

    def test_empty_tag(self):
        """Empty head tag."""
        xml = b"<figure><head></head></figure>"
        tei = Parser(xml)

        assert tei.table(tei.soup) is None


class TestCleanTitleString:
    """Unit tests for the clean_title_string function."""

    def test_non_alpha_string(self):  # noqa: D102
        s = "123"

        assert Parser.clean_title_string(s) == ""

    def test_clean_alpha_string(self):  # noqa: D102
        s = "Test"

        assert Parser.clean_title_string(s) == s

    def test_clean_dirty_string(self):  # noqa: D102
        s = "Test"
        dirty = f"21 {s}"

        assert Parser.clean_title_string(dirty) == s
