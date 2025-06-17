from loaders.arxiv_loader import ArxivPDFLoader
from loaders.pubmed_loader import PubMedPDFLoader
from loaders.user_pdf_loader import load_user_pdfs
from multimodal.pdf_processing import process_pdfs_and_upload_images  
from embeddings.image_embedding_pipeline import embed_docs_with_clip
 
from embeddings.voyage import get_voyage_embedding
from embeddings.clip import get_clip_embedding
from db.index_utils import create_vector_index
from db.mongodb_client import mongodb_client
from db.index_utils import create_multivector_index
from multimodal.pdf_processing import process_and_embed_docs


# 0. Load user PDFs (if any exist in a predefined folder or input source)
user_pdfs = load_user_pdfs()  # returns same format as arxiv_pdfs/pubmed_pdfs

# 1. Load from Arxiv
arxiv_loader = ArxivPDFLoader(query="Diabetes")
arxiv_pdfs = arxiv_loader.download_pdfs()

# 2. Load from PubMed
pubmed_loader = PubMedPDFLoader(query="Diabetes")
pubmed_pdfs = pubmed_loader.download_pdfs()

# 3. Combine
all_pdfs = user_pdfs+ arxiv_pdfs + pubmed_pdfs

# 4. Process + upload to GCS + Generate multimodal embeddings
embedded_docs = process_pdfs_and_upload_images(all_pdfs)

# 5. Generate multimodal embeddings
#embedded_docs = embed_docs_with_clip(docs, get_clip_embedding)

# 6. Insert to MongoDB
# Connect to the MongoDB collection
db = mongodb_client["diabetes_data"]
collection = db["docs_multimodal"]

try:
    # Optional: Clear previous docs
    # collection.delete_many({})

    collection.insert_many(embedded_docs)
    print(f"Inserted {len(embedded_docs)} documents.")

    create_vector_index(
        db=db,
        collection_name="docs_multimodal",
        index_name="image_vector_index",
        field_name="clip_embedding",
        num_dimensions=512,
    )

    create_multivector_index(
    db=db,
    collection_name="docs_multimodal",
    index_name="multimodal_vector_index"
    )   
    
    print("Vector index created successfully.")

except Exception as e:
    print(f"Error inserting docs or creating index: {e}")