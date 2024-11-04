from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from myproject.models import Conversation, Message

@login_required
def delete_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)

    Message.objects.filter(conversation=conversation).delete()

    conversation.delete()

    return JsonResponse({'status': 'success', 'message': 'Conversation deleted successfully'})
