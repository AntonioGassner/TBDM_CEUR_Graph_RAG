# USEFUL CYPHER COMMANDS

This file contains some Cypher code which is generally useful for debugging or manually solving some issues.

List indices
```sql
SHOW INDEXES YIELD name, labelsOrTypes, properties
RETURN *
```

Drop Index
```sql
DROP INDEX index_name IF EXISTS
```

Check content of index cannot be done, so instead we determine which nodes are indexed by querying for the nodes that have the indexed property
```sql
MATCH (n)
WHERE n.embedding IS NOT NULL
RETURN n
```

To lookup only Volumes (or Papers)
```sql
MATCH (v:Volume)
WHERE v.embedding IS NOT NULL
RETURN v
```

Matches only Volumes which do not have the field _embedding_. Used to retrieve new nodes to index, to avoid re-indexing nodes which already have had a vector embedding added to them
```sql
MATCH (n:Volume) WHERE n.embedding IS NULL RETURN n LIMIT 20
```

