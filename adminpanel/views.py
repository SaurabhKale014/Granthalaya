from urllib import request
from django.http import HttpResponse
from library.models import Author, Book
from .serializers import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.db import connection
from rest_framework.permissions import  IsAuthenticated
from .authentication import CustomJWTAuthentication
from .permissions import IsAdmin


class AdminDashboardView(APIView):
    permission_classes=[IsAuthenticated, IsAdmin]
    authentication_classes=[CustomJWTAuthentication]
    def get(self,request):
        with connection.cursor() as cursor:
            # Total Users 
            cursor.execute("select count(*) from users")
            total_users=cursor.fetchone()

            #Active users
            cursor.execute("select count(*) from users where is_active=1")
            active_users=cursor.fetchone()

            #Inactive users
            cursor.execute("select count(*) from users where is_active=0")
            inactive_users=cursor.fetchone()[0]

            #Total Books
            cursor.execute("select count(*) from Books")
            total_books=cursor.fetchone()

            #Available Books
            cursor.execute("select count(*) from Books where available_copies > 0")
            available_books=cursor.fetchone()[0]

            #Pending Borrow Requests
            cursor.execute("select count(*) from borrow_records where status='pending_approval'")
            pending_requests=cursor.fetchone()
            return Response({
                "total_users":total_users[0],
                "active_users":active_users[0],
                "inactive_users":inactive_users,
                "total_books":total_books[0],
                "available_books":available_books,
                "pending_requests":pending_requests[0]
            })

