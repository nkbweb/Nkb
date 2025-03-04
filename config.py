import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://username:password@localhost/instagram_clon')
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cloudinary Configuration
    CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
    if CLOUDINARY_URL:
        cloudinary_parsed = urlparse(CLOUDINARY_URL)
        CLOUDINARY_CLOUD_NAME = cloudinary_parsed.hostname
        CLOUDINARY_API_KEY = cloudinary_parsed.username
        CLOUDINARY_API_SECRET = cloudinary_parsed.password
    else:
        CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', 'diyijlhyt')
        CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '169293457628317')
        CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', 'nuvzowumCQuL4voMZrf0loSBacc')
