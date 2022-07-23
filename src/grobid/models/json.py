# noqa: D100
try:
    import orjson
except ImportError:
    _has_json = False
else:
    _has_json = True


class DataClassJSONMixin:
    """Use orjson to serialize dataclasses.dataclass."""

    def to_json(self, decode=True) -> str | bytes:
        """Attempt to use orjson to serialize dataclasses.dataclass.

        Args:
            decode: decode utf-8 bytes

        Returns:
            JSON either as str or bytes, depending on value of 'decode'

        Raises:
            RuntimeWarning: extra require 'json' not installed
        """
        if not _has_json:
            raise RuntimeWarning(
                "orjson is not installed. Run 'pip install grobid[json]'"
            )

        def default(obj):
            if isinstance(obj, set):
                return list(obj)

        if decode:
            return orjson.dumps(self, default=default).decode("utf-8")
        else:
            return orjson.dumps(self, default=default)
