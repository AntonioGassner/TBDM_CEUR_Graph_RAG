from dotenv import load_dotenv
from src.indexer import Indexer

def main():
    load_dotenv()

    indexer = Indexer()

    # For Volume entries:
    formatted_volumes = indexer.get_formatted_entries("Volume", limit=10)
    print("Volumes\n")
    for entry in formatted_volumes:
        print(entry)
        print("-" * 40)

    # For Paper entries:
    formatted_papers = indexer.get_formatted_entries("Paper", limit=10)
    print("Papers\n")
    for entry in formatted_papers:
        print(entry)
        print("-" * 40)


if __name__ == "__main__":
    main()

# response_str = repr(self.extract_embedding_vectors(volume_embeddings))
#
#         with open("embedding_response_clean.txt", "w") as file:
#             file.write(response_str)
