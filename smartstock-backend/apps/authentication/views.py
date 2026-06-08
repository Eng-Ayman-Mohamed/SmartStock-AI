from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView


class TokenRefreshView(BaseTokenRefreshView):
    envelope_exempt = True

from .models import CustomUser
from .permissions import IsAdminOnly
from .serializers import (
    MeSerializer,
    RegisterSerializer,
    RoleUpdateSerializer,
    UserCreateSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    envelope_exempt = True

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': MeSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    envelope_exempt = True

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {'status': 'error', 'error': 'AuthenticationFailed',
                 'message': 'Invalid email or password.', 'code': 401},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user = getattr(serializer, 'user', None)
        data = serializer.validated_data
        if user:
            data['user'] = MeSerializer(user).data
        return Response(data)


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    envelope_exempt = True

    def post(self, request):
        response = Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)
        refresh_cookie_name = getattr(settings, 'REFRESH_TOKEN_COOKIE_NAME', 'refresh_token')
        response.delete_cookie(refresh_cookie_name)
        return response


class MeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    envelope_exempt = True

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)


class UserListCreateView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all().order_by('-date_joined')
    permission_classes = (IsAdminOnly,)
    envelope_exempt = True

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (IsAdminOnly,)
    lookup_field = 'pk'
    envelope_exempt = True

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return RoleUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = RoleUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(instance).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance: CustomUser) -> None:
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_active:
            return Response(
                {'detail': 'User is already deactivated.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(UserSerializer(instance).data, status=status.HTTP_200_OK)
