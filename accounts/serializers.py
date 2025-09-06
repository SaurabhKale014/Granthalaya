from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'contact_no', 'address','is_admin']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class LoginSerializer(serializers.Serializer):
    email=serializers.EmailField()
    password=serializers.CharField(write_only=True)
    def validate(self, data):
        try:
            user=User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email not found")
        if not check_password(data['password'],user.password):
            raise serializers.ValidationError("Incorrect password")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
        data['user']=user
        return data