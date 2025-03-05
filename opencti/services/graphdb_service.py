import requests
import logging
import os
logger = logging.getLogger(__name__)
class GraphDBService:
    def __init__(self):
        self.repo_url = os.getenv("GRAPHDB_URL")  # Use environment variable
        self.auth = (
            (os.getenv("GRAPHDB_USER"), os.getenv("GRAPHDB_PASSWORD")) 
            if os.getenv("GRAPHDB_USER") 
            else None
        )
        self.query_url = self.repo_url.replace("/statements", "")

    def bulk_insert(self, rdf_data):
        """Insert RDF data into GraphDB and return detailed response"""
        try:
            response = requests.post(
                self.repo_url,  # Use instance variable, not hardcoded URL
                headers={"Content-Type": "application/x-turtle"},
                data=rdf_data,
                auth=self.auth,
                timeout=30  # Add timeout
            )

            if response.status_code == 204:
                return {
                    "success": True,
                    "message": "Data inserted successfully",
                    "triples_inserted": len(rdf_data.split('\n'))  # Estimate triples
                }
            else:
                return {
                    "success": False,
                    "message": f"Unexpected response: {response.status_code}",
                    "status_code": response.status_code,
                    "response_text": response.text
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error_type": type(e).__name__
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "success": False,
                "message": f"Processing error: {str(e)}",
                "error_type": type(e).__name__
            }

    def execute_query(self, sparql_query):
        """Execute SPARQL query with enhanced error handling"""
        try:
            response = requests.get(
                self.query_url,
                params={"query": sparql_query},
                headers={"Accept": "application/sparql-results+json"},
                auth=self.auth,
                timeout=30
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "results": response.json()["results"]["bindings"],
                "count": len(response.json()["results"]["bindings"])
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Query failed: {str(e)}")
            return {
                "success": False,
                "message": f"Query execution failed: {str(e)}",
                "error_type": type(e).__name__
            }