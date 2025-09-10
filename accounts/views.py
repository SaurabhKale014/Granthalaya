from django.shortcuts import render
from .models import User
from rest_framework.response import Response
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterView(APIView):
    def post(self,request):
        serializer=RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user=serializer.save()
            return Response({
                'message':'User registered successfully',
                'User ID':user.id,
                'Email':user.email

            },status=201)
        return Response(serializer.errors,status=400)

class LoginView(APIView):
    def post(self,request):
        serializer=LoginSerializer(data=request.data)
        if serializer.is_valid():
            user=serializer.validated_data['user']
            refresh=RefreshToken.for_user(user)
            return Response({
              'id':user.id,
              'Email':user.email,
              'first_name':user.first_name,
              'refresh':str(refresh),
              'access':str(refresh.access_token),
              'is_admin': user.is_admin  
            })
        return Response(serializer.errors,status=401)


