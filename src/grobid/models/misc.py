# noqa: D100
class DataClassDictMixin:
    """Mock for mashumaro.DataClassDictMixin."""

    def to_json(self):
        """Raises RuntimeWarning if user tries to use this method."""
        raise RuntimeWarning(
            "mashumaro is not installed. Run 'pip install grobid_client[json]'"
        )

    @classmethod
    def from_json(cls):
        """Raises RuntimeWarning if user tries to use this method."""
        raise RuntimeWarning(
            "mashumaro is not installed. Run 'pip install grobid_client[json]'"
        )


class DataClassJSONMixin(DataClassDictMixin):
    """Mock for mashumaro.DataClassJSONMixin."""

    pass
