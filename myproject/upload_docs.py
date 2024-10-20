# upload_docs.py
import os

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from dotenv import load_dotenv, find_dotenv
from qdrant_client import QdrantClient

# Load environment variables
_ = load_dotenv(find_dotenv())

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
qdrant_client = QdrantClient("localhost", port=6333)  # Adjust to your Qdrant configuration
collection_name = "my_collection"

def index(request):
    if request.method == 'POST' and request.FILES.getlist('uploaded_files'):
        fs = FileSystemStorage()
        file_urls = []

        for uploaded_file in request.FILES.getlist('uploaded_files'):
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_urls.append(fs.url(filename))

        messages.success(request, 'Files uploaded successfully!')
        return render(request, 'upload.html', {'file_urls': file_urls})

    return render(request, 'upload.html')
