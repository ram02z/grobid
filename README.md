# grobid
> Python library for serializing GROBID TEI XML to [dataclasses](https://docs.python.org/3/library/dataclasses.html)

[![Build Status](https://github.com/ram02z/grobid/workflows/tests/badge.svg)](https://github.com/ram02z/grobid/actions)
[![Coverage Status](https://coveralls.io/repos/github/ram02z/grobid/badge.svg)](https://coveralls.io/github/ram02z/grobid)
[![Latest Version](https://img.shields.io/pypi/v/grobid.svg)](https://pypi.python.org/pypi/grobid)
[![Python Version](https://img.shields.io/pypi/pyversions/grobid.svg)](https://pypi.python.org/pypi/grobid)
[![License](https://img.shields.io/badge/MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Installation

Use `pip` to install:

```shell
$ pip install grobid
$ pip install grobid[json] # for JSON serializable dataclass objects
```


You can also download the `.whl` file from the release section:

```shell
$ pip install *.whl
```

## Usage

### Client

In order to convert an academic PDF to TEI XML file, we use GROBID's REST
services. Specifically the [processFulltextDocument](https://grobid.readthedocs.io/en/latest/Grobid-service/#apiprocessfulltextdocument) endpoint.


```python
from pathlib import Path
from grobid.models.form import Form, File
from grobid.models.response import Response

pdf_file = Path("<your-academic-article>.pdf")
with open(pdf_file, "rb") as file:
    form = Form(
        file=File(
            payload=file.read(),
            file_name=pdf_file.name,
            mime_type="application/pdf",
        )
    )
    c = Client(base_url="<base-url>", form=form)
    try:
        xml_content = c.sync_request().content  # TEI XML file in bytes
    except GrobidClientError as e:
        print(e)
```

where `base-url` is the URL of the GROBID REST service

> You can use `https://cloud.science-miner.com/grobid/` to test

#### [Form](https://github.com/ram02z/grobid/blob/master/src/grobid/models/form.py#L20)

The `Form` class supports most of the optional parameters of the processFulltextDocument
endpoint.


### Parser

If you want to serialize the XML content, we can use the `Parser` class to
create [dataclasses](https://docs.python.org/3/library/dataclasses.html)
objects.

Not all of the GROBID annoation guidelines are met, but compliance is a goal.
See [#1](https://github.com/ram02z/grobid/issues/1).

```python
from grobid.tei import Parser

xml_content: bytes
parser = Parser(xml_content)
article = parser.parse()
article.to_json()  # throws RuntimeError if extra require 'json' not installed
```

where `xml_content` is the same as in [Client section](#client)

Alternately, you can load the XML from a file:

```python
from grobid.tei import Parser

with open("<your-academic-article>.xml", "rb") as xml_file:
  xml_content = xml_file.read()
  parser = Parser(xml_content)
  article = parser.parse()
  article.to_json()  # throws RuntimeError if extra require 'json' not installed
```

We use [mashumaro](https://github.com/Fatal1ty/mashumaro) to serialize the
dataclasses into JSON (mashumaro supports other formats, you can submit a PR if
you want). By default, mashumaro isn't installed, use `pip install
grobid[json]`.

## License

MIT

## Contributing

You are welcome to add missing features by submitting a PR, however, I won't be
accepting any requests other than GROBID annotation compliance.

## Disclaimer

This module was originally part of a group university project, however, all the
code and tests was also authored by me.
