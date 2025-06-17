import os
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from datetime import datetime

# === MongoDB Connection ===
username = quote_plus('Tuba')
password = quote_plus('di+ig3n(')
uri = 'mongodb+srv://' + username + ':' + password + "@diamind.q4fmjuw.mongodb.net/?retryWrites=true&w=majority&appName=DiaMind"

# === Local Files Folder ===
LOCAL_FOLDER = "../data/"  

# === Connect to MongoDB ===
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["diabetes_data"]  # Replace with your database name
datasets_col = db["datasets"]
data_col = db["data_records"]

try:
    client.admin.command('ping')
    print("✅ Connected to MongoDB Atlas.")

    # === Upload Files ===
    for file_name in os.listdir(LOCAL_FOLDER):
        file_path = os.path.join(LOCAL_FOLDER, file_name)

        # Skip non-data files
        if not file_name.lower().endswith(('.csv', '.xlsx', '.xls', '.json')):
            print(f"Skipping unsupported file: {file_name}")
            continue

        # Check if file already uploaded
        existing = datasets_col.find_one({"file_name": file_name})
        if existing:
            print(f"⏭️ Skipping {file_name} (already uploaded)")
            continue

        print(f"📂 Processing {file_name}...")

        # Read file into DataFrame
        if file_name.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
        elif file_name.endswith(".json"):
            df = pd.read_json(file_path)

        # === Insert Metadata ===
        dataset_doc = {
            "file_name": file_name,
            "upload_date": datetime.now(),
            "n_rows": df.shape[0],
            "n_columns": df.shape[1],
            "columns": df.columns.tolist(),
            "missing_values": df.isnull().sum().to_dict(),
            "file_type": os.path.splitext(file_name)[-1].replace(".", ""),
            "file_path": file_path
        }

        dataset_id = datasets_col.insert_one(dataset_doc).inserted_id
        print(f"✅ Inserted metadata for {file_name}")

        # === Insert Data Records ===
        data_records = df.to_dict(orient="records")
        for record in data_records:
            record["dataset_id"] = dataset_id

        if data_records:
            data_col.insert_many(data_records)
            print(f"✅ Uploaded data records for {file_name}")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    client.close()
    print("🔒 MongoDB connection closed.")
