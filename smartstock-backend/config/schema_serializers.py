from rest_framework import serializers


class ErrorResponseSerializer(serializers.Serializer):
    """Standard error envelope returned by the custom exception handler."""

    status = serializers.CharField(help_text='Always "error"', default='error')
    error = serializers.CharField(help_text='Exception or error type')
    message = serializers.CharField(help_text='Human-readable error message')
    code = serializers.IntegerField(help_text='HTTP status code')


class ValidationErrorResponseSerializer(serializers.Serializer):
    """Validation error envelope with per-field error lists."""

    status = serializers.CharField(help_text='Always "error"', default='error')
    error = serializers.CharField(help_text='Always "ValidationError"', default='ValidationError')
    message = serializers.CharField(help_text='Validation failed.', default='Validation failed.')
    fields = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text='Per-field validation errors',
    )
