"""Thin Neo4j wrapper for the cognitive-substrate build (PrimeKG)."""
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "primekg123")


class Graph:
    def __init__(self, uri: str = URI, auth: tuple = AUTH):
        self._driver = GraphDatabase.driver(uri, auth=auth)

    def query(self, cypher: str, **params) -> list[dict]:
        with self._driver.session() as session:
            return [record.data() for record in session.run(cypher, **params)]

    def close(self) -> None:
        self._driver.close()
