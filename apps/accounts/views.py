from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .schema import login_schema, register_schema
from .serializers import LoginSerializer, RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @register_schema
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.register_user(serializer.validated_data)
        return Response(
            {"detail": "Registration successful."},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @login_schema
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = services.login_user(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        return Response(tokens, status=status.HTTP_200_OK)
