from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD
import uuid

STIX = Namespace("http://docs.oasis-open.org/cti/ns/stix#")
STIX_TP = Namespace("http://docs.oasis-open.org/cti/ns/stix-taxii#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")

class STIXRDFConverter:
    def __init__(self):
        self.g = Graph()
        self.g.bind("stix", STIX)
        self.g.bind("stix-tp", STIX_TP)
    
    def convert_entity(self, entity):
        """Convert any STIX entity to RDF"""
        entity_id = entity.get("id", str(uuid.uuid4()))
        entity_uri = URIRef(f"{STIX}{entity_id}")
        
        # Add type
        entity_type = entity["type"].replace("-", "_")
        self.g.add((entity_uri, RDF.type, getattr(STIX, entity_type)))
        
        # Add properties
        for prop, value in entity.items():
            if prop == "type" or prop == "id":
                continue
            if isinstance(value, dict):
                self._handle_nested(entity_uri, prop, value)
            elif isinstance(value, list):
                for item in value:
                    self._handle_property(entity_uri, prop, item)
            else:
                self._handle_property(entity_uri, prop, value)
        
        return self.g
    
    def _handle_property(self, subject, predicate, obj):
        predicate_uri = getattr(STIX, predicate.replace("-", "_"))
        if isinstance(obj, str):
            self.g.add((subject, predicate_uri, Literal(obj, datatype=XSD.string)))
        elif isinstance(obj, bool):
            self.g.add((subject, predicate_uri, Literal(obj, datatype=XSD.boolean)))
        elif isinstance(obj, int):
            self.g.add((subject, predicate_uri, Literal(obj, datatype=XSD.integer)))
    
    def _handle_nested(self, subject, predicate, nested_obj):
        nested_uri = URIRef(f"{STIX}{nested_obj['id']}")
        self.g.add((subject, getattr(STIX, predicate), nested_uri))
        self.convert_entity(nested_obj)