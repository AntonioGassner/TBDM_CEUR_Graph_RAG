from dotenv import load_dotenv
from src.indexer import Indexer
from src.retriever import Retriever


def run_ingestion():
    """
    Runs the ingestion process.
    This should be run only once to index your data and set up the vector index.
    """
    load_dotenv()
    indexer = Indexer()
    indexer.drop_vector_index("CEUR_WS_INDEX")
    indexer.create_vector_index()
    indexer.index()
    print("Ingestion complete.")

def run_retrieval():
    """
    Runs the retrieval process.
    This can be executed multiple times after ingestion.
    """
    load_dotenv()
    retriever = Retriever()
    retriever.retrieve()
    retriever.rag()

def main():
    load_dotenv()
    # RUN JUST ONCE FOR SETUP
    # run_ingestion()
    run_retrieval()





if __name__ == "__main__":
    main()
