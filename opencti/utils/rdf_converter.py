from rdflib import Graph, Namespace, URIRef, Literal, RDF
from ..config.entities import STIX_ENTITIES

STIX = Namespace("http://docs.oasis-open.org/cti/ns/stix#")
STIX_REL = Namespace("http://docs.oasis-open.org/cti/ns/stix-relationship#")
def sanitize_text(text):
    """Clean text for RDF serialization"""
    if isinstance(text, str):
        return text.encode('utf-8', 'ignore').decode('utf-8')
    return str(text)

class STIXRDFConverter:
    def __init__(self):
        self.g = Graph()
        self.g.bind("stix", STIX)
        self.g.bind("stix-rel", STIX_REL)

    def convert_entity(self, entity):
        """Convert STIX entity to RDF triples"""
        # Clean all string values
        for key in entity:
            if isinstance(entity[key], str):
                entity[key] = sanitize_text(entity[key])
            elif isinstance(entity[key], list):
                entity[key] = [sanitize_text(i) if isinstance(i, str) else i for i in entity[key]]
        entity_type = entity['type'].replace("-", "_")
        entity_uri = URIRef(f"{STIX}{entity_type}/{entity['id']}")
        
        # Add type
        self.g.add((entity_uri, RDF.type, STIX[entity_type]))
        
        # Add properties
        for prop, value in entity.items():
            if prop in ['id', 'type']:
                continue
            self._add_property(entity_uri, prop, value)
        
        return self.g
    
    def _add_property(self, subject, predicate, value):
        """Handle different value types"""
        predicate_uri = STIX[predicate.replace("-", "_")]
        
        if isinstance(value, list):
            for item in value:
                self._add_value(subject, predicate_uri, item)
        else:
            self._add_value(subject, predicate_uri, value)
    
    def _add_value(self, subject, predicate, value):
        """Add triples with proper literal typing"""
        if isinstance(value, dict) and 'id' in value:
            # Handle relationships
            obj_uri = URIRef(f"{STIX}{value['type'].replace('-', '_')}/{value['id']}")
            self.g.add((subject, predicate, obj_uri))
        else:
            self.g.add((subject, predicate, Literal(str(value))))