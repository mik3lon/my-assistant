from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import mimetypes
from myproject.models import UserFile
from myproject.tasks import process_uploaded_file  # Import Celery task


@login_required
def upload_file(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')

        uploaded_count = 0
        skipped_count = 0

        for uploaded_file in files:
            file_size = uploaded_file.size
            file_name = uploaded_file.name
            file_type, _ = mimetypes.guess_type(uploaded_file.name)

            # Check if a file with the same name and size already exists for the user
            existing_file = UserFile.objects.filter(user=request.user, name=file_name, length=file_size).first()

            if existing_file:
                # If a file with the same name and size exists, add an error message and skip uploading
                skipped_count += 1
                messages.error(request, f"The file '{file_name}' already exists (same name and size).")
                continue  # Skip to the next file in the loop

            # Save the file to the UserFile model if it's not a duplicate
            user_file = UserFile(
                user=request.user,
                file=uploaded_file,
                name=file_name,
                length=file_size,
                file_type=file_type or 'unknown'
            )
            user_file.save()
            uploaded_count += 1

            # Trigger Celery task to process the uploaded file asynchronously
            process_uploaded_file.delay(user_file.id)

        # Provide feedback based on the number of files uploaded and skipped
        if uploaded_count > 0:
            messages.success(request, f'{uploaded_count} file(s) uploaded successfully and are being processed.')
        if skipped_count > 0:
            messages.warning(request, f'{skipped_count} file(s) were skipped because they already exist.')

        return JsonResponse({'status': 'success', 'message': 'File uploaded successfully and processing started.'})

    else:
        # Fetch all files uploaded by the user
        user_files = UserFile.objects.filter(user=request.user)

    return render(request, 'upload.html', {'user_files': user_files})
