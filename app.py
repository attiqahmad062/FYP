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
 
# @app.route('/groups', methods=['GET'])
# def get_groups():
#     # Define the SPARQL query
#     sparql_query = """
#     PREFIX ex: <https://attack.mitre.org>
#     SELECT ?groupName
#     WHERE {
#         ?groupName a ex:groups ;
#                    ex:groupId ?groupId .
#         OPTIONAL { ?groupName ex:use ?description . }
#         OPTIONAL { ?groupName ex:associatedGroups ?associatedGroups . }
#     }
#     """
#     try:
#         # Initialize SPARQLWrapper
#         sparql = SPARQLWrapper(
#              "http://localhost:7200/repositories/etiapt/statements"
#              "https://attack.mitre.org/"
#         )
#         sparql.setQuery(sparql_query)
#         sparql.setReturnFormat(JSON)
#         sparql.addCustomHttpHeader("Accept", "application/sparql-results+json")
#         # sparql.setDebug(True)
#         sparql.setMethod('GET')
#         res=sparql.query()
#         # sparql.setCredentials("root"
#         # , "1234")
        

        
#         # Execute query
#         results = res.convert()

#         # Parse results
#         # groups = []
#         # for result in results["results"]["bindings"]:
#         #     group = {
#         #         "groupName": result["groupName"]["value"],
#         #         "groupId": result["groupId"]["value"],
#         #         "description": result["description"]["value"],
#         #         "associatedGroups": result["associatedGroups"]["value"]
#         #     }
#         #     groups.append(group)

#         # Return the data as JSON
#         return jsonify({"status": "success", "data": "data"})
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

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
# def get_all_entries():
#     """Retrieve all entries (groups, techniques, campaigns, mitigations, software, procedures, detections) in one request"""
#     try:
#         # Initialize the RDF graph and parse the RDF data
#         graph = Graph()
#         graph.parse(GRAPHDB_ENDPOINT, format="xml")

#         # Unified SPARQL Query
#         sparql_query = """
#         PREFIX ex: <https://attack.mitre.org/>
#         SELECT ?type ?entity ?name ?id ?description ?group ?use  ?firstSeen ?lastSeen ?techniques ?dataSource ?detects ?dataComponent
#         WHERE {
#             {
#                 ?entity a ex:groups ;
#                         ex:groupName ?name ;
#                         ex:groupId ?id .
#                 OPTIONAL { ?entity ex:description ?description . }
#                 BIND("Group" AS ?type)
#             }
#             UNION
#             {
#                 ?entity a ex:techniques ;
#                         ex:techniqueName ?name ;
#                         ex:techniqueId ?id ;
#                         ex:use ?use ;
#                         ex:group_uses_techniques ?group .
#                 OPTIONAL {
#                     ?entity ex:referenceUrl ?ref .
#                     ?ref ex:url ?urls .
#                 }
            
#                 BIND("Technique" AS ?type)
#             }
#             UNION
#             {
#                 ?entity a ex:campaigns ;
#                         ex:campaignName ?name ;
#                         ex:campaignId ?id ;
#                         ex:group_ispartof_campaigns ?group ;
#                         ex:campaignsFirstseen ?firstSeen ;
#                         ex:campaignsLastseen ?lastSeen .
#                 BIND("Campaign" AS ?type)
#             }
#             UNION
#             {
#                 ?entity a ex:mitigations ;
#                         ex:mitigationName ?name ;
#                         ex:description ?description .
#                 BIND("Mitigation" AS ?type)
#                 BIND(str(?entity) AS ?id)
#             }
#             UNION
#             {
#                 ?entity a ex:softwares ;
#                         ex:softwareName ?name ;
#                         ex:softwareId ?id ;
#                         ex:softwareTechniques ?techniques .
#                 OPTIONAL { ?entity ex:url ?urls . }
#                 BIND("Software" AS ?type)
#             }
#             UNION
#             {
#                 ?entity a ex:procedures ;
#                         ex:procedureName ?name ;
#                         ex:description ?description .
#                 BIND("Procedure" AS ?type)
#                 BIND(str(?entity) AS ?id)
#             }
#             UNION
#             {
#                 ?entity a ex:detections ;
#                         ex:dataSource ?dataSource ;
#                         ex:detects ?detects ;
#                         ex:dataComponent ?dataComponent .
#                 BIND("Detection" AS ?type)
#                 BIND(str(?entity) AS ?id)
#             }
#         }
        
#         """

#         # Execute SPARQL query
#         results = graph.query(sparql_query)

#         # Organize results by type
#         entries = {
#             "Groups": [],
#             "Techniques": [],
#             "Campaigns": [],
#             "Mitigations": [],
#             "Softwares": [],
#             "Procedures": [],
#             "Detections": []
#         }

