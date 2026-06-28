import logging

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.authentication.permissions import IsViewerOrAbove
from config.schema_serializers import ErrorResponseSerializer, ValidationErrorResponseSerializer

from .serializers import (
    ChatConversationCreateSerializer,
    ChatConversationDetailSerializer,
    ChatConversationListSerializer,
    ChatConversationRenameSerializer,
    ChatMessageSerializer,
)
from .services import ConversationService

logger = logging.getLogger(__name__)


class MessagePagination(PageNumberPagination):
    page_size = 50
    ordering = 'created_at'


@extend_schema_view(
    list=extend_schema(
        responses={
            200: inline_serializer(
                'ConversationListResponse',
                {
                    'status': serializers.CharField(),
                    'data': ChatConversationListSerializer(many=True),
                },
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
        },
        tags=['ai'],
    ),
    create=extend_schema(
        request=ChatConversationCreateSerializer,
        responses={
            201: inline_serializer(
                'ConversationCreateResponse',
                {
                    'status': serializers.CharField(),
                    'data': ChatConversationDetailSerializer(),
                },
            ),
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Bad request'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Validation error'
            ),
        },
        examples=[
            OpenApiExample(
                'Create Conversation',
                value={'title': 'Inventory Questions'},
                request_only=True,
            ),
        ],
        tags=['ai'],
    ),
    retrieve=extend_schema(
        responses={
            200: inline_serializer(
                'ConversationDetailResponse',
                {
                    'status': serializers.CharField(),
                    'data': ChatConversationDetailSerializer(),
                },
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Conversation not found'
            ),
        },
        tags=['ai'],
    ),
    partial_update=extend_schema(
        request=ChatConversationRenameSerializer,
        responses={
            200: inline_serializer(
                'ConversationRenameResponse',
                {
                    'status': serializers.CharField(),
                    'data': ChatConversationDetailSerializer(),
                },
            ),
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Bad request'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Conversation not found'
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Validation error'
            ),
        },
        examples=[
            OpenApiExample(
                'Rename Conversation',
                value={'title': 'Updated Title'},
                request_only=True,
            ),
        ],
        tags=['ai'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Conversation not found'
            ),
        },
        tags=['ai'],
    ),
    messages=extend_schema(
        responses={
            200: inline_serializer(
                'ConversationMessagesResponse',
                {
                    'status': serializers.CharField(),
                    'data': ChatMessageSerializer(many=True),
                    'meta': inline_serializer(
                        'PaginationMeta',
                        {
                            'page': serializers.IntegerField(),
                            'total': serializers.IntegerField(),
                            'per_page': serializers.IntegerField(),
                        },
                    ),
                },
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Conversation not found'
            ),
        },
        tags=['ai'],
    ),
)
class ConversationViewSet(ViewSet):
    """
    ViewSet for managing chat conversations.

    list:       GET    /api/ai/conversations/
    create:     POST   /api/ai/conversations/
    retrieve:   GET    /api/ai/conversations/{id}/
    partial_update: PATCH /api/ai/conversations/{id}/
    destroy:    DELETE /api/ai/conversations/{id}/
    messages:   GET    /api/ai/conversations/{id}/messages/
    """

    permission_classes = [IsViewerOrAbove]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = ConversationService()
        return self._service

    def list(self, request):
        conversations = self.service.list_conversations(request.user)
        serializer = ChatConversationListSerializer(conversations, many=True)
        return Response({'status': 'success', 'data': serializer.data})

    def create(self, request):
        serializer = ChatConversationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        title = serializer.validated_data.get('title', 'New Conversation')
        conversation = self.service.create_conversation(request.user, title)
        detail = ChatConversationDetailSerializer(conversation)
        return Response(
            {'status': 'success', 'data': detail.data},
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        try:
            conversation = self.service.get_conversation(pk, request.user)
        except ValueError:
            return Response(
                {'status': 'error', 'message': 'Conversation not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ChatConversationDetailSerializer(conversation)
        return Response({'status': 'success', 'data': serializer.data})

    def partial_update(self, request, pk=None):
        serializer = ChatConversationRenameSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        try:
            conversation = self.service.rename_conversation(
                pk, request.user, serializer.validated_data['title']
            )
        except ValueError:
            return Response(
                {'status': 'error', 'message': 'Conversation not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        detail = ChatConversationDetailSerializer(conversation)
        return Response({'status': 'success', 'data': detail.data})

    def destroy(self, request, pk=None):
        try:
            self.service.delete_conversation(pk, request.user)
        except ValueError:
            return Response(
                {'status': 'error', 'message': 'Conversation not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        try:
            conversation = self.service.get_conversation(pk, request.user)
        except ValueError:
            return Response(
                {'status': 'error', 'message': 'Conversation not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        paginator = MessagePagination()
        page = paginator.paginate_queryset(conversation.messages.all(), request)
        serializer = ChatMessageSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
