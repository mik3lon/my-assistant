import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from dotenv import load_dotenv, find_dotenv
from qdrant_client import QdrantClient

from myproject.models import UserFile

# Load environment variables
_ = load_dotenv(find_dotenv())

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
qdrant_client = QdrantClient("localhost", port=6333)  # Adjust to your Qdrant configuration


@login_required
def my_assistant(request):
    user_files = UserFile.objects.filter(user=request.user)
    return render(request, 'my_assistant.html', {'user_files': user_files})
