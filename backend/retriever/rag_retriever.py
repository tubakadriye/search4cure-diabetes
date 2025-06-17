from typing import List
from PIL import Image
from io import BytesIO
from embeddings.clip import get_clip_embedding
from embeddings.gemini_text_embedding import get_gemini_embedding
from embeddings.sbert import get_sbert_embedding
from embeddings.voyage import get_voyage_embedding
from utils.gcs_utils import get_image_from_gcs



from typing import Union
from typing import List, Union
from PIL import Image
from io import BytesIO

from typing import Union
from typing import List, Union
from PIL import Image
from io import BytesIO

VS_INDEX_NAME = "multimodal_vector_index"

def vector_search(
    user_query: Union[str, Image.Image],
    model: str,
    collection:str,
    display_images: bool = True
) -> List[dict]:
    """
    Perform vector search using CLIP or SBERT, return matched GCS keys.
    
    Args:
        user_query (str or Image): Text or image input.
        model (str): One of "voyage", "clip", or "sbert".
        collection(str):
        display_images (bool): Show images if True.

    Returns:
        List[str]: GCS keys of matched items.
    """

    model_path_map = {
        "sbert": "sbert_text_embedding",
        "clip": "clip_text_embedding",  # for text query
        "clip_image": "clip_image_embedding",  # if image input
        "voyage": "voyage_embedding"  # optional
    }

    embedding_path = model_path_map.get(model)

   
    if embedding_path is None:
        raise ValueError(f"Unsupported or unconfigured model: {model}")
    
     # Compute the embedding vector
    if model == "clip":
        query_embedding = get_clip_embedding(user_query)
    elif model == "clip_image":
        if not isinstance(user_query, Image.Image):
             raise ValueError("clip_image model requires a PIL.Image input.")
        query_embedding = get_clip_embedding(user_query)
    elif model == "sbert":
        if not isinstance(user_query, str):
            raise ValueError("SBERT requires a text input.")
        query_embedding = get_sbert_embedding(user_query)
    elif model == "voyage":
        query_embedding = get_voyage_embedding(user_query, "query")
    else:
        raise ValueError(f"Model {model} not supported.")
    
    # Ensure query_embedding is a list of floats
    if not isinstance(query_embedding, list):
        query_embedding = query_embedding.tolist()
    
    pipeline = [
        {
            "$vectorSearch": {
                "index": VS_INDEX_NAME,
                "queryVector": query_embedding,
                "path": embedding_path,
                "numCandidates": 150,
                "limit": 20,
            }
        },
        {
            "$project": {
                "_id": 0,
                "gcs_key": 1,
                "width": 1,
                "height": 1,
                "score": {"$meta": "vectorSearchScore"},
                "pdf_title" : 1,
                "page_number":1,
                "sbert_text_embedding": 1,
                "clip_text_embedding": 1,
                "clip_image_embedding":1,
                "page_text": 1,
            }
        },
    ]

    results = collection.aggregate(pipeline)
    matched_docs = []

    for result in results:
        gcs_key = result["gcs_key"]
        result["image_bytes"] = get_image_from_gcs(gcs_key) 
        if display_images:
            img = Image.open(BytesIO(get_image_from_gcs(gcs_key)))
            print(f"{result['score']}\n")
            img.show()
        matched_docs.append(result)

    return matched_docs


def vector_search_for_csv(user_query, collection):
    """
    Perform a vector search in the MongoDB collection based on the user query.

    Args:
    user_query (str): The user's query string.
    collection (MongoCollection): The MongoDB collection to search.

    Returns:
    list: A list of matching documents.
    """

    # Generate embedding for the user query
    query_embedding = get_gemini_embedding(user_query)

    if query_embedding is None:
        return "Invalid query or embedding generation failed."

    # Define the vector search pipeline
    vector_search_stage = {
        "$vectorSearch": {
            "index": "vector_index_with_filter",
            "queryVector": query_embedding,
            "path": "embedding",
            "numCandidates": 150,  # Number of candidate matches to consider
            "limit": 5,  # Return top 4 matches
        }
    }

    unset_stage = {
        "$unset": "embedding"  # Exclude the 'embedding' field from the results
    }

    project_stage = {
        "$project": {
            "_id": 0,  # Exclude the _id field,
            "combined_info": 1,
            "score": {
                "$meta": "vectorSearchScore"  # Include the search score
            },
        }
    }

    pipeline = [vector_search_stage, unset_stage, project_stage]

    # Execute the search
    results = collection.aggregate(pipeline)
    return list(results)
