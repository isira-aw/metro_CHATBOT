import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List

load_dotenv()

class PineconeService:
    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.initialize()
    
    def initialize(self):
        try:
            # Initialize embeddings
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("⚠️ GOOGLE_API_KEY not found")
                return
                
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=google_api_key
            )
            
            # Initialize Pinecone
            try:
                from pinecone import Pinecone, ServerlessSpec
                from langchain_pinecone import Pinecone as PineconeVectorStore
                
                pinecone_api_key = os.getenv("PINECONE_API_KEY")
                if not pinecone_api_key:
                    print("⚠️ PINECONE_API_KEY not found")
                    return
                
                pc = Pinecone(api_key=pinecone_api_key)
                index_name = os.getenv("PINECONE_INDEX_NAME", "chatbot-knowledge")
                
                # Check if index exists
                existing_indexes = [idx.name for idx in pc.list_indexes()]
                
                if index_name not in existing_indexes:
                    pc.create_index(
                        name=index_name,
                        dimension=768,
                        metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="us-east-1")
                    )
                
                self.vector_store = PineconeVectorStore.from_existing_index(
                    index_name=index_name,
                    embedding=self.embeddings
                )
                
                print("✅ Pinecone initialized")
                
            except Exception as e:
                print(f"⚠️ Pinecone initialization failed: {e}")
                
        except Exception as e:
            print(f"⚠️ Embeddings initialization failed: {e}")
    
    def add_documents(self, text: str, metadata: dict = None) -> int:
        if not self.vector_store or not self.embeddings:
            raise Exception("Vector store not initialized. Check API keys and quota.")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        chunks = text_splitter.split_text(text)
        
        documents = [
            Document(page_content=chunk, metadata=metadata or {})
            for chunk in chunks
        ]
        
        self.vector_store.add_documents(documents)
        
        return len(chunks)
    
    def search_similar(self, query: str, k: int = 3) -> List[Document]:
        if not self.vector_store:
            return []
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"⚠️ Search failed: {e}")
            return []
    
    def get_retriever(self, k: int = 3):
        """Get a retriever for RAG pipeline"""
        if not self.vector_store:
            return None
        try:
            return self.vector_store.as_retriever(search_kwargs={"k": k})
        except Exception as e:
            print(f"⚠️ Retriever creation failed: {e}")
            return None