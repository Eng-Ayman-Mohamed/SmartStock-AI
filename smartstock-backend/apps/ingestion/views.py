from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsAdminOnly, IsViewerOrAbove

from .models import Document, DocumentChunk
from .serializers import DocumentChunkSerializer, DocumentListSerializer, DocumentUploadSerializer
from .services import IngestionService

service = IngestionService()


class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated, IsViewerOrAbove]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        file = serializer.validated_data['file']
        doc_type = serializer.validated_data.get('doc_type')

        raw = file.read()
        if not raw.startswith(b'%PDF'):
            return Response(
                {'status': 'error', 'message': 'Only PDF files are currently supported for ingestion.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        file.seek(0)

        if len(raw) > 10 * 1024 * 1024:
            return Response(
                {'status': 'error', 'message': 'File size exceeds 10MB limit.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            document = service.upload_document(file, request.user, doc_type)
            out = DocumentListSerializer(document, context={'request': request})
            return Response(
                {'status': 'success', 'data': out.data},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DocumentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsViewerOrAbove]
    serializer_class = DocumentListSerializer

    def get_queryset(self):
        return service.list_documents()


class DocumentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsViewerOrAbove]
    serializer_class = DocumentListSerializer
    queryset = Document.objects.filter(is_active=True)


class DocumentDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def delete(self, request, pk):
        success = service.soft_delete_document(pk)
        if not success:
            return Response(
                {'status': 'error', 'message': 'Document not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
