from django.urls import path
from .views import AuthorListCreateView, AuthorUpdateDeleteView,BookListCreateView,BookUpdateDeleteView,ApproveBorrowRequestView,ApproveReturnRequestView,AllBorrowRecordsView
urlpatterns = [
    path('authors/',AuthorListCreateView.as_view(), name='author-list-create'),
    path('authors/<int:pk>/',AuthorUpdateDeleteView.as_view()),
    path('books/',BookListCreateView.as_view()),
    path('books/<int:pk>/',BookUpdateDeleteView.as_view()),
    path('approve-borrow/<int:record_id>/',ApproveBorrowRequestView.as_view()),
    path('approve-return/<int:record_id>/',ApproveReturnRequestView.as_view()),
    path('all-records/', AllBorrowRecordsView.as_view(), name='all-records'),
   
]