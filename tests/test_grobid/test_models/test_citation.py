"""Unit tests for the citation module."""
from grobid.models import PersonName


class TestPersonName:
    """Unit tests for PersonName class."""

    first_name = "Foo"
    surname = "Bar"

    def test_to_string(self):
        """Tests surname only then adds first name."""
        person_name = PersonName(surname=self.surname)
        assert person_name.to_string() == self.surname

        person_name.first_name = self.first_name
        assert person_name.to_string() == f"{self.first_name} {self.surname}"
