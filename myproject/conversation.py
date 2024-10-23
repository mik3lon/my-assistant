from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from myproject.models import Conversation, Message

@login_required
def get_conversation(request, conversation_id):
    # Obtener la conversación asegurando que pertenece al usuario autenticado
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)

    # Obtener los mensajes asociados a esta conversación, ordenados por fecha de creación
    messages = conversation.messages.order_by('created_at').values('sender', 'content', 'created_at')

    # Crear una respuesta JSON con los detalles de la conversación y los mensajes
    data = {
        'conversation_id': conversation.id,
        'created_at': conversation.created_at,
        'messages': list(messages)
    }
    return JsonResponse(data)
