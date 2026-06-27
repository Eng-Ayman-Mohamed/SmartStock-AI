from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from config.schema_serializers import ErrorResponseSerializer, ValidationErrorResponseSerializer
from config.settings.base import IS_PRODUCTION

from .models import CustomUser
from .permissions import IsAdminOnly
from .serializers import (
    CookieTokenRefreshSerializer,
    CustomTokenObtainPairSerializer,
    MeSerializer,
    MeUpdateSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    RoleUpdateSerializer,
    UserCreateSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from .services import generate_verification_token, send_verification_email, verify_email_token


class TokenRefreshView(BaseTokenRefreshView):
    serializer_class = CookieTokenRefreshSerializer
    throttle_classes = []
    envelope_exempt = True

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={'type': 'object', 'properties': {'access': {'type': 'string'}}},
                description='Token refreshed successfully',
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Refresh token missing or invalid'
            ),
        },
        tags=['auth'],
        auth=[],
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.get('refresh')
        if refresh_token:
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=IS_PRODUCTION or not settings.DEBUG,
                samesite='None' if IS_PRODUCTION else 'Lax',
                max_age=3 * 24 * 60 * 60,
            )
        return response


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'login'
    envelope_exempt = True

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'access': {'type': 'string', 'description': 'JWT access token'},
                        'refresh': {'type': 'string', 'description': 'JWT refresh token'},
                        'user': {'$ref': '#/components/schemas/Me'},
                    },
                },
                description='User registered successfully',
            ),
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Bad request'
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Validation error'
            ),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        examples=[
            OpenApiExample(
                'Register Request',
                value={
                    'email': 'user@example.com',
                    'name': 'John Doe',
                    'password': 'securePass123',
                },
                request_only=True,
            ),
        ],
        tags=['auth'],
        auth=[],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = generate_verification_token(user)
        send_verification_email(user, token)
        return Response(
            {
                'detail': 'Account created. Please check your email to verify your address.',
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'login'
    envelope_exempt = True

    @extend_schema(
        request=CustomTokenObtainPairSerializer,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'access': {'type': 'string', 'description': 'JWT access token'},
                        'refresh': {'type': 'string', 'description': 'JWT refresh token'},
                        'user': {'$ref': '#/components/schemas/Me'},
                    },
                },
                description='Login successful',
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Invalid credentials'
            ),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        examples=[
            OpenApiExample(
                'Login Request',
                value={'email': 'user@example.com', 'password': 'securePass123'},
                request_only=True,
            ),
        ],
        tags=['auth'],
        auth=[],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as exc:
            error_detail = exc.detail if hasattr(exc, 'detail') else str(exc)
            if isinstance(error_detail, dict):
                has_missing_field = any(
                    'required' in str(v).lower() if isinstance(v, (list, str)) else False
                    for v in error_detail.values()
                )
                if has_missing_field:
                    return Response(
                        {
                            'status': 'error',
                            'error': 'ValidationError',
                            'message': 'Email and password are required.',
                            'code': 400,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            return Response(
                {
                    'status': 'error',
                    'error': 'AuthenticationFailed',
                    'message': 'Invalid email or password.',
                    'code': 401,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user = getattr(serializer, 'user', None)
        if user and not user.email_verified:
            return Response(
                {
                    'status': 'error',
                    'error': 'EmailNotVerified',
                    'message': 'Please verify your email before logging in.',
                    'code': 403,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        validated_data = serializer.validated_data
        response = Response(
            {
                'access': validated_data['access'],
                'refresh': validated_data['refresh'],
                'user': MeSerializer(user).data if user else None,
            },
            status=status.HTTP_200_OK,
        )
        response.set_cookie(
            key='refresh_token',
            value=validated_data['refresh'],
            httponly=True,
            secure=IS_PRODUCTION or not settings.DEBUG,
            samesite='None' if IS_PRODUCTION else 'Lax',
            max_age=3 * 24 * 60 * 60,
        )
        return response


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    envelope_exempt = True

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={'type': 'object', 'properties': {'detail': {'type': 'string'}}},
                description='Logged out successfully',
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
        },
        tags=['auth'],
    )
    def post(self, request):
        response = Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)
        refresh_cookie_name = getattr(settings, 'REFRESH_TOKEN_COOKIE_NAME', 'refresh_token')
        response.delete_cookie(refresh_cookie_name)
        return response


class VerifyEmailView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    envelope_exempt = True

    @extend_schema(
        request=VerifyEmailSerializer,
        responses={
            200: OpenApiResponse(
                response={'type': 'object', 'properties': {'detail': {'type': 'string'}}},
                description='Email verified successfully',
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer, description='Invalid or expired token'
            ),
        },
        tags=['auth'],
        auth=[],
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        success, message, http_status = verify_email_token(serializer.validated_data['token'])
        if success:
            return Response({'detail': message}, status=status.HTTP_200_OK)
        return Response(
            {'detail': message},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ResendVerificationView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    envelope_exempt = True

    @extend_schema(
        request=ResendVerificationSerializer,
        responses={
            200: OpenApiResponse(
                response={'type': 'object', 'properties': {'detail': {'type': 'string'}}},
                description='Verification email sent',
            ),
            400: OpenApiResponse(response=ErrorResponseSerializer, description='Validation error'),
        },
        tags=['auth'],
        auth=[],
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = CustomUser.objects.filter(email__iexact=email).first()
        if user and not user.email_verified:
            token = generate_verification_token(user)
            send_verification_email(user, token)
        return Response(
            {
                'detail': 'If that email is registered and unverified, a verification link has been sent.'
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    envelope_exempt = True

    @extend_schema(
        responses={
            200: MeSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
        },
        tags=['auth'],
    )
    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        request=MeUpdateSerializer,
        responses={
            200: MeSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Bad request'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
        },
        tags=['auth'],
    )
    def patch(self, request):
        serializer = MeUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(MeSerializer(user).data)


class UserListCreateView(generics.ListCreateAPIView):
    queryset = (
        CustomUser.objects.all()
        .prefetch_related('groups', 'user_permissions')
        .order_by('-date_joined')
    )
    permission_classes = (IsAdminOnly,)
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'email', 'username', 'first_name', 'is_active', 'role']
    filterset_fields = ['is_active', 'role']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    @extend_schema(
        responses={
            200: UserSerializer(many=True),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
        },
        tags=['auth'],
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @extend_schema(
        request=UserCreateSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Bad request'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Validation error'
            ),
        },
        tags=['auth'],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (IsAdminOnly,)
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return RoleUpdateSerializer
        return UserSerializer

    @extend_schema(
        responses={
            200: UserSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='User not found'),
        },
        tags=['auth'],
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @extend_schema(
        request=RoleUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Bad request'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='User not found'),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Validation error'
            ),
        },
        tags=['auth'],
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @extend_schema(
        request=RoleUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Bad request'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='User not found'),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Validation error'
            ),
        },
        tags=['auth'],
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

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

    @extend_schema(
        responses={
            200: UserSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='User already deactivated'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='User not found'),
        },
        tags=['auth'],
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance: CustomUser) -> None:
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    @extend_schema(
        responses={
            200: UserSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='User already deactivated'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='User not found'),
        },
        tags=['auth'],
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_active:
            return Response(
                {'detail': 'User is already deactivated.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(UserSerializer(instance).data, status=status.HTTP_200_OK)
