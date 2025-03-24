from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.embeddings import OpenAIEmbeddings
import configparser
import os
from openai import OpenAI


class Retriever:
    def __init__(self, ini_file="config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(ini_file)
        self.driver = GraphDatabase.driver(
            self.config.get("neo4j", "uri"),
            auth=(
                self.config.get("neo4j", "user"),
                self.config.get("neo4j", "pass")
            ))
        self.index_name = self.config.get("indexer", "index_name")
        self.embedding_model = self.config.get("indexer", "embedding_model")
        self.embedder = OpenAIEmbeddings(model=self.embedding_model)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI()


    def retrieve(self):
        # Initialize the retriever
        retriever = VectorRetriever(self.driver, self.index_name, self.embedder)

        # Run the similarity search
        query_text = "Tell me about the preceedings done by CEUR"
        response = retriever.search(query_text=query_text, top_k=5)
        print("Chunks: ")
        print(response)

    def rag(self):
        # Initialize the retriever
        retriever = VectorRetriever(self.driver, self.index_name, self.embedder)

        # 3. LLM
        # Note: the OPENAI_API_KEY must be in the env vars
        llm = OpenAILLM(model_name="gpt-4o", model_params={"temperature": 0})

        # Initialize the RAG pipeline
        rag = GraphRAG(retriever=retriever, llm=llm)

        # Query the graph
        query_text = "Tell me about the preceedings done by CEUR"
        response = rag.search(query_text=query_text, retriever_config={"top_k": 5})
        print("Answer")
        print(response.answer)