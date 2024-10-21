import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from myproject.models import UserFile

@login_required
def serve_protected_file(request, file_id):
    """Serves a file only if the user owns it."""
    # Get the file object, ensuring the user owns it
    user_file = get_object_or_404(UserFile, id=file_id, user=request.user)

    # Construct the file path in the private media directory
    file_path = os.path.join(settings.MEDIA_ROOT, str(user_file.file))

    # Check if the file exists
    if not os.path.exists(file_path):
        raise Http404("File does not exist")

    # Serve the file with FileResponse
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=user_file.name)
