from rest_framework import serializers

from library.models import  Book

class BookBrowseSerializer(serializers.ModelSerializer):
    class Meta :
        model=Book
        fields=['id','title','author','available_copies']