from app.sources.base import JobSource
from app.sources.oracle import OracleJobSource

_SOURCES: dict[str, type[JobSource]] = {
    "oracle": OracleJobSource,
}


class UnsupportedCompanyError(ValueError):
    pass


def get_source(company_name: str) -> JobSource:
    key = company_name.strip().lower()
    source_cls = _SOURCES.get(key)
    if source_cls is None:
        supported = ", ".join(sorted(_SOURCES))
        raise UnsupportedCompanyError(
            f"'{company_name}' isn't a supported company yet. Currently supported: {supported}."
        )
    return source_cls()
