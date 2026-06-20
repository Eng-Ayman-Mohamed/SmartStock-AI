import re

_CITATION_PATTERN = re.compile(r'\[Source:\s*([^,]+),\s*Page:\s*(\d+)\]')


def inject_citations(response: str, sources: list[dict]) -> str:
    if not sources:
        return response

    existing = _CITATION_PATTERN.findall(response)
    if existing:
        return response

    source = sources[0]
    doc = source.get('document', 'unknown')
    page = source.get('page', '?')
    return f'{response}\n\n[Source: {doc}, Page: {page}]'
