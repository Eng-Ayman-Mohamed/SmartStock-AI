import re

_CITATION_PATTERN = re.compile(r'\[Source:\s*([^,]+),\s*Page:\s*(\d+)\]')


def inject_citations(response: str, sources: list[dict]) -> str:
    if not sources:
        return response

    existing = _CITATION_PATTERN.findall(response)
    if existing:
        return response

    citations = []
    for source in sources:
        doc = source.get('document')
        page = source.get('page')
        if doc and page is not None:
            citations.append(f'[Source: {doc}, Page: {page}]')

    if not citations:
        return response

    return f'{response}\n\n' + '\n'.join(citations)
