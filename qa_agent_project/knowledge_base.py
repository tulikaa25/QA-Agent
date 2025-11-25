import os
from typing import List, Dict, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from transformers import AutoTokenizer, AutoModel
import torch
import chromadb
from chromadb.utils import embedding_functions

class KnowledgeBase:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        try:
            # Initialize tokenizer and model for internal query embedding
            self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            self.model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

            # Use ChromaDB's native SentenceTransformerEmbeddingFunction for collection creation
            self.chroma_embedding_function_instance = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")

            self.collection = self.client.get_or_create_collection(
                name="qa_agent_knowledge_base",
                embedding_function=self.chroma_embedding_function_instance # Pass the ChromaDB embedding function instance
            )
            print("ChromaDB collection initialized.")
        except Exception as e:
            print(f"Error initializing ChromaDB collection: {e}")
            self.collection = None # Indicate failure to initialize
            self.tokenizer = None # Also indicate tokenizer/model failure
            self.model = None
            self.chroma_embedding_function_instance = None # Also indicate embedding function instance failure
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        print("Text splitter initialized.")

    def _get_embedding_function(self):
        """
        Returns an internal embedding function for query texts using the loaded tokenizer and model.
        This is separate from the embedding function used for collection creation.
        """
        if not self.tokenizer or not self.model:
            raise Exception("Tokenizer or model not initialized for embedding.")
        
        def embed_documents_for_query(texts: List[str]) -> List[List[float]]:
            inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
            with torch.no_grad():
                model_output = self.model(**inputs)
            embeddings = model_output.last_hidden_state[:, 0, :].cpu().numpy()
            return embeddings.tolist()
        return embed_documents_for_query


    def add_documents(self, contents: List[str], metadatas: List[Dict]) -> None:
        """
        Adds documents to the knowledge base after chunking. Embeddings are handled by ChromaDB.
        """
        if not self.collection or not self.chroma_embedding_function_instance:
            print("Cannot add documents: ChromaDB collection or its embedding function not initialized.")
            return

        for i, content in enumerate(contents):
            try:
                # Create a Langchain Document for chunking
                doc = Document(page_content=content, metadata=metadatas[i])
                chunks = self.text_splitter.split_documents([doc])

                # Prepare data for ChromaDB
                ids = [f"{metadatas[i].get('source_document', 'unknown')}_{j}" for j in range(len(chunks))]
                chunk_contents = [chunk.page_content for chunk in chunks]
                chunk_metadatas = [chunk.metadata for chunk in chunks]

                if chunk_contents:
                    # ChromaDB's native embedding function handles embedding during add.
                    self.collection.add(
                        documents=chunk_contents,
                        metadatas=chunk_metadatas,
                        ids=ids
                    )
                    print(f"Added {len(chunks)} chunks from {metadatas[i].get('source_document', 'unknown')}")
                else:
                    print(f"No chunks generated for {metadatas[i].get('source_document', 'unknown')}")
            except Exception as e:
                print(f"Error adding document {metadatas[i].get('source_document', 'unknown')}: {e}")

    def query(self, query_text: str, n_results: int = 5, where: Dict = None) -> Tuple[List[str], List[Dict]]:
        """
        Queries the knowledge base for relevant documents.
        """
        if not self.collection:
            print("Cannot query: ChromaDB collection not initialized.")
            return [], []

        if not self.collection or not self.tokenizer or not self.model:
            print("Cannot query: ChromaDB collection or internal embedding model not initialized.")
            return [], []

        try:
            # Generate embedding for the query text using the internal model
            query_embedding = self._get_embedding_function()([query_text])[0]

            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": n_results,
                "include": ['documents', 'metadatas']
            }
            if where is not None:
                query_params["where"] = where

            results = self.collection.query(**query_params)
            return results['documents'][0], results['metadatas'][0]
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return [], []