#         for row in results:
#             entry = {
#                 "name": str(row.name),
#                 "id": str(row.id),
#                 "description": str(row.description) if row.description else None,
#                 "group": str(row.group) if row.group else None,
#                 "use": str(row.use) if row.use else None,
#                 "urls": str(row.urls) if row.urls else None,
#                 "body": str(row.body) if row.body else None,
#                 "firstSeen": str(row.firstSeen) if row.firstSeen else None,
#                 "lastSeen": str(row.lastSeen) if row.lastSeen else None,
#                 "techniques": str(row.techniques) if row.techniques else None,
#                 "dataSource": str(row.dataSource) if row.dataSource else None,
#                 "detects": str(row.detects) if row.detects else None,
#                 "dataComponent": str(row.dataComponent) if row.dataComponent else None
#             }

#             if str(row.type) == "Group":
#                 entries["Groups"].append(entry)
#             elif str(row.type) == "Technique":
#                 entries["Techniques"].append(entry)
#             elif str(row.type) == "Campaign":
#                 entries["Campaigns"].append(entry)
#             elif str(row.type) == "Mitigation":
#                 entries["Mitigations"].append(entry)
#             elif str(row.type) == "Software":
#                 entries["Softwares"].append(entry)
#             elif str(row.type) == "Procedure":
#                 entries["Procedures"].append(entry)
#             elif str(row.type) == "Detection":
#                 entries["Detections"].append(entry)

#         # Return JSON Response
#         return jsonify({"status": "success", "data": entries})

#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500
@app.route('/all-entries', methods=['GET'])
def get_combined_entries():
    """Retrieve and combine groups and techniques from separate queries"""
    try:
        graph = Graph()
        graph.parse(GRAPHDB_ENDPOINT, format="xml")
        # Query 1: Get all groups
        groups_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT ?groupId ?groupName 
        WHERE {
            ?group a ex:groups ;
                   ex:groupId ?groupId ;
                   ex:groupName ?groupName .
            
            OPTIONAL { ?group ex:alias ?alias }
            OPTIONAL { ?group ex:associatedGroups ?associatedGroup }
            OPTIONAL { ?group ex:description ?description }
            OPTIONAL { ?group ex:date ?date }
        }
        GROUP BY ?group ?groupId ?groupName
        limit 10 
        """

        # Query 2: Get all techniques
        techniques_query = """
        PREFIX ex: <https://attack.mitre.org/> 
        SELECT ?techniqueId ?groups
        WHERE {
            ?technique a ex:techniques ;   
                    ex:group_uses_techniques ?groups;
           
            BIND(str(?technique) AS ?techniqueId)
        }
        GROUP BY ?techniqueId   ?groups
        limit 12 
        """
        # Query 3: Get all detections
        detections_query = """
        PREFIX ex: <https://attack.mitre.org/> 
        SELECT    *
        WHERE {
            ?detection a ex:detections ;
            ex:dataSource ?dataSource ;
        #     ex:detects ?detects ;
            ex:dataComponent ?dataComponent ;
            
            BIND(str(?detection) AS ?detectionId)
        }
        """
        # Query 4: Get all procedures 
        procedures_query = """
        PREFIX ex: <https://attack.mitre.org/> 
        SELECT    *
        WHERE {
            ?procedure a ex:procedures ;

                        ex:procedureName  ?procedureName;
                        ex:description ?description .
        }
        """
        # Query 4: Get all softwares 
        softwares_query = """
        PREFIX ex: <https://attack.mitre.org/>
        SELECT  ?software ?softwareName ?softwareTechniques ?softwareId ?group
        WHERE {
            ?software a ex:softwares ;
            ex:softwareId ?softwareId ;
                        ex:softwareName ?softwareName ;
                            ex:softwareTechniques ?softwareTechniques ;
            ex:group_uses_software ?group
            OPTIONAL { ?software ex:url ?url .
            }
        #    BIND(str(?software) AS ?softwareId)
        } 

        """
        # Execute both queries
        groups_results = graph.query(groups_query)
        techniques_results = graph.query(techniques_query)

        # Process groups
        groups = []
        for row in groups_results:
            groups.append({
                "id": str(row.groupId),
                "name": str(row.groupName),
                # "description": str(row.description) if row.description else None,
                # "aliases": row.aliases.split("|") if row.aliases else [],
                # "associated_groups": row.associatedGroups.split("|") if row.associatedGroups else [],
                # "dates": row.dates.split("|") if row.dates else []
            })

        # Process techniques
        techniques = []
        for row in techniques_results:
            techniques.append({
                "id": str(row.techniqueId),
                # "name": str(row.techniqueName),
                # "uses": row.uses.split("|") if row.uses else [],
                "groups": row.groups.split("|") if row.groups else [],
            })

        return jsonify({
            "status": "success",
            "data": {
                "groups": groups,
                "techniques": techniques
            },
            "counts": {
                "groups": len(groups),
                "techniques": len(techniques)
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
if __name__ == '__main__':
    app.run(debug=True,port=5001)



