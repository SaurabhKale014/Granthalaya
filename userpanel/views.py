from django.db import connection
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import datetime
from adminpanel.authentication import CustomJWTAuthentication
from rest_framework.permissions import IsAuthenticated

class AvailableBooksView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[CustomJWTAuthentication]
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("select b.id,b.title ,a.name as Author_name,b.published_date from Books b left join Authors a on b.author_id=a.id where b.available_copies > 0;")
            # books=cursor.fetchall()
            # return Response(books)
            books=[]
            for row in cursor.fetchall():
                books.append({
                    'id': row[0],
                        'title': row[1],
                        'author_name': row[2],
                        'published_date': row[3]
                })
            return Response({
                'books':books
            })

# class BorrowRequestView(APIView):
#     def post(self, request, book_id):
#         try:
#             user_id=request.user.id
#             with connection.cursor() as cursor:
#                 cursor.execute("select id , available_copies from Books where id=%s",[book_id])
#                 book=cursor.fetchone()
#                 if not book:
#                     return Response({"error":"Book not found" },status=status.HTTP_404_NOT_FOUND)
#                 if book[1]<1:
#                     return Response({"error":"No copies available"},status=status.HTTP_404_NOT_FOUND)
                
#                 # Check if user already has pending/active request for this book
#                 cursor.execute("""
#                     SELECT id, status FROM borrow_records 
#                     WHERE user_id = %s AND book_id = %s 
#                     AND status IN ('pending_approval', 'approved')
#                 """, [user_id, book_id])
#                 existing_record=cursor.fetchone()
#                 if existing_record:
#                     return Response({"error":"You already have an active or pending request for this book."},status=status.HTTP_400_BAD_REQUEST)
        
#                 cursor.execute("""
#                     INSERT INTO borrow_records 
#                     (user_id, book_id, status, borrow_requested_at)
#                     VALUES (%s, %s, 'pending_approval', NOW())
#                 """, [user_id, book_id])
#                 return Response({"message":"Borrow request submitted successfully for admin approval."},status=status.HTTP_201_CREATED)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BorrowRequestView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[CustomJWTAuthentication]
    def post(self, request, book_id):
        try:
  
            user_id = request.user.id
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, available_copies FROM Books WHERE id=%s", [book_id])
                book = cursor.fetchone()
                if not book:
                    return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
                if book[1] < 1:
                    return Response({"error": "No copies available"}, status=status.HTTP_400_BAD_REQUEST)
                
                # Check if user already has pending/active request for this book
                cursor.execute("""
                    SELECT id, status FROM borrow_records 
                    WHERE user_id = %s AND book_id = %s 
                    AND status IN ('pending_approval', 'approved')
                """, [user_id, book_id])
                existing_record = cursor.fetchone()
                if existing_record:
                    return Response({"error": "You already have an active or pending request for this book."}, status=status.HTTP_400_BAD_REQUEST)
        
                cursor.execute("""
                    INSERT INTO borrow_records 
                    (user_id, book_id, status, borrow_requested_at)
                    VALUES (%s, %s, 'pending_approval', NOW())
                """, [user_id, book_id])
                
                return Response({"message": "Borrow request submitted successfully for admin approval."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReturnRequestView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[CustomJWTAuthentication]
    def patch(self,request,book_id):
        try:
            user_id = request.user.id
            with connection.cursor() as cursor:
                cursor.execute("select id from borrow_records where book_id=%s and user_id=%s and status='approved'",[book_id,user_id])
                borrow_record=cursor.fetchone()
                if not borrow_record:
                    return Response({"error":"No active borrowed book found for return"})
                record_id=borrow_record[0]
                cursor.execute("""
                               update borrow_records set status='return_requested', return_requested_at=NOW()  where id=%s""",[record_id])
                return Response({"message":"Return request submitted for admin verification."})
        except Exception as e :
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)


class MyBorrowedBooksView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[CustomJWTAuthentication]
    def get(self,request):
        try:
            user_id = request.user.id
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT br.id, b.title, a.name as author_name, 
                           b.isbn, br.borrow_approved_at, br.status
                    FROM borrow_records br
                    JOIN Books b ON br.book_id = b.id
                    JOIN Authors a ON b.author_id = a.id
                    WHERE br.user_id = %s 
                    AND br.status IN ('approved', 'return_requested')
                    ORDER BY br.borrow_approved_at DESC""",[user_id])
                borrowed_books=[]
                for row in cursor.fetchall():
                    borrowed_books.append({
                        'record_id':row[0],
                        'book_title':row[1],
                        'author_name':row[2],
                        'isbn':row[3],
                        'borrowed_date':row[4],
                        'status':row[5]
                    })
                return Response({
                    'count':len(borrowed_books),
                    'borrowed_books':borrowed_books
                })
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)

class BorrowingHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[CustomJWTAuthentication]
    def get(self, request):

        
        try:
            user_id = request.user.id
            
            with connection.cursor() as cursor:
                # Get complete borrowing history
                cursor.execute("""
                    SELECT br.id, b.title, a.name as author_name, 
                           b.isbn, br.status, br.borrow_requested_at,
                           br.borrow_approved_at, br.return_requested_at,
                           br.return_verified_at, br.admin_notes
                    FROM borrow_records br
                    JOIN Books b ON br.book_id = b.id
                    JOIN Authors a ON b.author_id = a.id
                    WHERE br.user_id = %s 
                    ORDER BY br.borrow_requested_at DESC
                """, [user_id])
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'record_id': row[0],
                        'book_title': row[1],
                        'author_name': row[2],
                        'isbn': row[3],
                        'status': row[4],
                        'status_display': self.get_status_display(row[4]),
                        'requested_at': row[5],
                        'approved_at': row[6],
                        'return_requested_at': row[7],
                        'return_verified_at': row[8],
                        'admin_notes': row[9]
                    })
                
                return Response({
                    'count': len(history),
                    'borrowing_history': history
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
