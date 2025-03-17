from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from threading import Thread
import math
from .config.entities import STIX_ENTITIES
from .services.opencti_service import OpenCTIService
from .services.graphdb_service import GraphDBService
from .utils.rdf_converter import STIXRDFConverter
from flask import Flask, request, jsonify
from pycti import OpenCTIConnectorHelper
import logging
import os
logger = logging.getLogger(__name__)
opencti_bp = Blueprint('opencti', __name__)
# cti_service = OpenCTIService()
# graphdb = GraphDBService()
STIX="https://attack.mitre.org/ontologies/stix/2.1"
# @opencti_bp.route('/sync', methods=['POST'])
# @jwt_required()
# def full_sync():
#     try:
#         Thread(target=background_sync).start()
#         return jsonify({"message": "Sync started"}), 202
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@opencti_bp.route('/sync', methods=['POST'])
def sync_opencti():
    try:
        data = cti_service.get_all_stix_data()
        # print("data is ",data)
        converter = STIXRDFConverter()
       
        # Batch processing
        BATCH_SIZE = 1000
        for entity_type, entities in data.items():
            for i in range(0, len(entities), BATCH_SIZE):
                
                batch = entities[i:i+BATCH_SIZE]
                rdf_data = []
                for entity in batch:
                    if "type" not in entity:
                        logger.error(f"Entity missing type field: {entity}")
                        continue  # Skip problematic entity
                    converter.convert_entity(entity)
                    rdf_data.append(converter.g.serialize(format="turtle"))
                
                # Insert batch
                print("inserting",rdf_data)
                result = graphdb.bulk_insert("\n".join(rdf_data))
                if not result["success"]:
                    return jsonify({"error": result["message"]}), 500

        return jsonify({
            "status": "success",
            "entities_processed": {k: len(v) for k, v in data.items()}
        }), 200
        
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
def background_sync():
    converter = STIXRDFConverter()
    data = cti_service.get_all_stix_data()
    # Process entities
    for entity_type, entities in data.items():
        if entity_type == "Relationship":
            continue
        for entity in entities:
            converter.convert_entity(entity)
    # Process relationships
    for rel in data.get("Relationship", []):
        converter.convert_entity(rel)
    
    # Insert into GraphDB
    graphdb.bulk_insert(converter.g.serialize(format="turtle"))

@opencti_bp.route('/entities', methods=['GET'])
def list_entity_types():
    return jsonify({"entity_types": STIX_ENTITIES}), 200

