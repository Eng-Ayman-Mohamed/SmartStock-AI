from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import CustomUser
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer
from apps.authentication.permissions import IsAdminOnly


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer


class LoginView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
        })


class UserRoleUpdateView(APIView):
    permission_classes = [IsAdminOnly]

    def patch(self, request, user_id):
        new_role = request.data.get('role')
        if new_role not in ['viewer', 'manager', 'admin']:
            return Response(
                {'error': 'Invalid role. Must be viewer, manager, or admin.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = CustomUser.objects.get(pk=user_id)
        user.role = new_role
        user.save()
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
        })
