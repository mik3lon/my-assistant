import json
import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from dotenv import load_dotenv, find_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.vectorstores import Qdrant
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from qdrant_client import QdrantClient
from .models import Conversation, Message  # Import the models

# Load environment variables
_ = load_dotenv(find_dotenv())

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
qdrant_client = QdrantClient("localhost", port=6333)  # Adjust to your Qdrant configuration

@login_required
def interact(request):
    if request.method == 'POST':
        try:
            # Extract the JSON data from the request
            data = json.loads(request.body)
            question = data.get('question', '')
            conversation_id = data.get('conversation_id', None)

            if not isinstance(question, str) or not question.strip():
                return JsonResponse({'error': 'Question input must be a non-empty string'}, status=400)

            # Check if the conversation ID is provided
            if conversation_id:
                # Fetch the existing conversation
                try:
                    conversation = Conversation.objects.get(id=conversation_id, user=request.user)
                except Conversation.DoesNotExist:
                    return JsonResponse({'error': 'Conversation not found'}, status=404)
            else:
                # Create a new conversation
                conversation = Conversation.objects.create(user=request.user)

            # Retrieve previous messages as chat history for the conversation
            chat_history = [
                HumanMessage(content=msg.content) if msg.sender == 'user' else msg.content
                for msg in conversation.messages.all().order_by('created_at')
            ]

            collection_name = f'user_{request.user.id}'
            embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-ada-002")
            qdrant = Qdrant(qdrant_client, collection_name, embeddings_model)
            retriever = qdrant.as_retriever(search_type="similarity", search_kwargs={"k": 20})

            llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o-mini-2024-07-18")

            system_prompt = """Given the chat history and a recent user question \
            generate a new standalone question \
            that can be understood without the chat history. Do NOT answer the question, \
            just reformulate it if needed or otherwise return it as is."""

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )

            retriever_with_history = create_history_aware_retriever(
                llm, retriever, prompt
            )

            # Define QA system prompt
            qa_system_prompt = """You are an assistant for question-answering tasks. \
            Use the following pieces of retrieved context to answer the question. \
            If you don't know the answer, just say that you don't know. \
            Use five sentences maximum and keep the answer concise. \
            You should return the reference of the data or the documentation.
        
            {context}"""

            qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", qa_system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )

            # Create question-answering chain
            question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

            # Create a retrieval chain with the history-aware retriever and question-answering chain
            rag_chain = create_retrieval_chain(retriever_with_history, question_answer_chain)

            # Call the RAG chain with valid inputs
            ai_msg_1 = rag_chain.invoke({
                "input": question,  # Use the question extracted from the POST request
                "chat_history": chat_history  # Ensure chat history is in the correct format
            })

            ai_response = ai_msg_1["answer"]

            # Update chat history with user input and AI response
            Message.objects.create(conversation=conversation, sender='user', content=question)
            Message.objects.create(conversation=conversation, sender='ai', content=ai_response)

            return JsonResponse({'conversation_id': str(conversation.id), 'response': ai_response}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)
