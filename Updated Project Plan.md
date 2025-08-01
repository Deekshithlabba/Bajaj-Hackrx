# **Project Plan: HackRx 6.0 \- Universal Document Intelligence System**

## **1\. Vision & Objective**

To build a flexible, AI-powered system that can ingest unstructured documents from a URL, understand a user's natural language query, and provide a structured, reasoned, and citable answer based *only* on the content of the provided documents.

The system will employ a two-stage LLM architecture to dynamically adapt its reasoning process and output schema to any domain (e.g., insurance, legal, HR) without requiring domain-specific coding, directly addressing the core challenge of the HackRx 6.0 problem statement.

## **2\. Core Architecture: Two-Stage RAG with Advanced Parsing**

The system is built on a Retrieval-Augmented Generation (RAG) foundation, enhanced with advanced parsing capabilities and a two-stage LLM reasoning pipeline to maximize accuracy and explainability.

### **2.1. Advanced Ingestion & Indexing Pipeline (Offline)**

This pipeline runs for each document URL provided in an API call to prepare the content for querying.

graph TD  
    A\[Document URL\] \--\> B{Advanced Document Loaders};  
    B \-- Extracted Content \--\> C{Layout-Aware Parser};  
    C \-- Text Chunks & Tables \--\> D{Embedding Model};  
    C \-- Images \--\> E{Multimodal LLM};  
    E \-- Image Descriptions \--\> D;  
    D \-- Text & Image Embeddings \--\> F\[(Vector Database \- Pinecone)\];

    subgraph "Data Preparation & Indexing"  
        B\["Load from URL (PDF, DOCX)"\];  
        C\["Parse Text, Headings, Tables & Images"\];  
        E\["Describe Images / OCR"\];  
        D\["Generate Embeddings"\];  
        F\["Index in Pinecone"\];  
    end

### **2.2. Dynamic Querying Pipeline (Online)**

This pipeline executes in real-time for every user query, dynamically building the logic to answer it.

graph TD  
    subgraph "User Input"  
        Q\[User Query\];  
        Docs\[(Vector DB)\];  
    end

    subgraph "Stage 1: Task Analysis & Prompt Generation"  
        R\[Retriever\] \--\> LLM1\[LLM 1: Task Analyzer\];  
        Q \--\> R;  
        Docs \-- Sample Chunks \--\> R;  
    end

    subgraph "Stage 2: Domain Expertise & Answering"  
        FullR\[Full Retriever\] \--\> A\[Augmenter\];  
        LLM1 \-- Dynamic Instructions & JSON Schema \--\> A;  
        Q \--\> FullR;  
        Docs \-- All Relevant Chunks \--\> FullR;  
        A \-- Dynamically Assembled Prompt \--\> LLM2\[LLM 2: Domain Expert \- GPT-4\];  
    end

    subgraph "Final Output"  
        LLM2 \--\> O\[Structured JSON Output\];  
    end

    style LLM1 fill:\#f96,stroke:\#333,stroke-width:2px  
    style LLM2 fill:\#f96,stroke:\#333,stroke-width:2px  
    style O fill:\#9f9,stroke:\#333,stroke-width:2px

## **3\. Team Roles & Work Distribution (Team of 5\)**

### **Person 1: Advanced Data Ingestion Lead**

* **Responsibilities:**  
  1. **Document Loading:** Implement functions to fetch and load documents directly from blob storage URLs as specified in the hackathon API.  
  2. **Layout-Aware Parsing:** Use advanced libraries (e.g., PyMuPDF, unstructured.io) to parse documents while preserving structure. Identify headings, paragraphs, and lists.  
  3. **Table Extraction:** Implement robust table extraction logic (e.g., using camelot or multimodal vision models) to convert tabular data into a clean, LLM-friendly format like Markdown.  
  4. **Multimodal Processing:** Integrate a multimodal model (like Gemini/GPT-4 Vision) to process images, charts, and scanned text (OCR). Generate rich text descriptions for visual content.  
  5. **Chunking & Metadata:** Chunk the processed text, tables, and image descriptions, ensuring every chunk is tagged with rich metadata (source URL, page number, content type) for explainability.  
* **Primary Goal:** Create a sophisticated ingestion pipeline that transforms complex, multi-format documents into a structured, searchable knowledge base.

### **Person 2: Vector Database & Retrieval Specialist**

* **Responsibilities:**  
  1. **Vector DB Integration:** Set up and manage the **Pinecone** vector database as recommended. Handle API keys and environment setup.  
  2. **Embedding Model:** Integrate a high-performance embedding model.  
  3. **Indexing Pipeline:** Build the script that takes the diverse output from Person 1 (text, table, image chunks), generates embeddings, and indexes everything into Pinecone with its associated metadata.  
  4. **Optimized Retrieval:** Implement the retrieval function that performs a hybrid search if possible (semantic \+ keyword) to fetch the most relevant chunks for both the "Task Analyzer" and the "Domain Expert" LLMs.  
* **Primary Goal:** Build a fast, scalable, and highly accurate retrieval system using the recommended Pinecone stack.

### **Person 3: LLM Orchestration & Prompt Engineering Lead**

* **Responsibilities:**  
  1. **LLM API Integration (GPT-4):** Set up the connection to the **GPT-4** API. Manage API calls, focusing on **Token Efficiency** by optimizing context length and response size.  
  2. **Stage 1 \- Task Analyzer:** Design the crucial "meta-prompt" that instructs the first LLM to analyze the query/chunks and generate the persona, reasoning steps, and output JSON schema.  
  3. **Stage 2 \- Dynamic Prompt Assembly:** Write the core logic that programmatically assembles the prompt for the second LLM (the Domain Expert) using the output from Stage 1\.  
  4. **Tool/Function Calling:** Implement the function-calling mechanism to ensure the final output is always a valid, structured JSON that matches the dynamically generated schema. This is key for **Reusability**.  
