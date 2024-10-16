# views.py
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib import messages

def upload_files(request):
    if request.method == 'POST' and request.FILES.getlist('uploaded_files'):
        fs = FileSystemStorage()
        file_urls = []

        for uploaded_file in request.FILES.getlist('uploaded_files'):
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_urls.append(fs.url(filename))

        messages.success(request, 'Files uploaded successfully!')
        return render(request, 'upload.html', {'file_urls': file_urls})

    return render(request, 'upload.html')

def process_docs(request):
    # Logic to process the uploaded documents
    messages.success(request, 'Documents processed successfully!')
    return render(request, 'processed.html')
