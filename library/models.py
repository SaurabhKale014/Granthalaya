from django.db import models

class Author(models.Model):
    name=models.CharField(max_length=100)
    bio=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='Authors'

class Book(models.Model):
    title=models.CharField(max_length=200)
    author=models.ForeignKey(Author,on_delete=models.CASCADE)
    isbn=models.CharField(max_length=13 , unique=True)
    published_date=models.DateField()
    total_copies=models.PositiveIntegerField(default=1)
    available_copies=models.PositiveIntegerField(default=1)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='Books'