* **Primary Goal:** Master the two-stage LLM workflow, ensuring the system is intelligent, adaptable, and token-efficient.

### **Person 4: Backend & API Architect (FastAPI)**

* **Responsibilities:**  
  1. **API Development:** Build the backend server using **FastAPI** as recommended.  
  2. **Hackathon Endpoint:** Implement the specific POST /hackrx/run endpoint. Ensure it correctly handles the Authorization: Bearer \<token\> header and the expected JSON payload (documents, questions).  
  3. **End-to-End Integration:** Act as the central integrator, connecting the work of Person 1, 2, and 3\. The API call should trigger the full pipeline: document fetching, indexing (if not already cached), and the two-stage query process.  
  4. **Performance & State:** Focus on **Latency**. Implement caching for document processing and indexing so that repeated queries on the same document are fast. Use **PostgreSQL** (as recommended) for logging, caching metadata, or managing job queues if needed.  
* **Primary Goal:** Build a performant, compliant, and scalable backend API that meets all hackathon specifications.

### **Person 5: Frontend & Explainability Lead**

* **Responsibilities:**  
  1. **UI/UX Design:** Design a clean interface for internal testing that allows the team to easily send requests to the backend API.  
  2. **Frontend Development:** Build the UI using a modern framework (e.g., React).  
  3. **API Interaction:** Implement the logic to send the correct JSON payload to the backend and handle the response.  
  4. **Explainability Visualization:** This is a key role. Create a compelling UI to render the structured JSON response. The UI should clearly display the final answer and the **Justification**, with clickable source references (e.g., "policy.pdf, Page 16") that show the exact text chunk used by the LLM. This directly addresses the **Explainability** evaluation criterion.  
* **Primary Goal:** Create a polished user interface that not only functions as a testing tool but also powerfully demonstrates the system's accuracy and traceability.

## **4\. Phased Execution Plan**

### **Phase I: Foundation & Core Components (Weeks 1-3)**

* **All:** Set up the development environment with FastAPI, Pinecone, and GPT-4 access.  
* **Person 1:** Implement loading from URL and advanced parsing for text and tables.  
* **Person 2:** Set up Pinecone and the indexing script. Achieve a basic text-to-vector-to-DB flow.  
* **Person 3:** Draft the "Task Analyzer" meta-prompt and the dynamic prompt assembler logic.  
* **Person 4:** Build the /hackrx/run endpoint that accepts the specified JSON and returns a mock response.  
* **Person 5:** Create the basic UI for submitting a document URL and a query.

### **Phase II: Integration & First End-to-End Flow (Weeks 4-6)**

* **Person 1 & 2:** Integrate the advanced parsing and indexing pipeline. A document URL should be fully processed and indexed in Pinecone.  
* **Person 3 & 4:** Integrate the full two-stage LLM logic into the backend. A query should now return a dynamically structured, reasoned JSON answer.  
* **Person 5:** Connect the frontend to the live backend and display the raw JSON response.  
* **Team Goal:** Achieve a fully functional end-to-end pipeline. Test rigorously with the "Known Documents" from the hackathon.

### **Phase III: Refinement & Optimization (Weeks 7-8)**

* **Person 1:** Add multimodal processing for images. Refine table extraction accuracy.  
* **Person 2:** Optimize retrieval logic (e.g., tuning 'k', experimenting with metadata filtering).  
* **Person 3:** Focus on **Token Efficiency**. Refine prompts to be more concise while maintaining accuracy.  
* **Person 4:** Focus on **Latency**. Implement caching and optimize the data flow to ensure responses are under 30 seconds.  
* **Person 5:** Build the final "Explainability" UI, beautifully rendering the citations and source text.  
* **Team Goal:** Harden the system, improve performance, and prepare for the "Unknown Documents".

### **Phase IV: Final Testing, Deployment & Submission (Weeks 9-10)**

* **Team:** Conduct final end-to-end testing with a focus on edge cases and potential errors.  
* **Person 4:** Deploy the final application to a public, HTTPS-enabled URL (e.g., on Heroku, Render).  
* **All:** Prepare the final submission, including code documentation. Double-check that all evaluation criteria are met.

## **5\. Technology Stack (HackRx 6.0 Recommended)**

* **Backend:** Python with **FastAPI**  
* **LLM:** **GPT-4** (or equivalent powerful model like Gemini Advanced)  
* **Vector Database:** **Pinecone**  
* **Database:** **PostgreSQL** (for caching, logging, or advanced state management)  
* **Frontend:** React (Recommended) or Vanilla JS with Tailwind CSS  
* **Deployment:** Heroku, Render, Railway, or other cloud platforms supporting Python.

## **6\. Meeting the HackRx 6.0 Evaluation Criteria**

* **Accuracy:** Addressed by advanced parsing (tables/images), high-quality embeddings, and the two-stage reasoning process.  
* **Token Efficiency:** A key responsibility of **Person 3**, who will optimize prompts to reduce cost and improve latency.  
* **Latency:** A key responsibility of **Person 4**, who will use caching and efficient integration to ensure fast response times.  
* **Reusability:** The core of the design. The Task Analyzer (Person 3's work) makes the system modular and adaptable to any document domain.  
* **Explainability:** Addressed by Person 1 (metadata tagging) and Person 5 (UI visualization), ensuring every answer is traceable back to its source.