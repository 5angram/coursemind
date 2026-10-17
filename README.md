import pypandoc

readme = r"""# CourseMind

CourseMind is a local-first AI learning assistant designed to help students learn from YouTube courses using Retrieval-Augmented Generation (RAG).

Instead of asking an AI model to answer from general knowledge, CourseMind processes the content of a selected YouTube course, creates searchable vector representations of the course material, retrieves relevant sections for each question, and generates an answer using the retrieved course context.

The project combines a FastAPI backend, JavaScript-based frontend, embeddings, vector retrieval, and locally running Ollama models.

---

## Overview

Learning from long YouTube courses often requires repeatedly searching through lectures to find specific concepts, explanations, examples, or comparisons.

CourseMind aims to make this process easier by allowing a student to:

- Add a YouTube playlist/course
- Process its lectures and transcripts
- Search the course using natural-language questions
- Ask questions across the entire course
- Receive answers grounded in retrieved course content
- See the lectures used as sources
- Generate lecture summaries
- Continue conversations using follow-up questions

The system is designed around a Retrieval-Augmented Generation pipeline so that answers are based primarily on indexed course material.

---

## Key Features

### 1. YouTube Course / Playlist Processing

CourseMind accepts a YouTube playlist/course and processes its lectures.

The backend pipeline handles:

1. Playlist extraction
2. Video identification
3. Transcript retrieval
4. Transcript cleaning
5. Text chunking
6. Embedding generation
7. Vector storage

### 2. Transcript Processing

Lecture transcripts are processed before being used for retrieval.

The processing pipeline includes:

- Transcript extraction
- Text cleaning
- Chunk generation
- Metadata association with lectures

This makes long lecture transcripts easier to search and retrieve.

### 3. Embedding-Based Retrieval

Course chunks are converted into vector embeddings.

When a user asks a question:

```text
User Question
      ↓
Question Embedding
      ↓
Similarity Search
      ↓
Relevant Course Chunks
```

The retrieved chunks are then used to construct the context for answer generation.

### 4. Course-Level Question Answering

CourseMind supports asking questions across the selected course rather than limiting the user to a single lecture.

Example:

```text
What is the difference between BFS and DFS?
```

The system searches the indexed course content for relevant information and generates an answer using the retrieved course context.

### 5. Topic-Aware Retrieval

The question-handling pipeline considers the topic of the user's question during retrieval.

This helps with questions involving:

- Related concepts
- Comparisons
- Topic-specific explanations
- Follow-up questions

### 6. Follow-Up Questions

CourseMind supports conversational questions where a new question depends on the previous interaction.

Example:

```text
User:
What is merge sort?

User:
What is its time complexity?
```

The system can use conversation and topic information to resolve the follow-up question.

### 7. Source Lectures

Retrieved information can be associated with the lecture from which the relevant content was obtained.

This allows the learner to identify the source lecture and return to the original course material.

### 8. Lecture Summaries

CourseMind provides lecture-level summarization functionality so that students can quickly understand the main concepts covered in a lecture.

### 9. Local LLM Processing

CourseMind uses Ollama for local embedding and language-model operations.

This allows the project to run its AI pipeline locally instead of depending entirely on external AI APIs.

---

# How CourseMind Works

The overall workflow is:

```text
                    YouTube Playlist
                           │
                           ▼
                    Video Extraction
                           │
                           ▼
                    Transcript Fetching
                           │
                           ▼
                    Transcript Cleaning
                           │
                           ▼
                       Chunking
                           │
                           ▼
                     Embeddings
                           │
                           ▼
                     Vector Store
                           │
                           ▼
                    Course Indexed
                           │
                           │
                    ┌──────▼──────┐
                    │ User Query  │
                    └──────┬──────┘
                           │
                           ▼
                    Query Embedding
                           │
                           ▼
                  Similarity Retrieval
                           │
                           ▼
                 Topic / Context Handling
                           │
                           ▼
                  Retrieved Course Context
                           │
                           ▼
                    Ollama LLM
                           │
                           ▼
                    Grounded Answer
                           │
                           ▼
                 Answer + Source Lectures
```

---

# RAG Pipeline

CourseMind follows a Retrieval-Augmented Generation approach.

## Indexing Phase

During course indexing:

```text
YouTube Course
      ↓
Lectures
      ↓
Transcripts
      ↓
Cleaned Text
      ↓
Text Chunks
      ↓
Embeddings
      ↓
Vector Storage
```

## Question-Answering Phase

When a student asks a question:

```text
Question
   ↓
Question Embedding
   ↓
Similarity Search
   ↓
Relevant Chunks
   ↓
Context Construction
   ↓
Prompt Construction
   ↓
Local LLM
   ↓
Answer
```

---

# System Architecture

```text
┌─────────────────────────────────────────────┐
│                 Frontend                    │
│                                             │
│ HTML / CSS / JavaScript                     │
│ Course Onboarding / Lecture / Chat UI       │
└─────────────────────┬───────────────────────┘
                      │
                      │ HTTP API
                      ▼
┌─────────────────────────────────────────────┐
│              FastAPI Backend                │
│                                             │
│ Course APIs                                 │
│ Playlist Processing                         │
│ Question Handling                           │
│ Lecture Summarization                       │
└───────────────┬─────────────────────────────┘
                │
       ┌────────┴─────────┐
       │                  │
       ▼                  ▼
 Transcript Pipeline   Retrieval Pipeline
       │                  │
       ▼                  ▼
 Cleaning              Embeddings
 Chunking              Vector Search
       │                  │
       └────────┬─────────┘
                │
                ▼
        Context Construction
                │
                ▼
          Prompt Building
                │
                ▼
             Ollama
        ┌───────┴────────┐
        │                │
        ▼                ▼
   Embeddings        Generation
```

---

# Technology Stack

## Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- Requests
- NumPy

## AI / Machine Learning

- Ollama
- Embedding models
- Local LLM inference
- Retrieval-Augmented Generation (RAG)
- Vector similarity retrieval

## YouTube Processing

- yt-dlp
- youtube-transcript-api

## Frontend

- HTML
- CSS
- JavaScript

## Storage

Course processing data is stored locally under:

```text
backend/data/
```

Generated data can include:

- Course manifests
- Indexing job information
- Transcripts
- Summaries
- Vector data

---

# Project Structure

```text
CourseMind/
│
├── backend/
│   ├── app.py
│   ├── check_missing.py
│   ├── chunker.py
│   ├── cleaner.py
│   ├── context_builder.py
│   ├── course_pipeline.py
│   ├── embedding.py
│   ├── generate_manifests.py
│   ├── index_course_job.py
│   ├── llm.py
│   ├── playlist.py
│   ├── playlist_pipeline.py
│   ├── process_video.py
│   ├── prompt_builder.py
│   ├── question_handler.py
│   ├── retriever.py
│   ├── search.py
│   ├── transcript.py
│   ├── vector_store.py
│   ├── video_pipeline.py
│   │
│   └── data/
│       ├── course_manifests/
│       ├── index_jobs/
│       ├── summary/
│       ├── transcripts/
│       └── vector/
│
├── frontend/
│   ├── app.js
│   ├── index.html
│   ├── lecture.html
│   ├── lecture.css
│   ├── lecture.js
│   ├── onboarding.html
│   └── style.css
│
├── venv/
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Installation

## 1. Clone the Repository

```bash
git clone <your-github-repository-url>
cd CourseMind
```

## 2. Create a Virtual Environment

On Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

## 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

# Ollama Setup

CourseMind currently uses Ollama for local embedding and language-model operations.

Install Ollama separately and make sure the Ollama service is running.

The current implementation uses models such as:

```bash
ollama pull bge-m3
ollama pull llama3.2
```

Start Ollama if it is not already running:

```bash
ollama serve
```

The models can be changed in the project configuration/code if different local models are preferred.

---

# Running the Backend

From the project root:

```bash
uvicorn backend.app:app --reload
```

The FastAPI backend will then be available through the local server.

FastAPI's interactive API documentation can also be used to inspect and test the backend endpoints.

---

# Running the Frontend

Open the frontend application from the `frontend` directory using a local web server.

For example, using VS Code Live Server:

```text
frontend/index.html
```

The frontend communicates with the FastAPI backend through HTTP APIs.

---

# Example Workflow

### Step 1 — Add a Course

Provide a YouTube playlist/course URL.

```text
YouTube Playlist
       ↓
    CourseMind
```

### Step 2 — Process the Course

CourseMind extracts the lectures and processes their transcripts.

```text
Playlist
   ↓
Videos
   ↓
Transcripts
   ↓
Chunks
   ↓
Embeddings
```

### Step 3 — Open the Course

After indexing, the course can be accessed through the CourseMind interface.

### Step 4 — Ask Questions

Example:

```text
Explain binary search according to this course.
```

### Step 5 — Retrieve Relevant Content

CourseMind searches the indexed course vectors for relevant chunks.

### Step 6 — Generate the Answer

The retrieved content is supplied to the local LLM as context.

```text
Retrieved Course Context
          +
       User Query
          ↓
      Local LLM
          ↓
        Answer
```

### Step 7 — Continue the Conversation

The learner can ask follow-up questions without restarting the interaction.

---

# Grounding Approach

A major goal of CourseMind is to reduce unsupported answers by providing the language model with retrieved course context.

The question-answering pipeline follows:

```text
User Question
      ↓
Retrieve Relevant Course Content
      ↓
Build Context
      ↓
Build Prompt
      ↓
Generate Answer
```

The model is instructed to use the supplied course context rather than freely inventing course-specific information.

However, Retrieval-Augmented Generation does not guarantee perfect factual accuracy. Generated answers should still be verified against the original lecture when accuracy is important.

---

# Limitations

### Transcript Dependency

The quality of the system depends on the availability and quality of YouTube transcripts.

### Retrieval Quality

Poor transcript segmentation, embeddings, or similarity retrieval can result in less relevant context.

### Local Hardware

Because Ollama models run locally, response speed and model capability depend on the available hardware and selected model.

### LLM Accuracy

Even when provided with retrieved context, an LLM can occasionally produce an inaccurate interpretation of that context.

### Course Data

Processed course data is generated locally and is not intended to be committed to the Git repository.

---

# Future Improvements

Potential improvements include:

- Hybrid keyword + vector retrieval
- Reranking retrieved chunks
- More advanced vector database integration
- Better transcript fallback mechanisms
- Improved retrieval evaluation
- Automated RAG evaluation
- More configurable embedding and LLM models
- User authentication
- Persistent course/user databases
- Background job queue for large courses
- Cloud deployment
- Better conversation memory
- Improved lecture recommendations
- Progress tracking for learners

---

# Why CourseMind?

CourseMind demonstrates the integration of several technologies into one practical AI application:

- Full-stack web development
- FastAPI backend development
- YouTube data processing
- Natural-language processing
- Text chunking
- Embeddings
- Vector similarity search
- Retrieval-Augmented Generation
- Local LLM inference
- Conversational question answering
- Frontend/backend API integration

The project is designed as a practical application of RAG rather than a standalone chatbot.

---

# Project Status

CourseMind is an actively developed project.

The current implementation includes:

- YouTube course/playlist processing
- Transcript processing
- Text chunking
- Embedding generation
- Vector retrieval
- Course-level question answering
- Follow-up question handling
- Topic-aware retrieval
- Lecture summarization
- Source lecture information
- Local Ollama inference
- Web-based frontend

---

## License

No license has been specified for this project yet.
"""

out = "/mnt/data/CourseMind_README.md"
pypandoc.convert_text(readme, "md", format="md", outputfile=out, extra_args=["--standalone"])
print(out)
print("README lines:", len(readme.splitlines()))
