# CEUR-WS Graph Retrieval Augmented Generation


## Table of Contents

## Table of Contents

- [Project Description](#project-description)
- [High-level application flow](#high-level-application-flow)
- [Installation](#installation)
  - [MongoDB](#mongodb)
  - [Neo4j](#neo4j)
  - [MongoDB Database Tools & mongoexport](#mongodb-database-tools--mongoexport)
  - [APOC](#apoc)
  - [Create Graph and import it into Neo4j using APOC](#create-graph-and-import-it-into-neo4j-using-apoc)
- [Application Usage](#application-usage)
  - [Install requirements](#install-requirements)
  - [OpenAI API Key](#openai-api-key)
  - [.env file](#env-file)
  - [Execute using main.py](#execute-using-mainpy)
  - [Limit number of nodes processed](#limit-number-of-nodes-processed)




## Project Description

This project is part of the "Technology for Big Data Management" course (http://didattica.cs.unicam.it/doku.php?id=didattica:ay2425:tbdm:main).
It aims to enable faster querying and access to the content of the [CEUR-WS website](https://ceur-ws.org/), a website which hosts scientific papers.
The project builds upon the work of my colleagues, who built a web scraper to extract metadata and content from the CEUR-WS volumes (https://github.com/AronOehrli/TBDM-CEUR-WS).
Having scraped the content of the CEUR website, and having extracted relevant metadata such as author, paper name, editor, volume in which the paper is published, we store this data in a graph database.

Since we have clear relationships between entities in this context (e.g. `Author -> WROTE -> Paper`, `Editor -> EDITED -> Volume`, `Paper -> BELONGS_TO -> Volume`), Graph RAG can leverage this inherent structure in the metadata.
We can represent the data as interconnected nodes and edges. 
This has several advantages:
- Normal RAG treats each document chunk independently, while Graph RAG captures relationships (e.g., which author wrote which paper, which editor is associated with a volume)
- For complex queries the graph structure allows for aggregation of related data
- The structured knowledge graph improves answer quality by providing rich context to the LLM



## High-level application flow

To enable Graph RAG we need to build a knowledge graph first.
This is done by forming a graph using the metadata provided by the web scraper. 
The nodes in the graph are then enriched with a semantic representation of their content, which is then queried to obtain relevant context.

1. The CEUR-WS website is scraped and metadata are extracted for each _Volume_ and _Paper_. This data is then stored in a MongoDB database.
2. The data is exported in JSON format from MongoDB and imported into Neo4j (a graph database) using APOC. Papers and Volumes form the nodes, alongside Authors and Editors. Relationships are formed between these nodes (wrote, edited_by, belongs_to).
3. For each Volume we take the text contained in the node and concatenate it to have a single chunk of information. This chunk is then passed to an _embedding model_, which is used to create a _vector embedding_ representing the semantic meaning of the chunk. This vector embedding is then added to the node.
4. An index is formed, containing all Volume nodes which were enriched with a vector embedding field 
5. Using a _Retriever_ we search the index using semantic similarity (cosine similarity, Euclidean distance) for the most relevant chunks based on the query
6. The retrieved chunks are used as entrypoints to the graph and the graph is traversed to extract the most relevant associated nodes.
7. Retrieved chunks and nodes are combined with the prompt and the user query and passed alongside to the LLM to generate an answer



## Installation

For the crawler component refer to https://github.com/AronOehrli/TBDM-CEUR-WS.
Following are the instructions to install and setup everything which will be needed to run this project.



### MongoDB

https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/#std-label-install-mdb-community-ubuntu

Install MongoDB
```shell
sudo apt-get update
sudo apt upgrade
sudo apt-get install -y mongodb-org
```

MongoDB post-installation
```shell
sudo systemctl start mongod
sudo systemctl status mongod
```

MongoDB start on boot
```shell
sudo systemctl enable mongod
```



### Neo4j

https://neo4j.com/docs/operations-manual/current/installation/linux/

Install openjdk 21, it is required by Neo4j
```shell
sudo apt update
sudo apt install openjdk-21-jdk -y
```

Verify java installation
```shell
java -version
```

Neo4j post-installation
```shell
sudo systemctl {start|stop|restart} neo4j
sudo systemctl status neo4j
```



### MongoDB Database Tools & mongoexport

Install database tools for mongoexport. These will allow us to export the contents of the database to JSON files.

https://www.mongodb.com/docs/database-tools/installation/installation-linux/

https://www.mongodb.com/docs/database-tools/mongoexport/

MongoDB check database content
```shell
mongosh
show dbs
use <database_name>
show collections
```

Export data from Mongo to JSON
```shell
mongoexport --collection=volumes --db=ceur_ws --out=volumes.json
mongoexport --collection=papers --db=ceur_ws --out=papers.json
```



### APOC

Get APOC for Neo4j. This will enable us to import the content of the JSON files generated above into Neo4j.

A word of caution: Since Neo4j 5 only the APOC-Core library is officially supported by Neo4j product and engineering. (Source: https://neo4j.com/labs/apoc/)

If you got the 2025 version of Neo4j then get APOC directly from github (https://github.com/neo4j/apoc)
```shell
sudo cp ~/Downloads/apoc-2025.02.0-core.jar /var/lib/neo4j/plugins/
sudo chown neo4j:neo4j /var/lib/neo4j/plugins/apoc-2025.02.0-core.jar
sudo systemctl restart neo4j
```

APOC post-installation 
(execute in APOC shell at http://localhost:7474/)
```shell
RETURN apoc.version() AS apocVersion
```

Check apoc.conf to enable imports from file
```shell
sudo nano /etc/neo4j/apoc.conf
```

Add the following to the file (ctrl + x to close, Y to accept changes to buffer)
```shell
apoc.import.file.enabled=true
```

Restart neo4j service after committing changes
```shell
sudo systemctl restart neo4j
```



### Create Graph and import it into Neo4j using APOC

Copy papers.json and volumes.json to Neo4j import dir
```shell
sudo cp /home/antonio/Desktop/papers.json /var/lib/neo4j/import
sudo cp /home/antonio/Desktop/volumes.json /var/lib/neo4j/import
```

Import the content of papers.json by executing the following import statement into the Neo4j console (http://localhost:7474/browser/). Default login to the console uses `user=neo4j` and `password=neo4j`. The first time you login you are asked to change the password.

```sql
// Load papers from Paper.json
CALL apoc.load.json("file:///papers.json") YIELD value AS paper
MERGE (p:Paper {id: paper._id['$oid']})
SET p.title = paper.title, p.pages = paper.pages, p.url = paper.url

// Create author nodes and relationships
FOREACH (authorName IN [x IN paper.author WHERE x IS NOT NULL] |
  MERGE (a:Author {name: authorName})
  MERGE (a)-[:WROTE]->(p)
)
  
// Link to volume node using volume_id
MERGE (v:Volume {id: paper.volume_id['$oid']})
MERGE (p)-[:BELONGS_TO]->(v);
```

Next import the content of the volumes.json file by executing the following import statement into the Neo4j console.
```sql
// Load volumes from Volume.json
CALL apoc.load.json("file:///volumes.json") YIELD value AS vol
MERGE (v:Volume {id: vol._id['$oid']})
SET v.title = vol.title,
    v.volnr = vol.volnr,
    v.urn = vol.urn,
    v.pubyear = vol.pubyear,
    v.volacronym = vol.volacronym,
    v.voltitle = vol.voltitle,
    v.fulltitle = vol.fulltitle,
    v.loctime = vol.loctime
// Create editor nodes and relationships
FOREACH (editorName IN [x IN vol.voleditor WHERE x IS NOT NULL] |
  MERGE (e:Editor {name: editorName})
  MERGE (v)-[:EDITED_BY]->(e)
);
```



## Application Usage

To run the application first you need to complete all the installation steps above.

### Install requirements
```shell
pip install -r requirements.txt
```



### OpenAI API Key
Assuming you have a properly formed graph in Neo4j, you can then run the ingestion pipeline once.
To run the ingestion pipeline you need to provide an OpenAI API key which you can get from here `https://platform.openai.com/api-keys`. 



### .env file

Create a `.env` file by copying the `example.env` file and renaming it to just `.env`.
The API key should go into the `.env` file



### Execute using main.py

The entrypoint for the application is the `main.py` file:
```python
def main():
    load_dotenv()
    # RUN JUST ONCE FOR SETUP
    # run_ingestion() 
    run_retrieval()
```

The first time you run the code, uncomment the `run_ingestion()` function, which will extract the first _N_ nodes from Neo4j and create a vector embedding out of the text of each entry. This vector embedding is then added to the original node, and will allow for semantic search.

For successive runs comment the `run_ingestion()` function again to avoid re-indexing the whole project over and over again.



### Limit number of nodes processed 
In the `config.ini` file there is a parameter which tells the ingestion pipeline how many entries to process at each run. This was done to avoid processing all the nodes in one go (I have 5090 Volume nodes in the database).

Change this value to index that many nodes:
```python
[indexer]
query_limit = 100
```



```shell
```

[//]: # ()
[//]: # (### Bugfixes to https://github.com/AronOehrli/TBDM-CEUR-WS)

[//]: # ( - does not read env variables, had to set them all as default. most likely issue is that the env file is nested inside the project instead of highest level)

[//]: # ( - missing init files completely, had to manually move the volume and paper classes &#40;data structures&#41; to the same folder as the scraper so that the imports work)

[//]: # ( - AttributeError: 'NoneType' object has no attribute 'find_all' breaking the code because it does not find ceur vol-nr, now ceur toc)
 
 
 
 
