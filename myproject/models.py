from django.db import models
import uuid
from django.contrib.auth.models import User

def user_directory_path(instance, filename):
    return f'user_{instance.user.id}/{filename}'

class UserFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path)
    name = models.CharField(max_length=255)
    length = models.IntegerField()
    file_type = models.CharField(max_length=50)
    upload_date = models.DateTimeField(auto_now_add=True)

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation {self.id} with {self.user.username}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=50)  # Could be 'user' or 'ai'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} in Conversation {self.conversation.id}"
