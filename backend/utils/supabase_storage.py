from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "Docs")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_to_supabase(file_path: str, filename: str) -> str:
    """Upload file to Supabase storage and return public URL"""
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # Upload to Supabase storage
    response = supabase.storage.from_(BUCKET_NAME).upload(
        path=filename,
        file=file_data,
        file_options={"content-type": "application/octet-stream"}
    )
    
    # Get public URL
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(filename)
    
    return public_url
