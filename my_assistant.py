import os

from dotenv import load_dotenv, find_dotenv
from langchain.chains import create_history_aware_retriever
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores.qdrant import Qdrant
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from qdrant_client.models import Distance, VectorParams

_ = load_dotenv(find_dotenv())

OPENAI_API_KEY=os.environ['OPENAI_API_KEY']

loaders = [
    PyPDFLoader("./Data/acta.pdf")
]

if __name__ == "__main__":
    collection_name = "my_collection"
    pages = []
    for loader in loaders:
        pages.extend(loader.load())

    # Split documents
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )

    docs = text_splitter.split_documents(pages)
    #
    # # Create embeddings using OpenAI
    embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-ada-002")
    #
    # # Generate embeddings for multiple documents using embed_documents
    vectors = embeddings_model.embed_documents([doc.page_content for doc in docs])
    #
    # # Initialize the Qdrant client (local or remote connection)
    qdrant_client = QdrantClient("localhost", port=6333)  # If you're running locally, adjust for your host

    # Define collection parameters
    if not qdrant_client.collection_exists(collection_name=collection_name):
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
        )

    # Upload documents to Qdrant
    points = [
        PointStruct(id=i, vector=vector, payload={"page_content": docs[i].page_content})
        for i, vector in enumerate(vectors)
    ]

    qdrant_client.upsert(
        collection_name=collection_name,
        points=points,
    )

    print(f"Inserted {len(points)} documents into Qdrant!")

    qdrant = Qdrant(qdrant_client, collection_name, embeddings_model)
    retriever = qdrant.as_retriever(search_type="similarity", search_kwargs={"k": 6})

    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-3.5-turbo-0125")


    # Define system prompts for reformulating questions
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

    # Create a retriever with history awareness
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

    # Example chat interaction
    chat_history = []

    # First question
    question = "¿En que fecha se celebró la reunion?"

    results = retriever.get_relevant_documents(question)

    # Check the retrieved documents
    for i, doc in enumerate(results):
        if not doc.page_content or not isinstance(doc.page_content, str):
            print(f"Invalid document at index {i}: {doc.page_content}")
        else:
            print(f"Valid document {i}: {doc.page_content[:100]}")  # Print first 100 characters of the document

    # Check the number of retrieved documents
    print(f"Number of retrieved documents: {len(results)}")

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question input must be a non-empty string")

    # Call the RAG chain with valid inputs
    ai_msg_1 = rag_chain.invoke({
        "input": question,  # Ensure question is a valid string
        "chat_history": chat_history  # Ensure chat history is in the correct format
    })

    # Update chat history with user input and AI response
    chat_history.extend([HumanMessage(content=question), ai_msg_1["answer"]])

    print(ai_msg_1["answer"])

    # Second question
    second_question = "¿Se aprobó la retirada del candado en el boton de apertura de la puerta para coches? ¿Con que porcentaje?"

    ai_msg_2 = rag_chain.invoke({"input": second_question, "chat_history": chat_history})
    print(ai_msg_2["answer"])

