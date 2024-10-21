# upload_files.py
import os

from django.conf import settings
from django.http import JsonResponse
from dotenv import load_dotenv, find_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from qdrant_client.models import Distance, VectorParams
from django.contrib.auth.decorators import login_required

# Load environment variables
_ = load_dotenv(find_dotenv())

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
qdrant_client = QdrantClient("localhost", port=6333)  # Adjust to your Qdrant configuration
collection_name = "my_collection"


@login_required
def index(request):
    if request.method == 'POST':
        # Define the folder where files are stored
        media_folder = os.path.join(settings.MEDIA_ROOT)

        # Get a list of all files in the media folder
        file_paths = [os.path.join(media_folder, file) for file in os.listdir(media_folder)]

        # Process the files and insert them into Qdrant
        try:
            # Load documents
            loaders = [PyPDFLoader(file_path) for file_path in file_paths]
            pages = []
            for loader in loaders:
                pages.extend(loader.load())

            # Split documents
            text_splitter = CharacterTextSplitter(
                separator="\n", chunk_size=1000, chunk_overlap=150, length_function=len
            )
            docs = text_splitter.split_documents(pages)

            # Create embeddings using OpenAI
            embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-ada-002")
            vectors = embeddings_model.embed_documents([doc.page_content for doc in docs])

            # Create Qdrant collection if it doesn't exist
            if not qdrant_client.collection_exists(collection_name=collection_name):
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
                )

            # Upload documents to Qdrant
            points = [
                PointStruct(id=i, vector=vector, payload={"page_content": docs[i].page_content})
                for i, vector in enumerate(vectors)
            ]
            qdrant_client.upsert(collection_name=collection_name, points=points)

            # Return success message
            return JsonResponse({'message': f"Inserted {len(points)} documents into Qdrant!"}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)
