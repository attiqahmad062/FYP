from flask import Flask, request, jsonify
import subprocess
# from SPARQLWrapper import SPARQLWrapper, JSON ,POST,GET
from rdflib import Graph, Namespace
from flask import Flask
from flask_jwt_extended import JWTManager,create_access_token 
from dotenv import load_dotenv
from opencti.routes import opencti_bp
import os
from flask_cors import CORS
from collections import defaultdict
# from tutorial.tutorial.spiders.mittreattack import mittreattack 
## dummy code
# GraphDB connection settings
GRAPHDB_ENDPOINT = "http://localhost:7200/repositories/etiapt/statements"  # Replace with actual endpoint
GRAPHDB_SETTINGS = {
    'endpoint': 'http://localhost:7200/repositories/etiapt/statements',
    'prefix': 'https://attack.mitre.org/'
}
load_dotenv()
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")
JWTManager(app)
CORS(app) 
# Register OpenCTI Blueprint
app.register_blueprint(opencti_bp, url_prefix='/api/opencti')
# crawler driver code
@app.route('/test-graphdb')
def test_graphdb():
    from opencti.services.graphdb_service import GraphDBService
    graphdb = GraphDBService()
    
    test_query = """
        SELECT * WHERE {
            ?s ?p ?o
        } LIMIT 1
    """
    
    try:
        results = graphdb.execute_query(test_query)
        if results:
            return jsonify({
                "status": "success",
                "results": results.get("results", {}).get("bindings", [])
            })
        return jsonify({"status": "empty", "message": "No data found"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    # Validate credentials (example)
    if username != "admin" or password != "admin":
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Create JWT token
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)
@app.route('/scrape', methods=['POST','GET'])
def scrape():
    try:
        # Run Scrapy spider
        subprocess.run(['scrapy', 'crawl', "mitreattack"], cwd='tutorial', check=True)
        return jsonify({'status': 'success', 'message': f'Spider {spider_name} executed successfully'})
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
 


@app.route('/groups', methods=['GET'])
def get_groups():
    try:
        # Load the RDF Graph from GraphDB
        graph = Graph()
        graph.parse(GRAPHDB_ENDPOINT, format="xml")

        # Define Namespace
        ex = Namespace("https://attack.mitre.org/")

        # SPARQL Query (RDFLib style)
        query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?groupName ?groupId ?description
        WHERE {
            ?groupName a ex:groups ;
                       ex:groupId ?groupId .
            OPTIONAL { ?groupName ex:use ?description . }  
        }
        """
        # Run the Query
        results = graph.query(query)

        # Process results
        groups = []
        for row in results:
            group = {
                "groupName": str(row.groupName),
                "groupId": str(row.groupId) if row.groupId else None,
                "description": str(row.description) if row.description else None,
        
            }
            groups.append(group)

        # Return JSON Response
        return jsonify({"status": "success", "data": groups})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/techniques', methods=['GET'])
def get_techniques():
    try:
        # Log message for debugging
        print("Attempting to connect to GraphDB...")

        # Load the RDF Graph from GraphDB
        graph = Graph()

        # Replace with the correct repository and format
        # Ensure that the repository is accessible and the URL is correct
        try:
            print("Loading data from GraphDB...")
            graph.parse(GRAPHDB_ENDPOINT, format="xml")
            print("Successfully loaded data from GraphDB.")
        except Exception as e:
            print("Error loading data from GraphDB:", str(e))
            return jsonify({"status": "error", "message": "Failed to load data from GraphDB"}), 500
        
        # Define Namespace
        ex = Namespace("https://attack.mitre.org/")

        # SPARQL Query (RDFLib style)
        query = """
        PREFIX ex: <https://attack.mitre.org/> 
        SELECT ?techniqueId ?group ?use (GROUP_CONCAT(DISTINCT ?url; separator=", ") AS ?urls) ?body
        WHERE {
            ?technique a ex:techniques ;
                    ex:use ?use ;
                    ex:group_uses_techniques ?group .

            OPTIONAL {  
                ?technique ex:referenceUrl ?ref .
                ?ref ex:url ?url .
            }
            OPTIONAL {
                ?ref ex:body ?body .
            }
            BIND(str(?technique) AS ?techniqueId)
        }
        GROUP BY ?techniqueId ?group ?use  ?body
        """

        print("Executing SPARQL query...")

        # Run the Query
        try:
            results = graph.query(query)
            print("Query executed successfully.")
        except Exception as e:
            print("Error executing SPARQL query:", str(e))
            return jsonify({"status": "error", "message": "Failed to execute SPARQL query"}), 500

        # Process results
        techniques = []
        for row in results:
            technique = {
                "techniqueId": str(row.techniqueId),
                "body": str(row.body) if row.body else None,
                "use": str(row.use) if row.use else None,
                "urls": str(row.urls) if row.urls else None,
                "group": str(row.group) if row.group else None
            }
            techniques.append(technique)

        # Return JSON Response
        print("Returning results...")
        return jsonify({"status": "success", "data": techniques})

    except Exception as e:
        # Log the full exception traceback
        print("An error occurred:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500
# campaigns
@app.route('/campaigns', methods=['GET'])
def get_campaigns():
    # Define the SPARQL query for campaigns
    sparql_query = """
    PREFIX ex: <https://attack.mitre.org/>
    SELECT *
    WHERE {
        ?campaign a ex:campaigns ;
                   ex:campaignName ?campaignName;
                   ex:campaignId ?campaignId ;
                   ex:group_ispartof_campaigns ?group_ispartof_campaigns;
                   ex:campaignsFirstseen ?campaignsFirstseen ;
                   ex:campaignsLastseen ?campaignsLastseen .
    }
    """
    try:
        # Initialize the RDF graph and parse the RDF data
        graph = Graph()
        graph.parse(GRAPHDB_ENDPOINT, format="xml")
        
        # Execute SPARQL query
        results = graph.query(sparql_query)
        
        # Collect the results into a list of dictionaries
        campaigns = []
        for row in results:
            campaigns.append({
                "campaignName": row["campaignName"],
                "campaignId": row["campaignId"],
                "group_ispartof_campaigns": row["group_ispartof_campaigns"],
                "campaignsFirstseen": row["campaignsFirstseen"],
                "campaignsLastseen": row["campaignsLastseen"]
            })
        
        # Return the data as JSON
        return jsonify({"status": "success", "data": campaigns})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# mitigations
@app.route('/mitigations', methods=['GET'])
def get_mitigations():
    # Define the SPARQL query for mitigations
    sparql_query = """
    PREFIX ex: <https://attack.mitre.org/>
    SELECT *
    WHERE {
        ?mitigation a ex:mitigations ;
                    ex:mitigationName ?mitigationName ;
                    ex:description ?description .
        BIND(str(?mitigation) AS ?mitigationId)
    }
    """
    try:
        # Initialize the RDF graph and parse the RDF data
        graph = Graph()
        graph.parse(GRAPHDB_ENDPOINT, format="xml")
        
        # Execute SPARQL query
        results = graph.query(sparql_query)
        
        # Collect the results into a list of dictionaries
        mitigations = []
        for row in results:
            mitigations.append({
                "mitigationName": row["mitigationName"],
                "mitigationId": row["mitigationId"],
                "description": row["description"]
            })
        
        # Return the data as JSON
        return jsonify({"status": "success", "data": mitigations})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# software 
@app.route('/softwares', methods=['GET'])
def get_softwares():
    # Define the SPARQL query for softwares
    sparql_query = """
    PREFIX ex: <https://attack.mitre.org/>
    SELECT ?software ?softwareName ?softwareTechniques ?softwareId ?url
    WHERE {
        ?software a ex:softwares ;
                  ex:softwareName ?softwareName ;
                  ex:softwareTechniques ?softwareTechniques ;
                  OPTIONAL { ?software ex:url ?url . }
        BIND(str(?software) AS ?softwareId)
    }
    """ 
    try:
        # Initialize the RDF graph and parse the RDF data
        graph = Graph()
        graph.parse(GRAPHDB_ENDPOINT, format="xml")
        
        # Execute SPARQL query
        results = graph.query(sparql_query)
        
        # Collect the results into a list of dictionaries
        softwares = []
        for row in results:
            softwares.append({
                "softwareName": row["softwareName"],
                "softwareId": row["softwareId"],
                "softwareTechniques": row["softwareTechniques"],
                "url": row.get("url", None)
            })
        
        # Return the data as JSON
        return jsonify({"status": "success", "data": softwares})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# procedures
@app.route('/procedures', methods=['GET'])
def get_procedures():
    # Define the SPARQL query for procedures
    sparql_query = """
    PREFIX ex: <https://attack.mitre.org/>
    SELECT *
    WHERE {
        ?procedure a ex:procedures ;
                   ex:procedureName ?procedureName;
                   ex:description ?description .
    }
    """
    try:
        # Initialize the RDF graph and parse the RDF data
        graph = Graph()
        graph.parse(GRAPHDB_ENDPOINT, format="xml")
        
        # Execute SPARQL query
        results = graph.query(sparql_query)
        
        # Collect the results into a list of dictionaries
        procedures = []
        for row in results:
            procedures.append({
                "procedureName": row["procedureName"],
                "description": row["description"]
            })
        
        # Return the data as JSON
        return jsonify({"status": "success", "data": procedures})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# detections 
@app.route('/detections', methods=['GET'])
def get_detections():
    # Define the SPARQL query for detections
    sparql_query = """
    PREFIX ex: <https://attack.mitre.org/>
    SELECT *
    WHERE {
        ?detection a ex:detections ;
                   ex:dataSource ?dataSource ;
                   ex:detects ?detects ;
                   ex:dataComponent ?dataComponent ;
        BIND(str(?detection) AS ?detectionId)
    }
    """
    try:
        # Initialize the RDF graph and parse the RDF data
        graph = Graph()
        graph.parse(GRAPHDB_ENDPOINT, format="xml")
        
        # Execute SPARQL query
        results = graph.query(sparql_query)
        
        # Collect the results into a list of dictionaries
        detections = []
        for row in results:
            detections.append({
                "dataSource": row["dataSource"],
                "detects": row["detects"],
                "dataComponent": row["dataComponent"],
                "detectionId": row["detectionId"]
            })
        
        # Return the data as JSON
        return jsonify({"status": "success", "data": detections})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
  

# @app.route('/all-entries', methods=['GET'])
# def get_combined_entries():
#     """Retrieve and combine all entity types from separate queries with simplified IDs."""
#     try:
#         graph = Graph()  # Create an RDF graph
#         graph.parse(GRAPHDB_ENDPOINT, format="xml")  # Parse RDF data from GraphDB

#         # Query 1: Get all groups (groupId is already in GXXXX format)
#         groups_query = """
#         PREFIX ex: <https://attack.mitre.org/>
#         SELECT ?groupId ?groupName 
#         WHERE {
#             ?group a ex:groups ;
#                    ex:groupId ?groupId ;
#                    ex:groupName ?groupName .
#             OPTIONAL { ?group ex:alias ?alias }
#             OPTIONAL { ?group ex:associatedGroups ?associatedGroup }
#             OPTIONAL { ?group ex:description ?description }
#             OPTIONAL { ?group ex:date ?date }
#         }
#         GROUP BY ?group ?groupId ?groupName
#         LIMIT 10 
#         """

#         # Query 2: Get all techniques (extract TXXXX from URI)
#         techniques_query = """
#         PREFIX ex: <https://attack.mitre.org/> 
#         SELECT ?techniqueId ?groups
#         WHERE {
#             ?technique a ex:techniques ;   
#                       ex:group_uses_techniques ?groups .
#             BIND(STRAFTER(STR(?technique), "https://attack.mitre.org/techniques/") AS ?techniqueId)
#         }
#         GROUP BY ?techniqueId ?groups
#         LIMIT 12 
#         """

#         campaigns_query = """
#         PREFIX ex: <https://attack.mitre.org/>
#         SELECT ?campaignId ?campaignName ?group
#         WHERE {
#             ?campaign a ex:campaigns ;
#                       ex:campaignId ?campaignId ;
#                       ex:campaignName ?campaignName ;
#                       ex:group_ispartof_campaigns ?group .
#             OPTIONAL { ?campaign ex:campaignsFirstseen ?firstSeen }
#             OPTIONAL { ?campaign ex:campaignsLastseen ?lastSeen }
#         }
#         GROUP BY ?campaignId ?campaignName ?group
#         LIMIT 10
#         """

#         # Query 4: Get all mitigations (extract MXXXX from URI)
#         mitigations_query = """
#         PREFIX ex: <https://attack.mitre.org/>
#         SELECT ?mitigationId ?mitigationName ?technique
#         WHERE {
#             ?mitigation a ex:mitigations ;
#                         ex:mitigationName ?mitigationName .
#                         ex:technique_implements_mitigations ?technique
#             OPTIONAL { ?mitigation ex:description ?description }
#             BIND(STRAFTER(STR(?mitigation), "https://attack.mitre.org/mitigations/") AS ?mitigationId)
#         }
#         GROUP BY ?mitigationId ?mitigationName
#         LIMIT 10
#         """

#         # Query 5: Get all softwares (softwareId is already in SXXXX format)
#         softwares_query = """
#         PREFIX ex: <https://attack.mitre.org/>
#         SELECT ?softwareId ?softwareName ?group
#         WHERE {
#             ?software a ex:softwares ;
#                       ex:softwareId ?softwareId ;
#                       ex:softwareName ?softwareName ;
#                       ex:group_uses_software ?group .
#             OPTIONAL { ?software ex:softwareTechniques ?techniques }
#             OPTIONAL { ?software ex:url ?url }
#         }
#         GROUP BY ?softwareId ?softwareName ?group
#         LIMIT 10
#         """

#         # Query 6: Get all procedures (no ID to modify)
#         procedures_query = """
#         PREFIX ex: <https://attack.mitre.org/>
#         SELECT ?procedure ?procedureName ?technique
#         WHERE {
#             ?procedure a ex:procedures ;
#              ex:technique_implements_procedures ?technique ;
#                        ex:procedureName ?procedureName .
#             OPTIONAL { ?procedure ex:description ?description }
#         }
#         GROUP BY ?procedureName
#         LIMIT 10
#         """

#         # Query 7: Get all detections (extract DXXXX from URI, assuming similar structure)
#         detections_query = """
#         PREFIX ex: <https://attack.mitre.org/>
#         SELECT ?detectionId ?dataSource ?technique
#         WHERE {
#             ?detection a ex:detections ;
#             ex:technique_implements_detections ?technique ;
#                        ex:dataSource ?dataSource .
#             OPTIONAL { ?detection ex:detects ?detects }
#             OPTIONAL { ?detection ex:dataComponent ?dataComponent }
#             BIND(STRAFTER(STR(?detection), "https://attack.mitre.org/detections/") AS ?detectionId)
#         }
#         GROUP BY ?detectionId ?dataSource
#         LIMIT 10
#         """

#         # Execute all SPARQL queries
#         groups_results = graph.query(groups_query)
#         techniques_results = graph.query(techniques_query)
#         campaigns_results = graph.query(campaigns_query)
#         mitigations_results = graph.query(mitigations_query)
#         softwares_results = graph.query(softwares_query)
#         procedures_results = graph.query(procedures_query)
#         detections_results = graph.query(detections_query)

#         # Process groups into a list of dictionaries
#         groups = []
#         for row in groups_results:
#             groups.append({
#                 "id": str(row.groupId),  # Already in GXXXX format
#                 "name": str(row.groupName),
#             })

#         # Process techniques into a list of dictionaries
#         techniques = []
#         for row in techniques_results:
#             techniques.append({
#                 "id": str(row.techniqueId),  # Now TXXXX instead of full URI
#                 "groups": str(row.groups).split("|") if row.groups else [],  # Split groups if multiple
#             })

#         # Process campaigns into a list of dictionaries
#         campaigns = []
#         for row in campaigns_results:
#             campaigns.append({
#                 "id": str(row.campaignId),  # Already in CXXXX format
#                 "name": str(row.campaignName),
#                 "group": str(row.group),
#             })

#         # Process mitigations into a list of dictionaries
#         mitigations = []
#         for row in mitigations_results:
#             mitigations.append({
#                 "id": str(row.mitigationId),  # Now MXXXX instead of full URI
#                 "name": str(row.mitigationName),
#             })

#         # Process softwares into a list of dictionaries
#         softwares = []
#         for row in softwares_results:
#             softwares.append({
#                 "id": str(row.softwareId),  # Already in SXXXX format
#                 "name": str(row.softwareName),
#                 "group": str(row.group),
#             })

#         # Process procedures into a list of dictionaries
#         procedures = []
#         for row in procedures_results:
#             procedures.append({
#                 "name": str(row.procedureName),  # No ID field
#             })

#         # Process detections into a list of dictionaries
#         detections = []
#         for row in detections_results:
#             detections.append({
#                 "id": str(row.detectionId),  # Now DXXXX instead of full URI
#                 "dataSource": str(row.dataSource),
#             })

#         # Return combined results as JSON
#         return jsonify({
#             "status": "success",
#             "data": {
#                 "groups": groups,
#                 "techniques": techniques,
#                 "campaigns": campaigns,
#                 "mitigations": mitigations,
#                 "softwares": softwares,
#                 "procedures": procedures,
#                 "detections": detections
#             },
#             "counts": {
#                 "groups": len(groups),  # Count of groups returned
#                 "techniques": len(techniques),  # Count of techniques returned
#                 "campaigns": len(campaigns),  # Count of campaigns returned
#                 "mitigations": len(mitigations),  # Count of mitigations returned
#                 "softwares": len(softwares),  # Count of softwares returned
#                 "procedures": len(procedures),  # Count of procedures returned
#                 "detections": len(detections)  # Count of detections returned
#             }
#         })

#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)})  # Return error if something fails

@app.route('/all-entries', methods=['GET'])
def get_combined_entries():
    """Retrieve and combine all entity types from separate queries with simplified IDs."""
    try:
        graph = Graph()  # Create an RDF graph
        graph.parse(GRAPHDB_ENDPOINT, format="xml")  # Parse RDF data from GraphDB

        # Query 1: Get all groups
        groups_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?groupId ?groupName ?alias ?associatedGroup ?description ?date
        WHERE {
            ?group a ex:groups ;
                   ex:groupId ?groupId ;
                   ex:groupName ?groupName .
            OPTIONAL { ?group ex:alias ?alias }
            OPTIONAL { ?group ex:associatedGroups ?associatedGroup }
            OPTIONAL { ?group ex:description ?description }
            OPTIONAL { ?group ex:date ?date }
        }
        GROUP BY ?group ?groupId ?groupName ?alias ?associatedGroup ?description ?date
        limit 1
        """

        # Query 2: Get all techniques
        techniques_query = """
        PREFIX ex: <https://attack.mitre.org/> 
        SELECT ?techniqueId ?groups
        WHERE {
            ?technique a ex:techniques ;   
                      ex:group_uses_techniques ?groups .
            BIND(STRAFTER(STR(?technique), "https://attack.mitre.org/techniques/") AS ?techniqueId)
        }
        GROUP BY ?techniqueId ?groups
        limit 1
        """

        # Query 3: Get all campaigns
        campaigns_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?campaignId ?campaignName ?group ?firstSeen ?lastSeen
        WHERE {
            ?campaign a ex:campaigns ;
                      ex:campaignId ?campaignId ;
                      ex:campaignName ?campaignName ;
                      ex:group_ispartof_campaigns ?group .
            OPTIONAL { ?campaign ex:campaignsFirstseen ?firstSeen }
            OPTIONAL { ?campaign ex:campaignsLastseen ?lastSeen }
        }
        GROUP BY ?campaignId ?campaignName ?group ?firstSeen ?lastSeen
        limit 1
        """

        # Query 4: Get all mitigations
        mitigations_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?mitigationId ?mitigationName ?technique ?description
        WHERE {
            ?mitigation a ex:mitigations ;
                        ex:mitigationName ?mitigationName ;
                        ex:technique_implements_mitigations ?technique .
            OPTIONAL { ?mitigation ex:description ?description }
            BIND(STRAFTER(STR(?mitigation), "https://attack.mitre.org/mitigations/") AS ?mitigationId)
        }
        GROUP BY ?mitigationId ?mitigationName ?technique ?description
        limit 1
        """

        # Query 5: Get all softwares
        softwares_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?softwareId ?softwareName ?group ?techniques ?url
        WHERE {
            ?software a ex:softwares ;
                      ex:softwareId ?softwareId ;
                      ex:softwareName ?softwareName ;
                      ex:group_uses_software ?group .
            OPTIONAL { ?software ex:softwareTechniques ?techniques }
            OPTIONAL { ?software ex:url ?url }
        }
        GROUP BY ?softwareId ?softwareName ?group ?techniques ?url
        limit 1
        """

        # Query 6: Get all procedures
        procedures_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?procedure ?procedureName ?technique ?description
        WHERE {
            ?procedure a ex:procedures ;
                       ex:technique_implements_procedures ?technique ;
                       ex:procedureName ?procedureName .
            OPTIONAL { ?procedure ex:description ?description }
        }
        GROUP BY ?procedure ?procedureName ?technique ?description
        limit 1
        """

        # Query 7: Get all detections
        detections_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?detectionId ?dataSource ?technique ?detects ?dataComponent
        WHERE {
            ?detection a ex:detections ;
                        ex:technique_implements_detections ?technique ;
                        ex:dataSource ?dataSource .
            OPTIONAL { ?detection ex:detects ?detects }
            OPTIONAL { ?detection ex:dataComponent ?dataComponent }
            BIND(STRAFTER(STR(?detection), "https://attack.mitre.org/detections/") AS ?detectionId)
        }
        GROUP BY ?detectionId ?dataSource ?technique ?detects ?dataComponent
        limit 1
        """

        # Execute all SPARQL queries
        groups_results = graph.query(groups_query)
        techniques_results = graph.query(techniques_query)
        campaigns_results = graph.query(campaigns_query)
        mitigations_results = graph.query(mitigations_query)
        softwares_results = graph.query(softwares_query)
        procedures_results = graph.query(procedures_query)
        detections_results = graph.query(detections_query)

        # Process groups into a list of dictionaries
        groups = []
        for row in groups_results:
            groups.append({
                "id": str(row.groupId),
                "name": str(row.groupName),
                "alias": str(row.alias) if row.alias else None,
                "associatedGroup": str(row.associatedGroup) if row.associatedGroup else None,
                "description": str(row.description) if row.description else None,
                "date": str(row.date) if row.date else None,
            })

        # Process techniques into a list of dictionaries
        techniques = []
        for row in techniques_results:
            techniques.append({
                "id": str(row.techniqueId),
                "groups": str(row.groups).split("|") if row.groups else [],
            })

        # Process campaigns into a list of dictionaries
        campaigns = []
        for row in campaigns_results:
            campaigns.append({
                "id": str(row.campaignId),
                "name": str(row.campaignName),
                "group": str(row.group),
                "firstSeen": str(row.firstSeen) if row.firstSeen else None,
                "lastSeen": str(row.lastSeen) if row.lastSeen else None,
            })

        # Process mitigations into a list of dictionaries
        mitigations = []
        for row in mitigations_results:
            mitigations.append({
                "id": str(row.mitigationId),
                "name": str(row.mitigationName),
                "technique": str(row.technique) if row.technique else None,
                "description": str(row.description) if row.description else None,
            })

        # Process softwares into a list of dictionaries
        softwares = []
        for row in softwares_results:
            softwares.append({
                "id": str(row.softwareId),
                "name": str(row.softwareName),
                "group": str(row.group),
                "techniques": str(row.techniques).split("|") if row.techniques else [],
                "url": str(row.url) if row.url else None,
            })

        # Process procedures into a list of dictionaries
        procedures = []
        for row in procedures_results:
            procedures.append({
                "name": str(row.procedureName),
                "technique": str(row.technique) if row.technique else None,
                "description": str(row.description) if row.description else None,
            })

        # Process detections into a list of dictionaries
        detections = []
        for row in detections_results:
            detections.append({
                "id": str(row.detectionId),
                "dataSource": str(row.dataSource),
                "technique": str(row.technique) if row.technique else None,
                "detects": str(row.detects) if row.detects else None,
                "dataComponent": str(row.dataComponent) if row.dataComponent else None,
            })

        # Return combined results as JSON
        return jsonify({
            "status": "success",
            "data": {
                "groups": groups,
                "techniques": techniques,
                "campaigns": campaigns,
                "mitigations": mitigations,
                "softwares": softwares,
                "procedures": procedures,
                "detections": detections
            },
            "counts": {
                "groups": len(groups),
                "techniques": len(techniques),
                "campaigns": len(campaigns),
                "mitigations": len(mitigations),
                "softwares": len(softwares),
                "procedures": len(procedures),
                "detections": len(detections)
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
#         # Return error if something fails``

@app.route('/all-entries-v2', methods=['GET'])
def get_combined_entries_force():
    """Retrieve and combine all entity types with all attributes from GraphDB."""
    try:
        graph = Graph()
        graph.parse(GRAPHDB_ENDPOINT, format="xml")

        # 1. Query: Groups with all attributes
        groups_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?groupId ?groupName 
            (COALESCE(GROUP_CONCAT(DISTINCT ?aliasBound; SEPARATOR="|"), "") AS ?aliases)
            (COALESCE(GROUP_CONCAT(DISTINCT ?associatedGroupBound; SEPARATOR="|"), "") AS ?associatedGroups)
            ?description ?date
            (COALESCE(?belongsToCountry, "") AS ?belongsToCountry)
            (COALESCE(GROUP_CONCAT(DISTINCT ?attackedCountryBound; SEPARATOR="|"), "") AS ?attackedCountries)
            (COALESCE(?motivation, "") AS ?motivation)
        WHERE {
            ?group a ex:groups ;
                   ex:groupId ?groupId ;
                   ex:groupName ?groupName .
            OPTIONAL { ?group ex:alias ?alias }.
            BIND(IF(BOUND(?alias), ?alias, "") AS ?aliasBound).
            OPTIONAL { ?group ex:associatedGroups ?associatedGroup }.
            BIND(IF(BOUND(?associatedGroup), ?associatedGroup, "") AS ?associatedGroupBound).
            OPTIONAL { ?group ex:description ?description }.
            OPTIONAL { ?group ex:date ?date }.
            OPTIONAL { ?group ex:group_belongs_to_country ?belongsToCountry }.
            OPTIONAL { ?group ex:group_attacked_country ?attackedCountry }.
            BIND(IF(BOUND(?attackedCountry), ?attackedCountry, "") AS ?attackedCountryBound).
            OPTIONAL { ?group ex:motivation ?motivation }.
        }
        GROUP BY ?groupId ?groupName ?description ?date ?belongsToCountry ?motivation
        LIMIT 5
        """

        # 2. Query: Techniques with all attributes
        techniques_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?techniqueId 
               (COALESCE(GROUP_CONCAT(DISTINCT ?groupsBound; SEPARATOR="|"), "") AS ?groups)
               ?use ?domain ?subId
               (COALESCE(GROUP_CONCAT(DISTINCT ?orgBound; SEPARATOR="|"), "") AS ?orgs)
               (COALESCE(GROUP_CONCAT(DISTINCT ?malwareBound; SEPARATOR="|"), "") AS ?malware)
               (COALESCE(GROUP_CONCAT(DISTINCT ?toolsBound; SEPARATOR="|"), "") AS ?tools)
               (COALESCE(GROUP_CONCAT(DISTINCT ?tacticsBound; SEPARATOR="|"), "") AS ?tactics)
        WHERE {
            ?technique a ex:techniques ;
                       ex:techniqueId ?techniqueId .
            OPTIONAL { ?technique ex:group_uses_techniques ?groups }.
            BIND(IF(BOUND(?groups), ?groups, "") AS ?groupsBound).
            OPTIONAL { ?technique ex:use ?use }.
            OPTIONAL { ?technique ex:domain ?domain }.
            OPTIONAL { ?technique ex:subId ?subId }.
            OPTIONAL { ?technique ex:org ?org }.
            BIND(IF(BOUND(?org), ?org, "") AS ?orgBound).
            OPTIONAL { ?technique ex:malware ?malware }.
            BIND(IF(BOUND(?malware), ?malware, "") AS ?malwareBound).
            OPTIONAL { ?technique ex:tools ?tools }.
            BIND(IF(BOUND(?tools), ?tools, "") AS ?toolsBound).
            OPTIONAL { ?technique ex:tactics ?tactics }.
            BIND(IF(BOUND(?tactics), ?tactics, "") AS ?tacticsBound).
            BIND(STRAFTER(STR(?technique), "https://attack.mitre.org/techniques/") AS ?techniqueId)
        }
        GROUP BY ?techniqueId ?use ?domain ?subId
        LIMIT 5
        """

        # 3. Query: Campaigns
        campaigns_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?campaignId ?campaignName 
               (COALESCE(GROUP_CONCAT(DISTINCT ?groupBound; SEPARATOR="|"), "") AS ?group)
               ?firstSeen ?lastSeen 
               (COALESCE(GROUP_CONCAT(DISTINCT ?techniquesBound; SEPARATOR="|"), "") AS ?techniques)
        WHERE {
            ?campaign a ex:campaigns ;
                      ex:campaignId ?campaignId ;
                      ex:campaignName ?campaignName .
            OPTIONAL { ?campaign ex:group_ispartof_campaigns ?group }.
            BIND(IF(BOUND(?group), ?group, "") AS ?groupBound).
            OPTIONAL { ?campaign ex:campaignsFirstseen ?firstSeen }.
            OPTIONAL { ?campaign ex:campaignsLastseen ?lastSeen }.
            OPTIONAL { ?campaign ex:campaignsTechniques ?techniques }.
            BIND(IF(BOUND(?techniques), ?techniques, "") AS ?techniquesBound).
        }
        GROUP BY ?campaignId ?campaignName ?firstSeen ?lastSeen
        LIMIT 5
        """

        # 4. Query: Mitigations
        mitigations_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?mitigationId ?mitigationName 
               (COALESCE(GROUP_CONCAT(DISTINCT ?techniqueBound; SEPARATOR="|"), "") AS ?techniques)
               ?description
               (COALESCE(GROUP_CONCAT(DISTINCT ?alertingOrReportingBound; SEPARATOR="|"), "") AS ?alerts)
               (COALESCE(GROUP_CONCAT(DISTINCT ?registryKeysBound; SEPARATOR="|"), "") AS ?registryKeys)
               (COALESCE(GROUP_CONCAT(DISTINCT ?pathsBound; SEPARATOR="|"), "") AS ?paths)
        WHERE {
            ?mitigation a ex:mitigations ;
                        ex:mitigationId ?mitigationId ;
                        ex:mitigationName ?mitigationName .
            OPTIONAL { ?mitigation ex:technique_implements_mitigations ?technique }.
            BIND(IF(BOUND(?technique), ?technique, "") AS ?techniqueBound).
            OPTIONAL { ?mitigation ex:description ?description }.
            OPTIONAL { ?mitigation ex:alertingOrReporting ?alertingOrReporting }.
            BIND(IF(BOUND(?alertingOrReporting), ?alertingOrReporting, "") AS ?alertingOrReportingBound).
            OPTIONAL { ?mitigation ex:registryKeys ?registryKeys }.
            BIND(IF(BOUND(?registryKeys), ?registryKeys, "") AS ?registryKeysBound).
            OPTIONAL { ?mitigation ex:paths ?paths }.
            BIND(IF(BOUND(?paths), ?paths, "") AS ?pathsBound).
            BIND(STRAFTER(STR(?mitigation), "https://attack.mitre.org/mitigations/") AS ?mitigationId)
        }
        GROUP BY ?mitigationId ?mitigationName ?description
        LIMIT 5
        """

        # 5. Query: Software
        softwares_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?softwareId ?softwareName 
               (COALESCE(GROUP_CONCAT(DISTINCT ?groupBound; SEPARATOR="|"), "") AS ?groups)
               (COALESCE(GROUP_CONCAT(DISTINCT ?techniquesBound; SEPARATOR="|"), "") AS ?techniques)
               ?url
        WHERE {
            ?software a ex:softwares ;
                      ex:softwareId ?softwareId ;
                      ex:softwareName ?softwareName .
            OPTIONAL { ?software ex:group_uses_software ?group }.
            BIND(IF(BOUND(?group), ?group, "") AS ?groupBound).
            OPTIONAL { ?software ex:softwareTechniques ?techniques }.
            BIND(IF(BOUND(?techniques), ?techniques, "") AS ?techniquesBound).
            OPTIONAL { ?software ex:url ?url }.
        }
        GROUP BY ?softwareId ?softwareName ?url
        LIMIT 5
        """

        # 6. Query: Procedures
        procedures_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?procedureId ?procedureName 
               (COALESCE(GROUP_CONCAT(DISTINCT ?techniqueBound; SEPARATOR="|"), "") AS ?techniques)
               ?description
               (COALESCE(GROUP_CONCAT(DISTINCT ?orgBound; SEPARATOR="|"), "") AS ?orgs)
               (COALESCE(GROUP_CONCAT(DISTINCT ?malwareBound; SEPARATOR="|"), "") AS ?malware)
               (COALESCE(GROUP_CONCAT(DISTINCT ?toolsBound; SEPARATOR="|"), "") AS ?tools)
        WHERE {
            ?procedure a ex:procedures ;
                       ex:procedureId ?procedureId ;
                       ex:procedureName ?procedureName .
            OPTIONAL { ?procedure ex:technique_implements_procedures ?technique }.
            BIND(IF(BOUND(?technique), ?technique, "") AS ?techniqueBound).
            OPTIONAL { ?procedure ex:description ?description }.
            OPTIONAL { ?procedure ex:org ?org }.
            BIND(IF(BOUND(?org), ?org, "") AS ?orgBound).
            OPTIONAL { ?procedure ex:malware ?malware }.
            BIND(IF(BOUND(?malware), ?malware, "") AS ?malwareBound).
            OPTIONAL { ?procedure ex:tools ?tools }.
            BIND(IF(BOUND(?tools), ?tools, "") AS ?toolsBound).
        }
        GROUP BY ?procedureId ?procedureName ?description
        LIMIT 5
        """

        # 7. Query: Detections
        detections_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?detectionId ?dataSource 
               (COALESCE(GROUP_CONCAT(DISTINCT ?techniqueBound; SEPARATOR="|"), "") AS ?techniques)
               (COALESCE(GROUP_CONCAT(DISTINCT ?detectsBound; SEPARATOR="|"), "") AS ?detects)
               ?dataComponent
               (COALESCE(GROUP_CONCAT(DISTINCT ?orgBound; SEPARATOR="|"), "") AS ?orgs)
               (COALESCE(GROUP_CONCAT(DISTINCT ?malwareBound; SEPARATOR="|"), "") AS ?malware)
               (COALESCE(GROUP_CONCAT(DISTINCT ?toolsBound; SEPARATOR="|"), "") AS ?tools)
        WHERE {
            ?detection a ex:detections ;
                       ex:detectionId ?detectionId ;
                       ex:dataSource ?dataSource .
            OPTIONAL { ?detection ex:technique_implements_detections ?technique }.
            BIND(IF(BOUND(?technique), ?technique, "") AS ?techniqueBound).
            OPTIONAL { ?detection ex:detects ?detects }.
            BIND(IF(BOUND(?detects), ?detects, "") AS ?detectsBound).
            OPTIONAL { ?detection ex:dataComponent ?dataComponent }.
            OPTIONAL { ?detection ex:org ?org }.
            BIND(IF(BOUND(?org), ?org, "") AS ?orgBound).
            OPTIONAL { ?detection ex:malware ?malware }.
            BIND(IF(BOUND(?malware), ?malware, "") AS ?malwareBound).
            OPTIONAL { ?detection ex:tools ?tools }.
            BIND(IF(BOUND(?tools), ?tools, "") AS ?toolsBound).
            BIND(STRAFTER(STR(?detection), "https://attack.mitre.org/detections/") AS ?detectionId)
        }
        GROUP BY ?detectionId ?dataSource ?dataComponent
        LIMIT 5
        """

        # Execute all queries
        results = {
            "groups": graph.query(groups_query),
            "techniques": graph.query(techniques_query),
            "campaigns": graph.query(campaigns_query),
            "mitigations": graph.query(mitigations_query),
            "softwares": graph.query(softwares_query),
            "procedures": graph.query(procedures_query),
            "detections": graph.query(detections_query)
        }

        # Function to process query results into JSON-friendly dictionaries
        def process_entity(query_results, fields_config):
            processed = []
            for row in query_results:
                entity = {}
                for field, config in fields_config.items():
                    value = getattr(row, field, None)
                    if value is None:
                        entity[field] = [] if config.get("is_list", False) else None
                    else:
                        if config.get("is_list", False):
                            entity[field] = str(value).split("|") if str(value) != "" else []
                        else:
                            entity[field] = str(value)
                processed.append(entity)
            return processed

        # Field configuration for each entity type
        field_configs = {
            "groups": {
                "groupId": {"is_list": False},
                "groupName": {"is_list": False},
                "aliases": {"is_list": True},
                "associatedGroups": {"is_list": True},
                "description": {"is_list": False},
                "date": {"is_list": False},
                "belongsToCountry": {"is_list": False},
                "attackedCountries": {"is_list": True},
                "motivation": {"is_list": False}
            },
            "techniques": {
                "techniqueId": {"is_list": False},
                "groups": {"is_list": True},
                "use": {"is_list": False},
                "domain": {"is_list": False},
                "subId": {"is_list": False},
                "orgs": {"is_list": True},
                "malware": {"is_list": True},
                "tools": {"is_list": True},
                "tactics": {"is_list": True}
            },
            "campaigns": {
                "campaignId": {"is_list": False},
                "campaignName": {"is_list": False},
                "group": {"is_list": True},
                "firstSeen": {"is_list": False},
                "lastSeen": {"is_list": False},
                "techniques": {"is_list": True}
            },
            "mitigations": {
                "mitigationId": {"is_list": False},
                "mitigationName": {"is_list": False},
                "techniques": {"is_list": True},
                "description": {"is_list": False},
                "alerts": {"is_list": True},
                "registryKeys": {"is_list": True},
                "paths": {"is_list": True}
            },
            "softwares": {
                "softwareId": {"is_list": False},
                "softwareName": {"is_list": False},
                "groups": {"is_list": True},
                "techniques": {"is_list": True},
                "url": {"is_list": False}
            },
            "procedures": {
                "procedureId": {"is_list": False},
                "procedureName": {"is_list": False},
                "techniques": {"is_list": True},
                "description": {"is_list": False},
                "orgs": {"is_list": True},
                "malware": {"is_list": True},
                "tools": {"is_list": True}
            },
            "detections": {
                "detectionId": {"is_list": False},
                "dataSource": {"is_list": False},
                "techniques": {"is_list": True},
                "detects": {"is_list": True},
                "dataComponent": {"is_list": False},
                "orgs": {"is_list": True},
                "malware": {"is_list": True},
                "tools": {"is_list": True}
            }
        }

        # Process each query's results
        response_data = {
            "groups": process_entity(results["groups"], field_configs["groups"]),
            "techniques": process_entity(results["techniques"], field_configs["techniques"]),
            "campaigns": process_entity(results["campaigns"], field_configs["campaigns"]),
            "mitigations": process_entity(results["mitigations"], field_configs["mitigations"]),
            "softwares": process_entity(results["softwares"], field_configs["softwares"]),
            "procedures": process_entity(results["procedures"], field_configs["procedures"]),
            "detections": process_entity(results["detections"], field_configs["detections"])
        }

        return jsonify({
            "status": "success",
            "data": response_data,
            "counts": {k: len(v) for k, v in response_data.items()}
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve data: {str(e)}"
        }), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Start the server on port 5001 with debug mode enabled