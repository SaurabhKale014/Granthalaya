from django.urls import path
from .views import AvailableBooksView,BorrowRequestView,ReturnRequestView,MyBorrowedBooksView,BorrowingHistoryView
urlpatterns = [
   path('available-books/', AvailableBooksView.as_view(), name='available-books'),
   path('borrow-request/<int:book_id>/',BorrowRequestView.as_view()),
   path('return-request/<int:book_id>/',ReturnRequestView.as_view()),
   path('my-borrowed-books/', MyBorrowedBooksView.as_view(), name='my-borrowed-books'),
   path('borrowing-history/', BorrowingHistoryView.as_view(), name='borrowing-history'),
]