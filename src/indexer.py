import configparser
import os
import neo4j_graphrag
from neo4j_graphrag.indexes import upsert_vectors
from neo4j_graphrag.types import EntityType
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.indexes import drop_index_if_exists
from openai import OpenAI
from src.utils import store_entries_in_file
from neo4j import GraphDatabase
from typing import List, Optional


class Indexer:
    def __init__(self, ini_file="config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(ini_file)
        self.driver = GraphDatabase.driver(
            self.config.get("neo4j", "uri"),
            auth=(
                self.config.get("neo4j", "user"),
                self.config.get("neo4j", "pass")
            ))
        self.dimension = self.config.getint("indexer", "dimension")
        self.index_name = self.config.get("indexer", "index_name")
        self.embedding_model = self.config.get("indexer", "embedding_model")
        self.query_limit = self.config.get("indexer", "query_limit")
        self.index_label = self.config.get("indexer", "index_label")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI()

        # For debugging: print the loaded configuration
        # self._print_config()

    def _print_config(self):
        print(f"  Driver: {self.driver}")
        print(f"  Dimension: {self.dimension}")
        print(f"  Index Name: {self.index_name}")
        print(f"  Embedding Model: {self.embedding_model}")
        print(f"  Large Language Model: {self.large_language_model}")
        print(f"  OPENAI_API_KEY: {'Set' if self.openai_api_key else 'Not Set'}")

    def index(self):
        # self.create_vector_index()
        volume_ids, volume_entries = self.get_formatted_entries("Volume")
        # paper_ids, paper_entries = self.get_formatted_entries("Paper")
        # store_entries_in_file(volume_entries)

        volume_embeddings = self.create_vector_embedding(volume_entries)
        # papers_embeddings = self.create_vector_embedding(paper_entries)

        self.upsert_vectors_preserve_properties(
            ids=volume_ids,
            embedding_property="embedding",
            embeddings=self.extract_embedding_vectors(volume_embeddings),
            neo4j_database="neo4j",
            )
        # self.upsert_vectors_preserve_properties(
        #     ids=paper_ids,
        #     embedding_property="vectorProperty",
        #     embeddings=self.extract_embedding_vectors(papers_embeddings),
        #     neo4j_database="neo4j",
        # )


    def extract_embedding_vectors(self, response):
        """
        Extracts a list of embedding vectors from a CreateEmbeddingResponse object.

        Parameters:
            response (CreateEmbeddingResponse): The response object returned from the OpenAI embedding model.
                It should have a 'data' attribute that is a list of Embedding objects, where each Embedding has
                an 'embedding' attribute containing a list of floats.

        Returns:
            list: A list of embedding vectors (each vector is a list of floats).
        """
        return [item.embedding for item in response.data]

    def fetch_nodes_by_label(self, label):
        """
        Fetch the first `limit` nodes with the given label from the Neo4j database,
        excluding nodes that already have an "embedding" property.
        Returns a list of nodes.
        """
        query = f"MATCH (n:{label}) WHERE n.embedding IS NULL RETURN n LIMIT {self.query_limit}"
        with self.driver.session() as session:
            result = session.run(query)
            nodes = [record["n"] for record in result]
        return nodes

    def format_node_properties(self, node):
        """
        Format the properties of a Neo4j node into a string, excluding the 'id' key.
        Each key-value pair is output as "key: value" on a new line.
        """
        properties = dict(node)
        # Remove the "id" property if it exists in the properties
        properties.pop("id", None)
        formatted = "\n".join(f"{key}: {value}" for key, value in properties.items())
        return formatted

    def get_formatted_entries(self, label):
        """
        Retrieve the first `limit` nodes with the given label,
        extract their IDs and formatted properties (without the 'id' key),
        and return two lists: one of IDs and one of formatted entries.
        """
        nodes = self.fetch_nodes_by_label(label)
        ids = []
        formatted_entries = []
        for node in nodes:
            # Use the internal node id attribute for the ID.
            node_id = (node.element_id)
            # node)["id"]
            ids.append(node_id)
            formatted_entries.append(self.format_node_properties(node))
        return ids, formatted_entries

    def create_vector_index(self):
        # Creating the index
        create_vector_index(
            self.driver,
            self.index_name,
            label=self.index_label,
            embedding_property="embedding",
            dimensions=self.dimension,
            similarity_fn="cosine",
            # Options: "cosine" or "euclidean".
            # Cosine is computationally more efficient,
            # and handles the case where embedding vectors are not normalized,
            # since it is less sensitive to magnitude differences
        )

    def check_index_info(self):
        return neo4j_graphrag.indexes.retrieve_vector_index_info(self.driver, self.index_name, "Volume", "embedding")

    def drop_vector_index(self, index_name):
        # Dropping the index if it exists
        drop_index_if_exists(
            self.driver,
            index_name,
        )

    def create_vector_embedding(self, entry):
        print("Creating Vector Embedding")
        return self.client.embeddings.create(
            model=self.embedding_model,
            input=entry,
            encoding_format="float"
        )

    def extract_embeddings(self, response):
        """
        Extract a list of embeddings from a vector embedding output.

        Parameters:
        CreateEmbeddingResponse:
            {
              "object": "list",
              "data": [
                {
                  "object": "embedding",
                  "embedding": [
                    0.0023064255,
                    -0.009327292,
                    .... (1536 floats total for ada-002)
                    -0.0028842222,
                  ],
                  "index": 0
                }
              ],
              "model": "text-embedding-ada-002",
              "usage": {
                "prompt_tokens": 8,
                "total_tokens": 8
              }
            }

        Returns:
            List[List[float]]: A list of embeddings (each embedding is a list of floats).
        """

        return [entry.embedding for entry in response.data]

    def ingest_vectors(self, embeddings, ids):
        print(f"Upserting vectors {ids}")
        try:
            upsert_vectors(
                self.driver,
                ids=ids,
                embedding_property="vectorProperty",
                embeddings=embeddings,
                neo4j_database="neo4j",
                entity_type=EntityType.NODE,
            )
        except Exception as e:
            print("Error during upsert_vectors:", e)

    def upsert_vectors_preserve_properties(
            self,
            ids: List[str],
            embedding_property: str,
            embeddings: List[List[float]],
            neo4j_database: Optional[str] = None,
    ) -> None:
        """
        Upserts (inserts or updates) the embedding field on existing nodes (matched by elementId)
        without removing the node's other properties.
        """
        if len(ids) != len(embeddings):
            raise ValueError("ids and embeddings must be the same length")
        if not all(len(embedding) == len(embeddings[0]) for embedding in embeddings):
            raise ValueError("All embeddings must be of the same size")

        # This query uses UNWIND to process each row,
        # MATCHes the node using elementId, and then sets only the embedding property.
        query = f"""
        UNWIND $rows AS row
        MATCH (n)
        WHERE elementId(n) = row.id
        SET n.{embedding_property} = row.embedding
        RETURN n
        """

        parameters = {
            "rows": [
                {"id": node_id, "embedding": embedding}
                for node_id, embedding in zip(ids, embeddings)
            ]
        }

        self.driver.execute_query(query_=query, parameters_=parameters, database_=neo4j_database)
