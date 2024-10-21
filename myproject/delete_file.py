from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from myproject.models import UserFile
from django.contrib import messages  # Import messages for success or error notifications

@login_required
def delete_file(request, file_id):
    """Deletes a file uploaded by the user."""
    if request.method == 'POST':
        # Fetch the file object, ensuring the user is the owner
        file = get_object_or_404(UserFile, id=file_id, user=request.user)

        # Delete the file
        file.delete()

        messages.success(request, 'File delete successfully!')

        return JsonResponse({'status': 'success', 'message': 'File deleted successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
