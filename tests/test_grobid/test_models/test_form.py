"""Unit tests for grobid form module."""


import fitz

from grobid.models.form import File, Form

with fitz.open(filetype="pdf") as test_pdf:
    test_pdf.new_page()
    test_obj = test_pdf.tobytes()


class TestForm:
    """Unit tests for Form class."""

    file: File = File(test_obj)

    def test_no_opt_params(self):  # noqa: D102
        form: Form = Form(self.file)

        assert form.to_dict() == dict(input=self.file.to_tuple())

    def test_segment_sentences_param(self):  # noqa: D102
        form: Form = Form(self.file, segment_sentences=True)

        assert form.to_dict() == dict(input=self.file.to_tuple(), segmentSentences="1")

    def test_consolidate_header_param(self):  # noqa: D102
        form: Form = Form(self.file, consolidate_header=0)

        assert form.to_dict() == dict(input=self.file.to_tuple(), consolidateHeader="0")

    def test_consolidate_citations_param(self):  # noqa: D102
        form: Form = Form(self.file, consolidate_citations=0)

        assert form.to_dict() == dict(
            input=self.file.to_tuple(), consolidateCitations="0"
        )

    def test_include_raw_citations_param(self):  # noqa: D102
        form: Form = Form(self.file, include_raw_citations=True)

        assert form.to_dict() == dict(
            input=self.file.to_tuple(), includeRawCitations=True
        )

    def test_include_raw_affliations_param(self):  # noqa: D102
        form: Form = Form(self.file, include_raw_affiliations=True)

        assert form.to_dict() == dict(
            input=self.file.to_tuple(), includeRawAffiliations=True
        )

    def test_tei_coordinates_param(self):  # noqa: D102
        tei_coordinates = "s"
        form: Form = Form(self.file, tei_coordinates=tei_coordinates)

        assert form.to_dict() == dict(
            input=self.file.to_tuple(), teiCoordinates=tei_coordinates
        )


class TestFile:
    """Unit tests for File class."""

    def test_no_opt_params(self):  # noqa: D102
        file: File = File(test_obj)

        assert file.to_tuple() == (None, test_obj, None)

    def test_file_name_param(self):  # noqa: D102
        file_name = "test"
        file: File = File(test_obj, file_name=file_name)

        assert file.to_tuple() == (file_name, test_obj, None)

    def test_mime_type_param(self):  # noqa: D102
        mime_type = "application/pdf"
        file: File = File(test_obj, mime_type=mime_type)

        assert file.to_tuple() == (None, test_obj, mime_type)

    def test_all_params(self):  # noqa: D102
        file_name = "test"
        mime_type = "application/pdf"
        file: File = File(test_obj, file_name=file_name, mime_type=mime_type)

        assert file.to_tuple() == (file_name, test_obj, mime_type)
