from rest_framework import permissions, generics, status
from rest_framework.response import Response
from knox.models import AuthToken
from django.contrib.auth.models import User
from .serializers import LoginSerializer, UserSerializer
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from .serializers import PasswordResetRequestSerializer, PasswordResetSerializer


class LoginApi(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract the user instance from the validated data
        username = serializer.validated_data['username']
        user = User.objects.get(username=username)

        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)[1]
        })


# Get User API
class UserApi(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        # # Check if the user is associated with a Staff or Customer object
        # if not (hasattr(request.user, 'staff') or hasattr(request.user, 'customer')):
        #     # Log out the user
        #     auth_logout(request)
        #     return Response({"detail": "User not associated with Staff or Customer."}, status=status.HTTP_403_FORBIDDEN)

        # If associated, return the user details
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def get_object(self):
        return self.request.user


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(
            email=serializer.validated_data['email'])
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{settings.FRONTEND_URL}auth/reset-password/{uid}/{token}"

        # Render the email template
        email_subject = 'Password Reset Request'
        email_body = render_to_string('reset_password.html', {
            'user': user,
            'reset_link': reset_link,
        })

        plain_message = strip_tags(email_body)
        try:
            send_mail(subject=email_subject,
                      message=plain_message,
                      from_email=settings.EMAIL_FROM_EMAIL,
                      auth_user=settings.EMAIL_HOST_USER,
                      auth_password=settings.EMAIL_HOST_PASSWORD,
                      recipient_list=[user.email],
                      html_message=email_body
                      )
        except Exception as e:
            print(e)

        return Response(
            {"message": "Password reset link sent."},
            status=status.HTTP_200_OK)


class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(
                serializer.validated_data['uid']))
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, serializer.validated_data['token']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response(
                    {"message": "Password reset successful."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Invalid token."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid uid."}, status=status.HTTP_400_BAD_REQUEST)
