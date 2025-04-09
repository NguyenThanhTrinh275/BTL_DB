class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:trinhbanh@localhost/BTL_Database'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your-secret-key'  # Dùng để mã hóa session, đặt một chuỗi ngẫu nhiên