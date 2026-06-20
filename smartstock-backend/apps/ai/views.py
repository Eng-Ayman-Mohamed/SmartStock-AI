import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.authentication.permissions import IsViewerOrAbove

from .serializers import (
    ChatConversationCreateSerializer,
    ChatConversationDetailSerializer,
    ChatConversationListSerializer,
    ChatConversationRenameSerializer,
    ChatMessageSerializer,
)
from .services import ConversationService

logger = logging.getLogger(__name__)


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
        self._service = ConversationService()

    def list(self, request):
        conversations = self._service.list_conversations(request.user)
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
        conversation = self._service.create_conversation(request.user, title)
        detail = ChatConversationDetailSerializer(conversation)
        return Response(
            {'status': 'success', 'data': detail.data},
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        try:
            conversation = self._service.get_conversation(pk, request.user)
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
            conversation = self._service.rename_conversation(
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
            self._service.delete_conversation(pk, request.user)
        except ValueError:
            return Response(
                {'status': 'error', 'message': 'Conversation not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        try:
            conversation = self._service.get_conversation(pk, request.user)
        except ValueError:
            return Response(
                {'status': 'error', 'message': 'Conversation not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ChatMessageSerializer(conversation.messages.all(), many=True)
        return Response({'status': 'success', 'data': serializer.data})
