from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import AuthorListCreateView, AuthorUpdateDeleteView,BookListCreateView,BookUpdateDeleteView,ApproveBorrowRequestView,ApproveReturnRequestView,AllBorrowRecordsView,ProfilePhotoUpdateView,MyAccountView
urlpatterns = [
    path('authors/',AuthorListCreateView.as_view(), name='author-list-create'),
    path('authors/<int:pk>/',AuthorUpdateDeleteView.as_view()),
    path('books/',BookListCreateView.as_view()),
    path('books/<int:pk>/',BookUpdateDeleteView.as_view()),
    path('approve-borrow/<int:record_id>/',ApproveBorrowRequestView.as_view()),
    path('approve-return/<int:record_id>/',ApproveReturnRequestView.as_view()),
    path('all-records/', AllBorrowRecordsView.as_view(), name='all-records'),
    path('set-profile-photo/',ProfilePhotoUpdateView.as_view()),    # GET
    path('get-profile-photo/',ProfilePhotoUpdateView.as_view()),    # PATCH
    path('my-account/', MyAccountView.as_view(), name='my-account'),# GET
    path('my-account/update/',MyAccountView.as_view())              # PATCH
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
