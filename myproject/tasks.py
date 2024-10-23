# tasks.py
import os
import re

from langchain.text_splitter import RecursiveCharacterTextSplitter  # Use a more advanced text splitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv, find_dotenv

from celery import shared_task
from .models import UserFile

# Load environment variables
_ = load_dotenv(find_dotenv())

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
qdrant_client = QdrantClient("localhost", port=6333, timeout=120)  # Adjust to your Qdrant configuration


@shared_task
def process_uploaded_file(user_file_id):
    try:
        # Get the uploaded file instance
        user_file = UserFile.objects.get(id=user_file_id)

        # You can update the status of the file if you track progress in your model
        user_file.status = 'IN_PROGRESS'
        user_file.save()

        # Process the file (e.g., generate embeddings, store in Qdrant, etc.)
        file_path = user_file.file.path
        loader = PyPDFLoader(file_path)

        all_pages = loader.load()
        file_to_pages_map = [user_file.file.name] * len(all_pages)  # Associate each page with the file name

        # Apply cleaning to each page's content while preserving the document structure
        for page in all_pages:
            page.page_content = clean_text(page.page_content)

        # Use a more advanced text splitter that respects paragraphs or semantic boundaries
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?"]  # Prioritize splitting on sentences and paragraphs
        )

        docs = []
        chunk_file_map = []

        # Split the text of each page into chunks and track which file they belong to
        for i, page in enumerate(all_pages):
            page_chunks = text_splitter.split_text(page.page_content)  # Split page into chunks
            docs.extend(page_chunks)  # Add chunks to docs
            chunk_file_map.extend([user_file.file.name] * len(page_chunks))  # Track the file for each chunk

        # Create embeddings using OpenAI
        embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-ada-002")
        vectors = embeddings_model.embed_documents([chunk for chunk in docs])

        collection_name = f'user_{user_file.user.id}'
        # Create Qdrant collection if it doesn't exist
        if not qdrant_client.collection_exists(collection_name=collection_name):
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
            )

        # Enhanced payload with additional metadata for better retrieval
        points = []
        for i, vector in enumerate(vectors):
            # Use `chunk_file_map` to get the correct file name for each chunk
            original_file_name = chunk_file_map[i]
            points.append(PointStruct(
                id=i,
                vector=vector,
                payload={
                    "page_content": docs[i],
                    "file_name": original_file_name,  # Attach correct file name
                    "chunk_index": i  # Add chunk index for reference
                }
            ))

        batch_upsert(collection_name, points, batch_size=50)

        # Update file status when processing is complete
        user_file.status = 'COMPLETED'
        user_file.save()

    except Exception as e:
        # Handle any errors that occur during processing
        user_file.status = 'FAILED'
        user_file.save()
        raise e


def batch_upsert(collection_name, points, batch_size=50):
    """Upserts points into Qdrant in batches."""
    for i in range(0, len(points), batch_size):
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points[i:i + batch_size]
        )

# Clean up the text within the document objects
def clean_text(text):
    """Cleans text by removing unwanted patterns like headers, footers, etc."""
    text = re.sub(r'\n+', ' ', text)  # Normalize newlines
    text = re.sub(r'Page \d+', '', text)  # Remove page numbers
    text = text.strip()
    return text
