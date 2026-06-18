from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password as django_validate_password
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_api_settings

from .models import CustomUser

User = get_user_model()


def _full_name(first_name: str, last_name: str) -> str:
    return f'{first_name} {last_name}'.strip()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['email'] = user.email
        return token

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field].required = False
        self.fields['email'] = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        identifier = attrs.get('email') or attrs.get(self.username_field)
        if not identifier:
            raise serializers.ValidationError('Email or username is required.')

        user = authenticate(
            request=self.context.get('request'),
            email=identifier,
            password=attrs['password'],
        )
        if user is None:
            user = authenticate(
                request=self.context.get('request'),
                **{self.username_field: identifier, 'password': attrs['password']},
            )

        if not jwt_api_settings.USER_AUTHENTICATION_RULE(user):
            raise AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )

        self.user = user
        refresh = self.get_token(user)
        return {'refresh': str(refresh), 'access': str(refresh.access_token)}


class CookieTokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True, required=False)
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        request = self.context['request']
        refresh = attrs.get('refresh') or request.COOKIES.get(
            getattr(settings, 'SIMPLE_JWT', {}).get('AUTH_COOKIE', 'refresh_token')
        )
        if not refresh:
            raise serializers.ValidationError('Refresh token not found in cookies.')
        inner = TokenRefreshSerializer(data={'refresh': refresh}, context=self.context)
        inner.is_valid(raise_exception=True)
        return inner.validated_data


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, min_length=1, max_length=255)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'password')

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'A user with this email already exists. Please use a different email address.'
            )
        return value

    def validate_password(self, value: str) -> str:
        django_validate_password(value)
        return value

    def create(self, validated_data):
        name = validated_data.pop('name').strip()
        password = validated_data.pop('password')
        email = validated_data['email']
        first_name, _, last_name = name.partition(' ')
        user = CustomUser(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=CustomUser.Role.VIEWER,
        )
        user.set_password(password)
        user.save()
        return user


class MeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'role', 'is_active')

    def get_name(self, obj: CustomUser) -> str:
        return _full_name(obj.first_name, obj.last_name)


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'name',
            'role',
            'is_active',
            'date_joined',
            'last_login',
        )
        read_only_fields = fields

    def get_name(self, obj: CustomUser) -> str:
        return _full_name(obj.first_name, obj.last_name)


class UserCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, min_length=1, max_length=255)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'password', 'role')

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_password(self, value: str) -> str:
        django_validate_password(value)
        return value

    def validate_role(self, value: str) -> str:
        if value not in CustomUser.Role.values:
            raise serializers.ValidationError('Invalid role.')
        return value

    def create(self, validated_data):
        name = validated_data.pop('name').strip()
        password = validated_data.pop('password')
        email = validated_data['email']
        first_name, _, last_name = name.partition(' ')
        user = CustomUser(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=validated_data['role'],
        )
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        return UserSerializer(instance).data


class MeUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, min_length=1, max_length=255, required=False)
    email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ('name', 'email')

    def validate_email(self, value: str) -> str:
        User = get_user_model()
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError(
                'A user with this email already exists. Please use a different email address.'
            )
        return value

    def update(self, instance, validated_data):
        name = validated_data.pop('name', None)
        if name:
            name = name.strip()
            first_name, _, last_name = name.partition(' ')
            instance.first_name = first_name
            instance.last_name = last_name
        email = validated_data.get('email')
        if email:
            instance.email = email
            instance.username = email
        instance.save()
        return instance


class RoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('role',)

    def validate_role(self, value: str) -> str:
        if value not in CustomUser.Role.values:
            raise serializers.ValidationError('Invalid role.')
        return value
