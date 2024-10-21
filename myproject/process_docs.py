import os
import re  # New for text cleaning
from django.conf import settings
from django.http import JsonResponse
from dotenv import load_dotenv, find_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Use a more advanced text splitter
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from qdrant_client.models import Distance, VectorParams
from django.contrib.auth.decorators import login_required
from .models import UserFile

# Load environment variables
_ = load_dotenv(find_dotenv())

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
qdrant_client = QdrantClient("localhost", port=6333)  # Adjust to your Qdrant configuration

@login_required
def index(request):
    if request.method == 'POST':
        try:
            # Query the UserFile model to get files for the authenticated user
            user_files = UserFile.objects.filter(user=request.user)

            # Get the paths of the user's files
            file_paths = [os.path.join(settings.MEDIA_ROOT, user_file.file.name) for user_file in user_files]

            if not file_paths:
                return JsonResponse({'error': 'No files found for the user'}, status=404)

            # Process the files and insert them into Qdrant
            # Load documents
            loaders = [PyPDFLoader(file_path) for file_path in file_paths]
            all_pages = []
            file_to_pages_map = []  # To keep track of which file each page comes from
            for i, loader in enumerate(loaders):
                pages = loader.load()
                all_pages.extend(pages)
                file_to_pages_map.extend([user_files[i].file.name] * len(pages))  # Map each page to a file

            # Clean up the text within the document objects
            def clean_text(text):
                # Remove unwanted patterns like headers, footers, etc.
                text = re.sub(r'\n+', ' ', text)  # Normalize newlines
                text = re.sub(r'Page \d+', '', text)  # Remove page numbers
                text = text.strip()
                return text

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
            docs = text_splitter.split_documents(all_pages)  # Split after cleaning

            # Create embeddings using OpenAI
            embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-ada-002")
            vectors = embeddings_model.embed_documents([doc.page_content for doc in docs])

            collection_name = f'user_{request.user.id}'
            # Create Qdrant collection if it doesn't exist
            if not qdrant_client.collection_exists(collection_name=collection_name):
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
                )

            # Enhanced payload with additional metadata for better retrieval
            points = []
            for i, vector in enumerate(vectors):
                # Find the original file name for this document chunk
                original_file_name = file_to_pages_map[i // len(all_pages)]  # Map each chunk back to its file
                points.append(PointStruct(
                    id=i,
                    vector=vector,
                    payload={
                        "page_content": docs[i].page_content,
                        "file_name": original_file_name,  # Attach file name
                        "chunk_index": i  # Example of adding chunk index
                    }
                ))

            qdrant_client.upsert(collection_name=collection_name, points=points)

            return JsonResponse({'message': f"Loaded {len(points)} documents"}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)