@opencti_bp.route('/entities/<entity_type>', methods=['GET'])
def get_entities(entity_type):
    if entity_type not in STIX_ENTITIES:
        return jsonify({"error": "Invalid entity type"}), 400
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    offset = (page - 1) * per_page
    
    try:
        # Count query
        count_query = f"""
            PREFIX stix: <{STIX}>
            SELECT (COUNT(DISTINCT ?entity) AS ?total)
            WHERE {{ ?entity a stix:{entity_type.replace('-', '_')} }}
        """
        total = int(graphdb.execute_query(count_query)[0]['total'])
        
        # Data query
        data_query = f"""
            PREFIX stix: <{STIX}>
            SELECT ?entity ?property ?value
            WHERE {{
                ?entity a stix:{entity_type.replace('-', '_')} ;
                        ?property ?value .
            }}
            LIMIT {per_page}
            OFFSET {offset}
        """
        results = graphdb.execute_query(data_query)
        
        # Process results
        entities = {}
        for row in results:
            entity_id = row['entity'].split('/')[-1]
            prop = row['property'].split('#')[-1]
            
            if entity_id not in entities:
                entities[entity_id] = {"id": entity_id, "type": entity_type, "properties": {}}
            
            if prop in entities[entity_id]['properties']:
                if not isinstance(entities[entity_id]['properties'][prop], list):
                    entities[entity_id]['properties'][prop] = [entities[entity_id]['properties'][prop]]
                entities[entity_id]['properties'][prop].append(row['value'])
            else:
                entities[entity_id]['properties'][prop] = row['value']
        
        return jsonify({
            "data": list(entities.values()),
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": math.ceil(total / per_page)
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# # ope cti for import
# helper = OpenCTIConnectorHelper(config)

# # Extended entity mapping including all STIX2 objects
# ENTITY_METHOD_MAP = {
#     # Threat Intelligence
#     "Threat-Actor": "threat_actor",
#     "Intrusion-Set": "intrusion_set",
#     "Campaign": "campaign",
#     "Malware": "malware",
#     "Tool": "tool",
#     "Attack-Pattern": "attack_pattern",
#     "Course-Of-Action": "course_of_action",
#     "Indicator": "indicator",
#     "Observed-Data": "observed_data",
#     "Report": "report",
#     "Note": "note",
#     "Opinion": "opinion",
    
#     # Vulnerability Management
#     "Vulnerability": "vulnerability",
    
#     # Identity
#     "Identity": "identity",
#     "Sector": "sector",
#     "Organization": "organization",
#     "Individual": "individual",
    
#     # Location
#     "Location": "location",
#     "Country": "country",
#     "Region": "region",
#     "City": "city",
    
#     # Infrastructure
#     "Infrastructure": "infrastructure",
#     "Hostname": "hostname",
#     "Domain-Name": "domain_name",
#     "IPv4-Addr": "ipv4_addr",
#     "IPv6-Addr": "ipv6_addr",
#     "URL": "url",
#     "Email-Addr": "email_addr",
#     "Mac-Addr": "mac_addr",
    
#     # Cyber-Physical
#     "Device": "device",
    
#     # STIX Cyber Observables
#     "Artifact": "artifact",
#     "Autonomous-System": "autonomous_system",
#     "Directory": "directory",
#     "Domain-Name": "domain_name",
#     "Email-Message": "email_message",
#     "File": "file",
#     "Network-Traffic": "network_traffic",
#     "Process": "process",
#     "Software": "software",
#     "User-Account": "user_account",
#     "Windows-Registry-Key": "windows_registry_key",
#     "X509-Certificate": "x509_certificate",
    
#     # Analysis
#     "Case": "case",
#     "Feedback": "feedback",
#     "Malware-Analysis": "malware_analysis",
    
#     # STIX Meta
#     "Language-Content": "language_content",
#     "Marking-Definition": "marking_definition",
#     "Grouping": "grouping",
#     "Data-Component": "data_component",
#     "Data-Source": "data_source"
# }

# def create_stix2_object(entity_type, data):
#     """Create STIX2 object based on entity type"""
#     method_name = ENTITY_METHOD_MAP.get(entity_type)
#     if not method_name:
#         return None
        
#     method = getattr(helper.api.stix2, f"create_{method_name}", None)
#     if not method:
#         return None
        
#     return method(**data)

# @app.route('/import', methods=['POST'])
# def import_data():
#     try:
#         # Get data from request
#         data = request.get_json()
        
#         if not data or 'objects' not in data:
#             return jsonify({"error": "Invalid STIX2 bundle format"}), 400
#         results = []
#         for obj in data['objects']:
#             entity_type = obj.get('type')
#             if not entity_type:
#                 continue
                
#             # Create the STIX object
#             stix_object = create_stix2_object(entity_type, obj)
            
#             if stix_object:
#                 results.append({
#                     "id": stix_object['id'],
#                     "type": entity_type,
#                     "status": "success"
#                 })
#             else:
#                 results.append({
#                     "type": entity_type,
#                     "status": "failed",
#                     "error": "Unsupported entity type"
#                 })

#         # Send bundle to OpenCTI
#         bundle = helper.api.stix2.export_entity("Bundle", results)
#         helper.send_stix2_bundle(bundle)

#         return jsonify({"results": results}), 200

#     except Exception as e:
#         helper.log_error(f"Error during import: {str(e)}")
#         return jsonify({"error": str(e)}), 500