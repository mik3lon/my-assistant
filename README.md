# PDF Question Answering App

## Overview

This application allows users to upload PDF documents, process their content using AI, and interact with a chatbot to ask questions about the uploaded documents. The system stores document embeddings in Qdrant, a vector database, and uses Redis for managing asynchronous tasks via Celery.

### Features
- **Google OAuth Login**: Secure login using Google OAuth 2.0.
- **PDF Upload**: Upload and manage your PDF documents.
- **Content Processing**: Extract meaningful embeddings from PDFs using Unstructured.
- **Vector Database Storage**: Store and retrieve embeddings efficiently using Qdrant.
- **AI Chat Interaction**: Engage with an AI-powered chatbot to query the content of the PDFs.
- **Task Management**: Use Celery and Redis to handle PDF processing asynchronously.

## Technology Stack
- **Backend**: Python with Django for handling views and requests.
- **AI Model**: Leverages advanced NLP models for embedding extraction and question answering.
- **Vector Database**: Qdrant for efficient similarity search.
- **Task Queue**: Celery with Redis for asynchronous task management.
- **Database**: SQLite for storing user and conversation data.

## Installation

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- Google Cloud Platform account for OAuth credentials

### Steps

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/your-repo/pdf-question-answering-app.git
    cd pdf-question-answering-app
    ```

2. **Set Up Python Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. **Run Docker Services**:
    ```bash
    docker-compose up -d
    ```

4. **Apply Migrations**:
    ```bash
    python manage.py migrate
    ```

5. **Configure Google OAuth**:
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Create a new project or select an existing one.
    - Navigate to **APIs & Services** > **Credentials**.
    - Create OAuth 2.0 credentials and configure the consent screen.
    - Add authorized redirect URIs (e.g., `http://localhost:8000/accounts/google/login/callback/`).
    - Download the credentials JSON file and place it in your project directory.
    - Set the required environment variables or add them to your `settings.py`:
      ```python
      SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '<your-client-id>'
      SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '<your-client-secret>'
      ```

6. **Start Django Server**:
    ```bash
    python manage.py runserver
    ```

7. **Start Celery Worker**:
    ```bash
    celery -A myproject worker --loglevel=info
    ```

## Usage

### Login with Google
1. Access the application at `http://localhost:8000`.
2. Click on "Login with Google" to authenticate.
3. Once authenticated, you can upload PDFs and interact with the chatbot.

### Load PDFs
1. After logging in, upload your PDF files.
2. The system will process the PDFs asynchronously, and embeddings will be stored in Qdrant.

### Chat with the AI
1. Navigate to the chatbot interface.
2. Ask questions about the uploaded PDFs.
3. The AI will retrieve relevant information and provide answers based on the document content.

## Architecture

### Backend
- **Django**: Handles web requests, renders views, and manages user sessions.
- **Google OAuth**: Enables secure login and user authentication.
- **Celery**: Manages asynchronous PDF processing tasks.
- **Redis**: Used as a message broker for Celery.

### Storage and Retrieval
- **Qdrant**: Stores embeddings for fast similarity searches.
- **SQLite**: Stores user data and conversation history.

### PDF Processing
- **Unstructured**: Extracts text and generates embeddings from uploaded PDFs.

## Docker Compose Configuration

The following services are defined in the `docker-compose.yml` file:

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334
      QDRANT__LOG_LEVEL: "info"

  redis:
    image: redis:latest
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: ["redis-server", "--appendonly", "yes"]
    restart: always

volumes:
  qdrant_storage:
    driver: local
  redis_data:
    driver: local
