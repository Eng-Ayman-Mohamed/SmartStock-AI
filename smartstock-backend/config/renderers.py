from rest_framework.renderers import JSONRenderer


class ResponseEnvelopeRenderer(JSONRenderer):
    media_type = 'application/json'
    format = 'json'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        view = renderer_context.get('view') if renderer_context else None
        response = renderer_context.get('response') if renderer_context else None

        status_code = response.status_code if response else 200

        if status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)

        if getattr(view, 'envelope_exempt', False):
            return super().render(data, accepted_media_type, renderer_context)

        if isinstance(data, dict) and 'status' in data and 'data' in data:
            return super().render(data, accepted_media_type, renderer_context)

        request = renderer_context.get('request') if renderer_context else None
        page_param = request.query_params.get('page', 1) if request else 1
        try:
            page_param = int(page_param)
        except (TypeError, ValueError):
            page_param = 1

        if isinstance(data, dict) and 'results' in data and 'count' in data:
            wrapped = {
                'status': 'success',
                'data': data.pop('results'),
                'meta': {
                    'page': page_param,
                    'total': data.get('count', 0),
                    'per_page': 20,
                    **{k: v for k, v in data.items() if k != 'count'},
                },
            }
            return super().render(wrapped, accepted_media_type, renderer_context)

        if isinstance(data, dict) and 'results' in data:
            wrapped = {
                'status': 'success',
                'data': data.get('results', data),
                'meta': {
                    'page': page_param,
                    'total': len(data.get('results', data)),
                    'per_page': len(data.get('results', data)),
                },
            }
            return super().render(wrapped, accepted_media_type, renderer_context)

        if isinstance(data, list):
            wrapped = {
                'status': 'success',
                'data': data,
                'meta': {
                    'page': 1,
                    'total': len(data),
                    'per_page': len(data),
                },
            }
            return super().render(wrapped, accepted_media_type, renderer_context)

        wrapped = {
            'status': 'success',
            'data': data,
            'meta': {},
        }
        return super().render(wrapped, accepted_media_type, renderer_context)
