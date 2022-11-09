import pytest

from djangocms_xliff.types import XliffContext


@pytest.fixture
def create_xliff_context():
    def _create_xliff_context(units, source_language="de", target_language="fr", page_id=1, page_path="/test"):
        return XliffContext(
            source_language=source_language,
            target_language=target_language,
            page_id=page_id,
            page_path=page_path,
            units=units,
        )

    return _create_xliff_context
