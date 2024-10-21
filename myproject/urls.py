from django.urls import path, include
from . import upload_files
from . import process_docs
from . import index
from . import serve_file
from django.conf.urls.static import static
from django.conf import settings

from .delete_file import delete_file
from .interaction import interact

urlpatterns = [
    path('', index.index, name='main'),

    path('upload-files/', upload_files.upload_file, name='upload_file'),
    path('process-docs/', process_docs.index, name='process_docs'),
    path('interact', interact, name='interacts'),
    path('delete-file/<int:file_id>/', delete_file, name='delete_file'),
    path('media/file/<int:file_id>/', serve_file.serve_protected_file, name='serve_protected_file'),

    path('accounts/', include('allauth.urls')),
    path('accounts/', include('allauth.socialaccount.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
