BƯớc 1: Cài đặt PostgreSQL
Bước 2: Sử dụng PGadmin để tạo dự án chạy các script trong các file .sql
Bước 3: Fork dự án về máy và cài đặt các thư viện và framework cần thiết trong file requirement.txt
Bước 4: Tạo file .env theo cấu trúc sau:
.env
DATABASE_URL=postgresql://<user_name>:<password_postgre>@localhost:5432/<DB_Name>
FLASK_ENV=development
SECRET_KEY=your-random-secret-key   
