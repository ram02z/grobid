# noqa: D100
# TODO: figure out how to mock dependency
import sys
from dataclasses import dataclass

import pytest

from grobid.models.json import DataClassJSONMixin


@dataclass
class MockDataClass(DataClassJSONMixin):  # noqa: D101
    test: set


class TestDataClassJSONMixin:  # noqa: D101
    obj = MockDataClass(test=set())

    def test_orjson_available(self):  # noqa: D102
        if "orjson" in sys.modules:
            assert self.obj.to_json(decode=True) == '{"test":[]}'
            assert self.obj.to_json(decode=False) == b'{"test":[]}'

    def test_orjson_not_available(self):  # noqa: D102
        if "orjson" not in sys.modules:
            with pytest.raises(RuntimeWarning):
                self.obj.to_json()