class AuthorListCreateView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    authentication_classes=[CustomJWTAuthentication]
    def get(self, request):
        authors=Author.objects.all()
        serializer=AuthorSerializer(authors, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer=AuthorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuthorUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    authentication_classes=[CustomJWTAuthentication]
    def patch(self, request, pk):
        with connection.cursor() as cursor:
            cursor.execute("select id from Authors where id=%s",[pk])
            if not cursor.fetchone():
                return Response({"error":"Author not found"},status=status.HTTP_404_NOT_FOUND)
            
            if  request.data:

                if 'name' in request.data:
                    cursor.execute("update Authors set name =%s where id =%s",[request.data['name'],pk])
                    return Response({"message":"Author name updated successfully"})
                
                if 'bio' in request.data:
                    bio=request.data.get('bio')
                    cursor.execute("update Authors set bio=%s where id=%s",[bio,pk])
                    return Response({"message":"Author bio updated successfully"})
            
            return Response({"message":"No data given to update"})
    
    def delete(self, request , pk):
        with connection.cursor() as cursor:
            cursor.execute("select id from Authors where id=%s",[pk])
            if not cursor.fetchone():
                return Response({"error":"Author not found"},status=status.HTTP_404_NOT_FOUND)
            cursor.execute("delete from Authors where id=%s",[pk])
            return Response({"message":"Author deleted successfully"})
        

class BookListCreateView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    authentication_classes=[CustomJWTAuthentication]
    def get(self,request):
        books=Book.objects.all()
        serializer=BookSerializer(books,many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer=BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Book added successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class BookUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    authentication_classes=[CustomJWTAuthentication]
    def patch(self, request, pk):
        with connection.cursor() as cursor:
            cursor.execute("select id  from Books where id=%s",[pk])
            if not cursor.fetchone():
                return Response({"error":"Book not found"},status=status.HTTP_404_NOT_FOUND)
            allowed_fields = ['title', 'isbn', 'published_date', 'total_copies', 'available_copies', 'author']
            update_data={}
            for field in allowed_fields:
                if field in request.data:
                    update_data[field]=request.data[field]
            if not update_data:
                return Response({"message":"No fields provided for update"},status=status.HTTP_400_BAD_REQUEST)
            set_clause=", ".join([f"{field}=%s" for field in update_data.keys()])
            params=list(update_data.values()) + [pk]
            cursor.execute(f"update Books set {set_clause} where id=%s",params)
            return Response({"message":"Book updated successfully"})
    
    def delete(self, request, pk):
        with connection.cursor() as cursor:
            cursor.execute("select id from Books where id = %s",[pk])
            if not cursor.fetchone():
                return Response({"error":"Book not found"},status=status.HTTP_404_NOT_FOUND)
            cursor.execute("delete from Books where id=%s",[pk])
            return Response({"message":"Book deleted successfully."})

class ApproveBorrowRequestView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    authentication_classes=[CustomJWTAuthentication]

    def get(self,request):
        with connection.cursor() as cursor:
            cursor.execute("""
                            select br.id as record_no,concat(u.first_name,' ',u.last_name)as name, b.title as book_name,date(borrow_requested_at) as request_date from borrow_records br 
            left join users u on br.user_id=u.id 
            left join Books b on br.book_id=b.id
            where br.status='pending_approval'
            """)
            request_records=cursor.fetchall()
            data=[]
            for record in request_records:
                record_id, user_name, book_name,request_date = record
                data.append({
                    'record_id':record_id,
                    'user_name':user_name,
                    'book_name':book_name,
                    'request_date':request_date
                })
            return Response({"data":data})

    def patch(self, request, record_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("select id ,book_id,status from borrow_records where id=%s and status='pending_approval'",[record_id])
                record = cursor.fetchone()
                if not record:
                    return Response({"error":"Borrow record not found or not in pending approval status."},status=status.HTTP_404_NOT_FOUND)
                # check book availability
                cursor.execute("select available_copies from Books where id=%s",[record[1]])
                book=cursor.fetchone()
                if not book or book[0]<1:
                    return Response({"error":"No copies available for this book."},status=status.HTTP_400_BAD_REQUEST)
                # approve the request
                cursor.execute("""
                    UPDATE borrow_records 
                    SET status = 'approved', borrow_approved_at = NOW()
                    WHERE id = %s
                """, [record_id])

                 # Decrease available copies
                cursor.execute("""
                    UPDATE Books 
                    SET available_copies = available_copies - 1 
                    WHERE id = %s
                """, [record[1]])  # book_id
                
                return Response({
                    "message": "Borrow request approved successfully",
                    "record_id": record_id,
                    "status": "approved"
                })
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ApproveReturnRequestView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    authentication_classes=[CustomJWTAuthentication]

    def get(self,request):
        with connection.cursor() as cursor:
            cursor.execute("""
                            select br.id as record_no,concat(u.first_name,' ',u.last_name)as name, b.title as book_name,date(return_requested_at) as request_date from borrow_records br 
            left join users u on br.user_id=u.id 
            left join Books b on br.book_id=b.id
            where br.status='return_requested'
            """)
            request_records=cursor.fetchall()
            data=[]
            for record in request_records:
                record_id, user_name, book_name,request_date = record
                data.append({
                    'record_id':record_id,
                    'user_name':user_name,
                    'book_name':book_name,
                    'request_date':request_date
                })
            return Response({"data":data})
    def patch(self,request,record_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                select id,book_id,status from borrow_records where id=%s and status='return_requested'""",[record_id])
                record=cursor.fetchone()
                if not record:
                    return Response({"error":"Return request not found or already processed."},status=status.HTTP_404_NOT_FOUND)
                cursor.execute("""
                        update borrow_records set status='return_verified',return_verified_at=NOW(),admin_notes=%s where id=%s""",[request.data.get('notes',''),record_id])
                cursor.execute("""
        
                        update Books set available_copies=available_copies + 1 where id=%s""",[record[1]])
                return Response({"message":"Return verified successfully","record_id":record_id},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)


class AllBorrowRecordsView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    authentication_classes=[CustomJWTAuthentication]
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                # Get all borrow records with user and book details
                cursor.execute("""
                    SELECT 
                        br.id, br.status, br.borrow_requested_at,
                        br.borrow_approved_at, br.return_requested_at,
                        br.return_verified_at, br.admin_notes,
                        u.email as user_email, u.first_name, u.last_name,
                        b.title as book_title, a.name as author_name
                    FROM borrow_records br
                    JOIN users u ON br.user_id = u.id
                    JOIN Books b ON br.book_id = b.id
                    JOIN Authors a ON b.author_id = a.id
                    ORDER BY br.borrow_requested_at DESC
                """)
                
                records = []
                for row in cursor.fetchall():
                    records.append({
                        'record_id': row[0],
                        'status': row[1],
                        'status_display': self.get_status_display(row[1]),
                        'borrow_requested_at': row[2],
                        'borrow_approved_at': row[3],
                        'return_requested_at': row[4],
                        'return_verified_at': row[5],
                        'admin_notes': row[6],
                        'user_email': row[7],
                        'user_name': f"{row[8]} {row[9]}",
                        'book_title': row[10],
                        'author_name': row[11]
                    })
                
                return Response({
                    'count': len(records),
                    'records': records
                })
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_status_display(self, status):
        status_map = {
            'pending_approval': 'Pending Approval',
            'approved': 'Borrowed',
            'rejected': 'Rejected',
            'return_requested': 'Return Requested',
            'return_verified': 'Returned',
            'damage_reported': 'Damage Reported'
        }
        return status_map.get(status, status)


import os
import uuid
from django.conf import settings 
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status


class ProfilePhotoUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[CustomJWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def get(self,request):
        user_id=request.user.id
        with connection.cursor() as cursor:
            cursor.execute("select profile_photo from users where id=%s",[user_id])
            user=cursor.fetchone()
            if not user:
                return Response({"error":"User not found"},status=status.HTTP_404_NOT_FOUND)
            return Response({"profile_photo":user[0]},status=status.HTTP_200_OK)

    def patch(self, request):
        user_id = request.user.id  # comes from JWT token

        if "profile_photo" not in request.FILES:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES["profile_photo"]

        # Ensure folder exists
        upload_dir = os.path.join(settings.MEDIA_ROOT, "profile_pictures")
        os.makedirs(upload_dir, exist_ok=True)

        # Delete any old files for this user (any extension)
        import glob
        old_files = glob.glob(os.path.join(upload_dir, f"{user_id}_profile_photo.*"))
        for old_file in old_files:
            try:
                os.remove(old_file)
            except FileNotFoundError:
                pass

        # Always save as <user_id>_profile_photo.<ext>
        ext = file.name.split(".")[-1]
        filename = f"{user_id}_profile_photo.{ext}"
        file_path = os.path.join(upload_dir, filename)

        # Save/overwrite file
        with open(file_path, "wb+") as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        # Relative path stored in DB
        relative_path = f"profile_pictures/{filename}"
        full_url = request.build_absolute_uri(settings.MEDIA_URL + relative_path)

        # Raw SQL update
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET profile_photo = %s WHERE id = %s",
                [full_url, user_id]
            )        

        return Response(
            {
                "message": "Profile photo updated",
                "profile_photo": full_url,  # frontend-ready full URL
            },
            status=status.HTTP_200_OK
        )


class MyAccountView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[CustomJWTAuthentication]
    def get(self,request):
        user_id=request.user.id
        with connection.cursor() as cursor:
            cursor.execute("""
                    select id,email,first_name,last_name,contact_no,address,profile_photo,created_at as joined_date from users where id=%s""",[user_id])
            user=cursor.fetchone()
            if not user:
                return Response({"error":"User not found"},status=status.HTTP_404_NOT_FOUND)
            user_data={
                "id":user[0],
                "email":user[1],
                "first_name":user[2],
                "last_name":user[3],
                "contact_no":user[4],
                "address":user[5],
                "profile_photo":user[6],
                "joined_date":user[7],
            }
            return Response(user_data,status=status.HTTP_200_OK)
    
    def patch(self,request):
        user_id=request.user.id
        allowed_fields = ['first_name', 'last_name', 'contact_no', 'address']
        update_data={}
        for field in allowed_fields:
            if field in request.data:
                update_data[field]=request.data[field]
        if not update_data:
            return Response({"message":"No fields provided for update"},status=status.HTTP_400_BAD_REQUEST)
        set_clause=", ".join([f"{field}=%s" for field in update_data.keys()])
        params=list(update_data.values()) + [user_id]
        with connection.cursor() as cursor:
            cursor.execute(f"update users set {set_clause} where id=%s",params)
            return Response({"message":"Account details updated successfully", "updated_fields": update_data},status=status.HTTP_200_OK)

class NotificationView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]

    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, DATE(created_at) as created_date
                FROM Books
                WHERE DATE(created_at) = CURDATE()
            """)
            books_added = cursor.fetchall()

        if books_added:
            book_list = [{"id": b[0], "title": b[1], "date": str(b[2])} for b in books_added]
            return Response({
                "message": f"{len(book_list)} new book added today"
               
            }, status=200)

        return Response({
            "message": "No new notification today."
           
        }, status=200)

class UserManagement(APIView):
    permission_classes=[IsAuthenticated,IsAdmin]
    authentication_classes=[CustomJWTAuthentication]
    def get(self,request):
        with connection.cursor() as cursor:
            cursor.execute("""
                select id , concat(first_name,' ',last_name) AS name ,email,contact_no,address,is_active from users where is_admin !=1""")
            user_data=cursor.fetchall()
            data=[]
            for record in user_data:
                id,name,email,contact_no,address,is_active=record
                data.append({
                    'id':id,
                    'name':name,
                    'email':email,
                    'contact_no':contact_no,
                    'address':address,
                    'is_active':"Active" if is_active==1 else "Inactive"
                })
            return Response({"data":data},status=200)
        
        
    
    def patch(self,request,id):
        status=request.data.get('action')
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                           select id from users where id=%s""",[id])
                data=cursor.fetchone()
                if data:
                    cursor.execute("""
                           update users set is_active=%s where id=%s""",[status,id])
                    return Response({"message":"User updated successfully"},status=200)
                return Response({"message":"User not found"},status=404)
        
        except Exception as e:
            return Response({"error":e})
    
    def delete(self,request,id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("select id from users where id=%s",[id])
                user=cursor.fetchone()
                if user:
                    cursor.execute("delete from users where id=%s",[id])
                    return Response({"message":"User deleted successfully."},status=200)
                return Response({"error":"User not found."},status=404)
        except Exception as e:
            return Response({"error":e})


