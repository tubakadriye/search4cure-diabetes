import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
import gridfs

# === MongoDB connection ===
username = quote_plus('Tuba')
password = quote_plus('di+ig3n(')
uri = f'mongodb+srv://{username}:{password}@diamind.q4fmjuw.mongodb.net/?retryWrites=true&w=majority&appName=DiaMind'

client = MongoClient(uri, server_api=ServerApi('1'))
db = client["diabetes_data"]
fs = gridfs.GridFS(db)  # GridFS instance

local_folder = "../data/articles/"  

# === Walk through all subfolders ===
for root, dirs, files in os.walk(local_folder):
    for file_name in files:
        if file_name.lower().endswith('.pdf'):
            file_path = os.path.join(root, file_name)

            # Use relative path for uniqueness
            relative_path = os.path.relpath(file_path, local_folder)

            # Check if file already exists in GridFS
            existing = db.fs.files.find_one({"filename": file_name})
            if existing:
                print(f"❌ Skipping {file_name} (already uploaded)")
                continue

            with open(file_path, 'rb') as f:
                file_id = fs.put(f, filename=file_name)
                print(f"✅ Uploaded {file_name} to GridFS (ID: {file_id})")

client.close()
print("🔒 MongoDB connection closed.")
