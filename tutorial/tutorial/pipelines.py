
import re
import scrapy
import time
import html
from itemadapter import ItemAdapter
from rdflib import Literal
from datetime import datetime
from spacy.language import Language
from transformers import AutoTokenizer, AutoModelForTokenClassification
from spacy.tokens import Doc
import torch
# Load the Hugging Face tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("bnsapa/cybersecurity-ner")
hf_model = AutoModelForTokenClassification.from_pretrained("bnsapa/cybersecurity-ner")
from SPARQLWrapper import SPARQLWrapper, JSON, POST, URLENCODED
import spacy
GRAPHDB_SETTINGS = {
    'endpoint': 'http://localhost:7200/repositories/etiapt/statements',
    'prefix': 'https://attack.mitre.org/'
}
class GroupTable(scrapy.Item):
    MittreName = scrapy.Field()
    GroupName = scrapy.Field() 
    Summary = scrapy.Field()
    AssociatedGroups = scrapy.Field()
    Url = scrapy.Field()

class TechniquesTable(scrapy.Item):
    TID = scrapy.Field()
    Use = scrapy.Field()
    Domain = scrapy.Field()  
    References = scrapy.Field()
    SubId = scrapy.Field()
    GroupId = scrapy.Field()
    Name = scrapy.Field()
class SoftwareTable(scrapy.Item):
    SID = scrapy.Field()
    GroupId = scrapy.Field()
    Name = scrapy.Field()
    References = scrapy.Field()
    Techniques = scrapy.Field()
class CampaignsTable(scrapy.Item):
    CID = scrapy.Field()
    Name = scrapy.Field()
    FirstSeen = scrapy.Field()
    GroupId = scrapy.Field() 
    LastSeen = scrapy.Field()
    References = scrapy.Field()
    Techniques = scrapy.Field()

class SubTechniques(scrapy.Item):
    STID = scrapy.Field()
    Name = scrapy.Field()

class ProcedureExamples(scrapy.Item):
    PID = scrapy.Field()
    Name = scrapy.Field()
    Description = scrapy.Field()
    References=scrapy.Field()
    TechniqueId=scrapy.Field()
class Mitigations(scrapy.Item):
    MID = scrapy.Field()
    Mitigation = scrapy.Field()
    Description = scrapy.Field()
    References=scrapy.Field()
    TechniqueId=scrapy.Field()
class Detections(scrapy.Item):
    DID = scrapy.Field()
    DataSource = scrapy.Field()
    DataComponent = scrapy.Field()
    Detects = scrapy.Field()
    References=scrapy.Field()
    TechniqueId=scrapy.Field()
    # model for mitigations

if not Doc.has_extension("ner_type"):
    Doc.set_extension("ner_type", default=None)
@Language.component("cybersecurity_ner")
def cybersecurity_ner(doc):
        # Unpack the tuple (doc, type)
  if doc is None or len(doc) == 0:
        print("Error: 'doc' is not initialized or is empty.")
        return doc  # Return the empty doc to avoid further issues    
  ner_type = doc._.ner_type
  print("type - : ",ner_type)
    # Mitigation-specific processing
  if ner_type == "mitigations":
        tokens = [token.text for token in doc]
        try:
            inputs = tokenizer(tokens, return_tensors="pt", is_split_into_words=True, truncation=True, padding=True)
        except Exception as e:
            print(f"Tokenization error: {e}")
            return doc

        with torch.no_grad():
            outputs = hf_model (**inputs).logits

        predicted_token_class_indices = torch.argmax(outputs, dim=2).squeeze().tolist()
        predicted_labels = [hf_model.config.id2label[idx] for idx in predicted_token_class_indices]

        subword_mask = inputs.word_ids()
        previous_word_id = None
        full_word_label = ""

        for i, token in enumerate(doc):
            word_id = subword_mask[i]
            if word_id != previous_word_id:
                if previous_word_id is not None and full_word_label:
                    doc[previous_word_id].ent_type_ = full_word_label
                full_word_label = predicted_labels[i] if predicted_labels[i] != 'O' else ''
            previous_word_id = word_id

        if previous_word_id is not None and full_word_label:
            doc[previous_word_id].ent_type_ = full_word_label
        # Additional label handling for mitigation-specific entities
        for token in doc:
            if token.text.lower().startswith("alert") or token.text.lower().startswith("report"):
                token.ent_type_ = "Alerting or Reporting"
                print("i got alert")
            elif "registry key" in token.text.lower():
                token.ent_type_ = "Registry Keys"
            elif token.text.startswith("HKLM\\") or "SOFTWARE" in token.text.upper() or "Microsoft" in token.text:
                token.ent_type_ = "Registry Keys"
            elif token.text.startswith("\\"):
                token.ent_type_ = "Paths"

        return doc
  else:    
    tokens = [token.text for token in doc]

    # Tokenize the text using Hugging Face's tokenizer
    try:
        inputs = tokenizer(tokens, return_tensors="pt", is_split_into_words=True, truncation=True, padding=True)
    except Exception as e:
        print(f"Tokenization error: {e}")
        return doc
 
    # Get predictions from Hugging Face model
    with torch.no_grad():
        outputs = hf_model(**inputs).logits

    # Map the predictions to their corresponding labels
    predicted_token_class_indices = torch.argmax(outputs, dim=2).squeeze().tolist()
    predicted_labels = [hf_model.config.id2label[idx] for idx in predicted_token_class_indices]

    # Initialize variables for subword processing
    subword_mask = inputs.word_ids()
    previous_word_id = None
    full_word = ""
    full_word_label = ""

    for i, token in enumerate(doc):
        word_id = subword_mask[i]

        if word_id != previous_word_id:
            # Assign the previous word if needed
            if previous_word_id is not None and full_word_label:
                doc[previous_word_id].set_extension("hf_ent_type", default=None, force=True)
                doc[previous_word_id]._.hf_ent_type = full_word_label

            # Reset for a new word
            full_word = token.text
            full_word_label = predicted_labels[i] if predicted_labels[i] != 'O' else ''
        else:
            full_word += token.text.replace("##", "")

        previous_word_id = word_id

    # Assign the last word if necessary
    if previous_word_id is not None and full_word_label:
        doc[previous_word_id].set_extension("hf_ent_type", default=None, force=True)
        doc[previous_word_id]._.hf_ent_type = full_word_label

    return doc

# Add the custom Hugging Face NER component at the end of the spaCy pipeline


class MySQLPipeline:
    def open_spider(self, spider):
        self.sparql = SPARQLWrapper(GRAPHDB_SETTINGS['endpoint'])
        self.nlp = spacy.load("en_core_web_sm")
        self.nlp.add_pipe("cybersecurity_ner", last=True)
        print("Connection to GraphDB established")
    def close_spider(self, spider):
        # GraphDB connection does not need explicit closing
        pass
    def process_item(self, item, spider):
        try:
            if isinstance(item, GroupTable):
                query = self.create_group_table_query(item) 
            elif isinstance(item, TechniquesTable):
                query = self.create_techniques_table_query(item)
                print(query)
            elif isinstance(item, SoftwareTable):
                query = self.create_software_table_query(item)
            elif isinstance(item, CampaignsTable):
                query = self.create_compains_table_query(item)
            elif isinstance(item, SubTechniques):
                query = self.create_sub_techniques_query(item)
            elif isinstance(item, ProcedureExamples):
                query = self.create_procedure_examples_query(item)
            elif isinstance(item, Mitigations):
                query = self.create_mitigations_query(item)
            elif isinstance(item, Detections):
                query = self.create_detections_query(item)
            else:
                return item   
            self.execute_sparql(query)
        except Exception as e:
            print(f"An error occurred while processing item: {e}")
        return item
    def execute_sparql(self, query):
        try:
            # query = query.strip()  # Remove leading/trailing whitespace
            query = query.encode('utf-8')  # Encode as UTF-8 (if required by SPARQLWrapper)
            self.sparql.setQuery(query)
            self.sparql.setMethod(POST)
            self.sparql.setRequestMethod(URLENCODED)
            self.sparql.query()
        except Exception as e:
            print(f"An error occurred while executing SPARQL query: {e}")
    def create_group_table_query(self, item):
        try:
                mitre_name = item.get('MittreName', '').replace('"', '\\"')
                group_name = item.get('GroupName', '').replace(' ', '_')
                associated_groups = item.get('AssociatedGroups', '').replace('"', '\\"')
                summary = item.get('Summary', '').replace('"', '\\"')
                doc = self.nlp(summary)

                group_entities = {
                    "GroupName": "",
                    "Date": "",
                    "group_belongs_to_country": "",
                    "group_attacked_country": [],
                    "Motivation": "",
                    "Aliases": []
                }
                country_found = False
                date_found = False

                # Extract entities based on labels
                for ent in doc.ents:
                    if ent.label_ == "ORG":  # Organization or Group Name
                        group_entities["GroupName"] = ent.text
                        print("ORG:", ent.text)

                    elif ent.label_ == "DATE" and not date_found:  # Store only the first date
                        group_entities["Date"] = ent.text
                        date_found = True
                        print("DATE:", ent.text)

                    elif ent.label_ == "GPE":  # Country/Location
                        if not country_found:  # First country as 'group_belongs_to_country'
                            group_entities["group_belongs_to_country"] = ent.text
                            country_found = True
                            print("Belongs to Country:", ent.text)
                        else:  # Subsequent country as 'group_attacked_country'
                            group_entities["group_attacked_country"].append(ent.text)
                            print("Attacked Country:", ent.text)

                    elif ent.label_ == "MISC":  # Motivation
                        group_entities["Motivation"] = ent.text
                        print("Motivation:", ent.text)

                    elif ent.label_ == "PERSON":  # Aliases
                        group_entities["Aliases"].append(ent.text)
                        print("Alias:", ent.text)

                print(f"Extracted Group Entities: {group_entities}")

                self.store_group_entities(mitre_name, group_entities)
                # url = item.get('Url', '').replace('"', '\\"')
 # ex:associatedGroups "{associated_groups}" ;
                        # ex:url "{url}" .
                return f"""
                PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>
                INSERT DATA {{
                        ex:{mitre_name} a ex:groups ;
                        ex:groupId "{mitre_name}" ;
                        ex:groupName "{group_name}" ;
                        ex:description "{summary}" ;
                        ex:associatedGroups  "{associated_groups}" .
                }}
                """
        except Exception as e:
                print(f"An error occurred while creating GroupTable query: {e}")
                return ""
            
    def create_techniques_table_query(self, item):
     def escape_string(value):
            if value is None:
                return ""
            return value.strip().replace("\\", "\\\\").replace("\"", "\\\"")

     try:
        technique_id = item.get('TID')
        if not technique_id:
            raise ValueError("Technique ID is missing or empty")

        # refs = self.create_references(item.get('References'), technique_id, 'technique')
        
        technique_id = escape_string(technique_id)
        technique_name = escape_string(item.get('Name'))
        use = escape_string(item.get('Use'))
        domain = escape_string(item.get('Domain'))
        sub_id = escape_string(item.get('SubId'))
        group_id = escape_string(item.get('GroupId'))
        if not technique_id or not technique_name:
            raise ValueError("Essential fields are missing")
        if sub_id:
            # If subId exists, delete any existing data with the same technique_id and sub_id
            delete_existing = f"""
            DELETE WHERE {{
                ex:{technique_id} ex:subId "{sub_id}" .
            }};
            """
        else:  
            # If subId does not exist, delete any existing data with the same technique_id and no subId
            delete_existing = f"""
            DELETE WHERE {{
                ex:{technique_id} a ex:techniques .
                FILTER(NOT EXISTS {{ ex:{technique_id} ex:subId ?subId }})
            }};
            """
#         insert_new = f"""
#     INSERT {{
#         ex:{technique_id} a ex:techniques ;
#         ex:domain "{domain}" ;
#         ex:subId "{sub_id}" ;
#         ex:techniqueName "{technique_name}" ;
#         ex:techniqueId "{technique_id}" ;
#         ex:group_uses_techniques "{group_id}" .
#         ex:{technique_id} ex:use "{use}" .

#     }}
#     WHERE {{
#         FILTER NOT EXISTS {{
#             ex:{technique_id} ex:group_uses_techniques "{group_id}" .
          
#         }}
#     }}
# """  

  

        uses = item.get('Use', '').replace('"', '\\"')
        doc = self.nlp(uses)

        # Store extracted entities from both models
        technique_entities = {
            "ORG": [],         # Organizations (from spaCy)
            "Malware": [],     # Malware (from Hugging Face)
            "GroupNames": [],  # Group Names (from spaCy)
            "Tools": [],       # Tools (from Hugging Face)
            "Tactics": []        # Tactics (from Hugging Face)
        }

        # Extract entities from spaCy's default NER model
        for ent in doc.ents:
            if ent.label_ == "ORG":
                technique_entities["ORG"].append(ent.text)
            elif ent.label_ == "PERSON":
                technique_entities["GroupNames"].append(ent.text)

        # Extract entities from Hugging Face's custom NER model
        for token in doc:
            # print("tok/en is ",token.text)
            # B-Organization
            if token._.hf_ent_type == "B-Organization":
                technique_entities["ORG"].append(token.text)
            if token._.hf_ent_type == "B-Malware":
                technique_entities["Malware"].append(token.text)
            elif token._.hf_ent_type == "I-System":
                technique_entities["Tools"].append(token.text)
            elif token._.hf_ent_type == "B-System":
                technique_entities["Tools"].append(token.text)
            elif token._.hf_ent_type == "TACTIC":
                technique_entities["Tactics"].append(token.text)

        # Print extracted technique entities for debugging
        # print(f"Extracted Technique Entities: {technique_entities}")
        # Store the extracted entities into GraphDB via SPARQL queries
        # self.store_technique_entities(technique_id, technique_entities)

        # return f"""
        # PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>
      
        
        # """
        # insert_new = f"""
        #     PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>

        #     INSERT {{
        #         ex:{technique_id} a ex:techniques ;
        #         ex:domain "{domain}" ;
        #         ex:subId "{sub_id}" ;
        #         ex:techniqueName "{technique_name}" ;
        #         ex:techniqueId "{technique_id}" ;
        #         ex:group_uses_techniques "{group_id}" .
        #         ex:{technique_id} ex:use "{use}" .
        #     }}
        #     WHERE {{
        #         FILTER NOT EXISTS {{
        #             ex:{technique_id} ex:group_uses_techniques "{group_id}" .
        #         }}
        #     }}
        # """
        # insert_new = insert_new.encode('utf-8')
      
        return f"""
            PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>

            INSERT {{
                ex:{technique_id} a ex:techniques ;
                ex:domain "{domain}" ;
                ex:subId "{sub_id}" ;
                ex:techniqueName "{technique_name}" ;
                ex:techniqueId "{technique_id}" ;
                ex:group_uses_techniques "{group_id}" .
                ex:{technique_id} ex:use "{use}" .
            }}
            WHERE {{
                FILTER NOT EXISTS {{
                    ex:{technique_id} ex:group_uses_techniques "{group_id}" .
                }}
            }}
        """
     except Exception as e:
        print(f"An error occurred while creating TechniquesTable query: {e}")
        return "" 
    # def create_techniques_table_query(self, item):
    #     def escape_string(value):
    #         if value is None:
    #             return ""
    #         return value.strip().replace("\\", "\\\\").replace("\"", "\\\"")

    #     try:
    #         technique_id = item.get('ID')
    #         if not technique_id:
    #             raise ValueError("Technique ID is missing or empty")

    #         refs = self.create_references(item.get('References'), technique_id, 'technique')

    #         technique_id = escape_string(technique_id)
    #         technique_name = escape_string(item.get('Name'))
    #         use = escape_string(item.get('Use'))
    #         domain = escape_string(item.get('Domain'))
    #         sub_id = escape_string(item.get('SubId'))
    #         group_id = escape_string(item.get('GroupId'))
        
    #         if not technique_id or not technique_name:
    #             raise ValueError("Essential fields are missing")

    #         return f"""
    #         PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>
    #         INSERT DATA {{
    #             ex:{technique_id} a ex:techniques ;
    #             ex:domain "{domain}" ;
    #             ex:subId "{sub_id}" ;
    #             ex:techniqueName "{technique_name}" ;
    #             ex:techniqueId "{technique_id}" ;
    #             ex:group_uses_techniques "{group_id}";
    #             ex:use "{use}" .
    #             {refs}     
    #         }} 
    #         """
    #     except Exception as e:
    #         print(f"An error occurred while creating TechniquesTable query: {e}")
    #         return ""

    def create_software_table_query(self, item):
        try:
            #  ex:techniques "{item.get('Techniques')}" .
            software_id = item.get('SID')
            # refs = self.create_references(item.get('References'), software_id, 'software')
            return f"""
            PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>
            INSERT DATA {{
                ex:{software_id} a ex:softwares ;
                    ex:softwareName "{item.get('Name')}" ;
                    ex:softwareTechniques "{item.get('Techniques')}" ;
                    ex:group_uses_software "{item.get('GroupId')}";
                    ex:softwareId "{software_id}" .
                
            }}  
            """
        except Exception as e:
            print(f"An error occurred while creating SoftwareTable query: {e}")
            return ""
    #       ID = scrapy.Field()
    # Name = scrapy.Field()
    # FirstSeen = scrapy.Field()
    # LastSeen = scrapy.Field()
    # References = scrapy.Field()
    # Techniques = scrapy.Field()
    

    def create_compains_table_query(self, item):
        def escape_string(value):
            if value is None:
                return ""
            return value.strip().replace("\\", "\\\\").replace("\"", "\\\"")

        def format_date(date_string):
            try:
                # Attempt to parse the date string (assuming the format is like 'June 2022')
                parsed_date = datetime.strptime(date_string, "%B %Y")
                # Return the date in xsd:date format (YYYY-MM-DD)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                # If parsing fails, return the original string, but this might still cause issues
                return date_string

        try:
            campaign_id = escape_string(item.get('CID'))
            first_seen = format_date(escape_string(item.get('FirstSeen')))
            last_seen = format_date(escape_string(item.get('LastSeen')))
            techniques = item.get('Techniques')
            
            # refs = self.create_references(item.get('References'), campaign_id, 'campaign')

            techniques_triples = ""
            if techniques:
                techniques_triples = "\n".join(
                    [f'ex:{campaign_id} ex:campaignsTechniques "{escape_string(technique)}" .' for technique in techniques]
                )
            return f"""
            PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            INSERT DATA {{
                    ex:{campaign_id} a ex:campaigns ;
                    ex:campaignName "{escape_string(item.get('Name'))}" ;
                    ex:campaignId "{campaign_id}" ;
                    ex:group_ispartof_campaigns "{escape_string(item.get('GroupId'))}" ;
                    ex:campaignsFirstseen "{first_seen}"^^xsd:date ;
                    ex:campaignsLastseen "{last_seen}"^^xsd:date .
                    {techniques_triples}
                   
            }}
            """
        except Exception as e:
            print(f"An error occurred while creating CompainsTable query: {e}")
            return ""

    # def create_compains_table_query(self, item):
    #     def escape_string(value):
    #         if value is None:
    #             return ""
    #         return value.strip().replace("\\", "\\\\").replace("\"", "\\\"")
    #     try:
    #         campaign_id=escape_string(item.get('ID'))
    #         first_seen=escape_string(item.get('FirstSeen')) 
    #         last_seen=escape_string(item.get('LastSeen')) 
    #         # techniques=escape_string(item.get('Techniques')) 
    #         refs = self.create_references(item.get('References'), campaign_id, 'campaign')
    #         return f"""
    #         PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>
    #         INSERT DATA {{
    #                 ex:{campaign_id} a ex:campaigns ;
    #                 ex:campaignName "{item.get('Name')}" ;
    #                 ex:campaignId "{item.get('ID')}" ;
    #                 ex:group_ispartof_campaigns "{item.get('GroupId')}";
    #                 ex:campaignsTechniques "{item.get('Techniques')}" .
    #                 ex:campaignsFirstseen "{first_seen}" .
    #                 ex:campaignsLastseen "{last_seen}" .
    #                 {refs}
    #         }}
    #         """
    #     except Exception as e:
    #         print(f"An error occurred while creating CompainsTable query: {e}")
    #         return ""

    # def create_sub_techniques_query(self, item):
    #     try:
    #         return f"""
    #         PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>
    #         INSERT DATA {{
    #             ex:{item.get('ID')} a ex:subtechniques ;
    #                 ex:name "{item.get('Name')}" .
    #         }}
    #         """
    #     except Exception as e:
    #         print(f"An error occurred while creating SubTechniques query: {e}")
    #         return ""
    def create_procedure_examples_query(self, item):
     def escape_string(value):
        if value is None:
            return ""
        return value.strip().replace("\\", "\\\\").replace("\"", "\\\"")
     try: 
        procedure_id = escape_string(item.get('PID'))
        if not procedure_id:
            raise ValueError("Technique ID is missing or empty")
        name = escape_string(item.get('Name'))
        description = escape_string(item.get('Description'))
        # refs = self.create_references(item.get('References'), procedure_id, 'procedure')
        doc = self.nlp(description)

        # Store extracted entities from both models
        procedure_entities = {
            "ORG": [],         # Organizations (from spaCy)
            "Malware": [],     # Malware (from Hugging Face)
            "GroupNames": [],  # Group Names (from spaCy)
            "Tools": [],       # Tools (from Hugging Face)
            "Tactics": []      # Tactics (from Hugging Face)
        }

        # Extract entities from spaCy's default NER model
        for ent in doc.ents:
            if ent.label_ == "ORG":
                procedure_entities["ORG"].append(ent.text)
            elif ent.label_ == "PERSON":
                procedure_entities["GroupNames"].append(ent.text)

        # Extract entities from Hugging Face's custom NER model
        for token in doc:
            print("token is ",token.text)
            # B-Organization
            if token._.hf_ent_type == "B-Organization":
                procedure_entities["ORG"].append(token.text)
            if token._.hf_ent_type == "B-Malware":
                procedure_entities["Malware"].append(token.text)
            elif token._.hf_ent_type == "I-System":
                procedure_entities["Tools"].append(token.text)
            elif token._.hf_ent_type == "B-System":
                procedure_entities["Tools"].append(token.text)
            elif token._.hf_ent_type == "TACTIC":
                procedure_entities["Tactics"].append(token.text)
        for key in procedure_entities:
         procedure_entities[key] = ', '.join(procedure_entities[key])
        # Print extracted technique entities for debugging
        print(f"Extracted Procedure Entities: {procedure_entities}")
        # Store the extracted entities into GraphDB via SPARQL queries
        self.store_procedure_entities(procedure_id, procedure_entities)
        procedure_uri = f"<https://attack.mitre.org/procedures/{procedure_id}>"
        return f"""
        PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>
        INSERT DATA {{
            {procedure_uri} a ex:procedures ;
                ex:procedureName  "{name}" ;
                ex:technique_implements_procedures "{item.get("TechniqueId")}";
                ex:description "{description}" 
            
        }}
        """
     except Exception as e:
        print(f"An error occurred while creating ProcedureExamples query: {e}")
        return ""

    def create_mitigations_query(self, item):
        def escape_string(value):
            if value is None:
                return ""
            return value.strip().replace("\\", "\\\\").replace("\"", "\\\"")
        try:
            mitigation_id = escape_string(item.get('MID'))
            if not mitigation_id :
             raise ValueError("Technique ID is missing or empty") 
            description = escape_string(item.get('Description'))
            # refs = self.create_references(item.get('References'), mitigation_id, 'mitigation')
           
            # Sample text to test
            # Process the text
   
            ner_type = "mitigations"
            doc = self.nlp(description)
            doc._.ner_type = ner_type
            doc = self.nlp(doc)
            # doc = self.nlp(description)
            mitigation_entities = {
            "Alerting or Reporting": [],         # Organizations (from spaCy)
            "Registry Keys": [],     # Malware (from Hugging Face)
            "Paths": [],  # Group Names (from spaCy)
        }
            print("doc is ",mitigation_entities)
            for token in doc:
                # print("token is ",token.text)
            # B-Organization
                if token._.hf_ent_type == "Alerting or Reporting":
                    mitigation_entities["Alerting or Reporting"].append(token.text)
                if token._.hf_ent_type == "Registry Keys":
                    mitigation_entities["Registry Keys"].append(token.text)
                elif token._.hf_ent_type == "Paths":
                    mitigation_entities["Paths"].append(token.text)
                # if token.text.lower().startswith("alert") or token.text.lower().startswith("report"):
                #      mitigation_entities["Alerting or Reporting"].append(token.text)
                # elif "registry key" in token.text.lower():
                #     token.hf_ent_type = "Registry Keys"
                # elif token.text.startswith("HKLM\\") or "SOFTWARE" in token.text.upper() or "Microsoft" in token.text:
                #     mitigation_entities["Registry Keys"].append(token.text)
                # elif token.text.startswith("\\"):
                #     mitigation_entities["Paths"].append(token.text)
            # Extract and organize recognized entities
            # mitigation_entities = {}

            # for token in doc:
            #     if token.ent_type_:
            #         # Add the entity type to the mitigation_entities dictionary dynamicall
            #         mitigation_entities[token.ent_type_].append(token.text)

            # Log the recognized entities for debugging


            print("Mitigation Entities:", mitigation_entities)
            # self.store_mitigation_entities(mitigation_id, mitigation_entities)
            mtigation_uri = f"<https://attack.mitre.org/mitigations/{mitigation_id}>"
            return f"""
            PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>
            INSERT DATA {{
                ex:{mtigation_uri} a ex:mitigations ;
                    ex:mitigationName "{item.get('Mitigation')}" ;   
                    ex:description "{description}" ;
                    ex:technique_implements_mitigations "{item.get("TechniqueId")}" .
            }}
            """
        except Exception as e:
            print(f"An error occurred while creating Mitigations query: {e}")
            return ""
    def create_detections_query(self, item):
        def escape_string(value):
            if value is None:
                return ""
            return value.strip().replace("\\", "\\\\").replace("\"", "\\\"")
        try:
            detects = escape_string(item.get('Detects'))
            detection_id = escape_string(item.get('DID'))
            if not detection_id :
             raise ValueError("Technique ID is missing or empty") 
           
            refs = self.create_references(item.get('References'), detection_id, 'detection')
            doc = self.nlp(detects)

            # Store extracted entities from both models
            detection_entities = {
                "ORG": [],         # Organizations (from spaCy)
                "Malware": [],     # Malware (from Hugging Face)
                "GroupNames": [],  # Group Names (from spaCy)
                "Tools": [],       # Tools (from Hugging Face)
                "Tactics": []      # Tactics (from Hugging Face)
            }

            # Extract entities from spaCy's default NER model
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    detection_entities["ORG"].append(ent.text)
                elif ent.label_ == "PERSON":
                    detection_entities["GroupNames"].append(ent.text)

            # Extract entities from Hugging Face's custom NER model
            for token in doc:
                print("token is ",token.text)
                # B-Organization
                if token._.hf_ent_type == "B-Organization":
                    detection_entities["ORG"].append(token.text)
                if token._.hf_ent_type == "B-Malware":
                    detection_entities["Malware"].append(token.text)
                elif token._.hf_ent_type == "I-System":
                    detection_entities["Tools"].append(token.text)
                elif token._.hf_ent_type == "B-System":
                    detection_entities["Tools"].append(token.text)
                elif token._.hf_ent_type == "TACTIC":
                    detection_entities["Tactics"].append(token.text)
            for key in detection_entities:
                detection_entities[key] = ', '.join(detection_entities[key])
            # Print extracted technique entities for debugging
            print(f"Extracted Procedure Entities: {detection_entities}")
            # Store the extracted entities into GraphDB via SPARQL queries
            # self.store_detection_entities(detection_id, detection_entities)
            detection_uri = f"<https://attack.mitre.org/detections/{detection_id}>"
            return f""" 
            PREFIX ex: <{GRAPHDB_SETTINGS['prefix']}>
            INSERT DATA {{
                {detection_uri} a ex:detections ;
                    ex:detectionId "{detection_id}";
                    ex:dataSource "{item.get('DataSource')}" ;
                    ex:detects "{detects}" ;
                    ex:dataComponent "{item.get('DataComponent')}" ;
                    ex:technique_implements_detections"{item.get("TechniqueId")}"
                    
            }}
            """
        except Exception as e:
            print(f"An error occurred while creating Mitigations query: {e}")
            return ""
 
    def create_references(self, references, id, ref_type):
        # try:
        #     links = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', references)
        #     triples = ""
        #     for i, link in enumerate(links, start=1):
        #         triples += f'ex:{id}  a  ex:referenceUrl; ex:url "{link}" .\n'
        #     return triples
        # except Exception as e:
        #     print(f"An error occurred while creating references: {e}")
        #     return ""
        # try:
        #         triples = ""
        #         for ref in references:
        #             link = ref.get("link", "").strip()
        #             body = ref.get("body", "").strip()
                    
        #             if link:  # Ensure the link is not empty
        #                 triples += f'ex:{id} a ex:referenceUrl; ex:url "{link}"'
        #                 if body:  # Add the body if it exists
        #                     triples += f'; ex:body "{body}"'
        #                     print("body in graph db " ,body) 
        #                 triples += " .\n" 
                
        #         return triples
        # except Exception as e:
        #         print(f"An error occurred while creating references: {e}")
        #         return ""

        def escape_sparql_literal(value):
            return html.escape(value).replace('"', '\\"').replace('\n', '\\n')

        # Generate the SPARQL query
        # sparql_query = f"""
        # PREFIX ex: <https://attack.mitre.org/>
        # INSERT DATA {{
        #     ex:{id} ex:referenceUrl [
        #         ex:url "{escape_sparql_literal(link)}"^^xsd:string
        #         {f'; ex:body "{escape_sparql_literal(body)}"^^xsd:string' if body else ''}
        #     ] .
        # }}
        # """
        try:
            for ref in references:
                link = ref.get("link", "").strip()
                body = ref.get("body", "").strip()
                id_iri = f'<https://attack.mitre.org/{id}>'
                if link:  
                        if body:
                            body = re.sub(r'["\\]', r'\\\g<0>', body)  # Escape quotes and backslashes
                            body = re.sub(r'[\n\r\t]', ' ', body)  # Remove newlines, tabs
                        # Construct SPARQL query
                        print("Program resumes after 10 seconds")
                       
                        sparql_query = f"""
                        PREFIX ex: <https://attack.mitre.org/>
                        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                        INSERT DATA {{
                            {id_iri} ex:referenceUrl [
                                ex:url "{link}"^^xsd:string ;
                                {f'ex:refBody "{body}"^^xsd:string ;' if body else ''}
                            ] .
                        }}
                        """

                        # print(f"Executing SPARQL Query:\n{sparql_query}")
                        # Set up the SPARQL endpoint and execute the query
                        try:
                            self.sparql.setQuery(sparql_query)
                            self.sparql.setMethod(POST)
                            self.sparql.setReturnFormat(JSON)
                            
                            response = self.sparql.query()
                            # print(response)
                            try:
                                response = self.sparql.query().convert()
                                print("Query executed successfully!")
                                print(f"Inserted reference successfully: {link}")
                            except Exception as e:
                                print("Error executing query:", e)
                            # response_str = str(response)
                            # response_lines = response_str.split("\n")  # Split response into lines
                            
                            #     # Print only the first four lines
                            # print("\n".join(response_lines[:4]))  
                            
                                # Convert response to string and split into lines
                            time.sleep(10)
                        
                        except Exception as e:
                            print(f"SPARQL Query Execution Failed: {e}")

                        # time.sleep(100)  # Sleep for 10 seconds
                        
                        # Execute the query
                        
                        
                
            return {"status": "success", "message": "All references inserted successfully."}
        
        except Exception as e:
            print(f"Error inserting references: {e}")
            return {"status": "error", "message": str(e)}



    def store_group_entities(self, group_uri, group_entities):
        # Ensure group_uri is enclosed in angle brackets if it's a full URI
        group_uri = f"<https://attack.mitre.org/{group_uri}>"
        if not group_uri.startswith("<"):
            group_uri = f"<{group_uri}>"
        # Store Group Name / Organization
        if group_entities.get("GroupName"):
            group_name_literal = Literal(group_entities['GroupName']).n3()
            group_name_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {group_uri} ex:groupName ?oldName }}
            INSERT {{ {group_uri} ex:groupName {group_name_literal} }}
            WHERE {{ {group_uri} ex:description ?desc }}
            """
            self.sparql.setQuery(group_name_query)
            self.sparql.setMethod('POST')
            self.sparql.query()
        # Store Dates
        if group_entities.get("Date"):
            date_literal = Literal(group_entities['Date']).n3()
            date_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {group_uri} ex:date ?oldDate }}
            INSERT {{ {group_uri} ex:date {date_literal} }}
            WHERE {{ {group_uri} ex:description ?desc }}
            """
            self.sparql.setQuery(date_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Country / Location group_attacked_country
        if group_entities.get("group_belongs_to_country"):
            country_literal = Literal(group_entities['group_belongs_to_country']).n3()
            country_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {group_uri} ex:group_belongs_to_country ?oldCountry }}
            INSERT {{ {group_uri} ex:group_belongs_to_country {country_literal} }}
            WHERE {{ {group_uri} ex:description ?desc }}
            """ 
            self.sparql.setQuery(country_query)  
            self.sparql.setMethod('POST')
            self.sparql.query()
        if group_entities.get("group_attacked_country"):
            country_literal = Literal(group_entities['group_attacked_country']).n3()
            country_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {group_uri} ex:group_attacked_country ?oldCountry }}
            INSERT {{ {group_uri} ex:group_attacked_country {country_literal} }}
            WHERE {{ {group_uri} ex:description ?desc }}
            """
            self.sparql.setQuery(country_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Motivation (Financial Gain, Trade, etc.)
        if group_entities.get("Motivation"):
            motivation_literal = Literal(group_entities['Motivation']).n3()
            motivation_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {group_uri} ex:motivation ?oldMotivation }}
            INSERT {{ {group_uri} ex:motivation {motivation_literal} }}
            WHERE {{ {group_uri} ex:description ?desc }}
            """
            self.sparql.setQuery(motivation_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Aliases
        for alias in group_entities.get("Aliases", []):
            alias_literal = Literal(alias).n3()
            alias_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {group_uri} ex:alias ?oldAlias }}
            INSERT {{ {group_uri} ex:alias {alias_literal} }}
            WHERE {{ {group_uri} ex:description ?desc }}
            """
            self.sparql.setQuery(alias_query)
            self.sparql.setMethod('POST')
            self.sparql.query()
    def store_technique_entities(self, technique_uri, technique_entities):
    # Ensure technique_uri is enclosed in angle brackets if it's a full URI
        technique_uri = f"<https://attack.mitre.org/{technique_uri}>"
        if not technique_uri.startswith("<"):
            technique_uri = f"<{technique_uri}>"

        # Store ORG (Organizations)
        if technique_entities.get("ORG"):
            org_literal = Literal(technique_entities['ORG']).n3()
            org_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {technique_uri} ex:org ?oldOrg }}
            INSERT {{ {technique_uri} ex:org {org_literal} }}
            WHERE {{ {technique_uri} ex:use ?desc }}
            """
            self.sparql.setQuery(org_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Malware
        if technique_entities.get("Malware"):
            malware_literal = Literal(technique_entities['Malware']).n3()
            malware_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {technique_uri} ex:malware ?oldMalware }}
            INSERT {{ {technique_uri} ex:malware {malware_literal} }}
            WHERE {{ {technique_uri} ex:use ?desc }}
            """
            self.sparql.setQuery(malware_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Group Names
        if technique_entities.get("GroupNames"):
            group_name_literal = Literal(technique_entities['GroupNames']).n3()
            group_name_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {technique_uri} ex:groupName ?oldGroupName }}
            INSERT {{ {technique_uri} ex:groupName {group_name_literal} }}
            WHERE {{ {technique_uri} ex:use ?desc }}
            """
            self.sparql.setQuery(group_name_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Tools
        if technique_entities.get("Tools"):
            tools_literal = Literal(technique_entities['Tools']).n3()
            tools_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {technique_uri} ex:tools ?oldTools }}
            INSERT {{ {technique_uri} ex:tools {tools_literal} }}
            WHERE {{ {technique_uri} ex:use ?desc }}
            """
            self.sparql.setQuery(tools_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Tactics
        if technique_entities.get("Tactics"):
            tactics_literal = Literal(technique_entities['Tactics']).n3()
            tactics_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {technique_uri} ex:tactics ?oldTactics }}
            INSERT {{ {technique_uri} ex:tactics {tactics_literal} }}
            WHERE {{ {technique_uri} ex:use ?desc }}
            """
            self.sparql.setQuery(tactics_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

            # storing mitigation entities to graph DB 
    def store_mitigation_entities(self, mitigation_id, mitigation_entities):
        mitigation_uri = f"<https://attack.mitre.org/mitigations/{mitigation_id}>"

        # Store Alerting or Reporting entities
        if mitigation_entities.get("Alerting or Reporting"):
            for alert in mitigation_entities["Alerting or Reporting"]:
                alert_literal = Literal(alert).n3()
                alert_query = f"""
                PREFIX ex: <https://attack.mitre.org/>
                DELETE {{ {mitigation_uri} ex:alertingOrReporting ?oldAlert }}
                INSERT {{ {mitigation_uri} ex:alertingOrReporting {alert_literal} }}
                WHERE {{ {mitigation_uri} ex:description ?desc }}
                """
                self.sparql.setQuery(alert_query)
                self.sparql.setMethod('POST')
                self.sparql.query()

        # Store Registry Keys entities
        if mitigation_entities.get("Registry Keys"):
            for reg_key in mitigation_entities["Registry Keys"]:
                reg_key_literal = Literal(reg_key).n3()
                reg_key_query = f"""
                PREFIX ex: <https://attack.mitre.org/>
                DELETE {{ {mitigation_uri} ex:registryKeys ?oldRegKey }}
                INSERT {{ {mitigation_uri} ex:registryKeys {reg_key_literal} }}
                WHERE {{ {mitigation_uri} ex:description ?desc }}
                """
                self.sparql.setQuery(reg_key_query)
                self.sparql.setMethod('POST')
                self.sparql.query()

        # Store Paths entities
        if mitigation_entities.get("Paths"):
            for path in mitigation_entities["Paths"]:
                path_literal = Literal(path).n3()
                path_query = f"""
                PREFIX ex: <https://attack.mitre.org/>
                DELETE {{ {mitigation_uri} ex:paths ?oldPath }}
                INSERT {{ {mitigation_uri} ex:paths {path_literal} }}
                WHERE {{ {mitigation_uri} ex:description ?desc }}
                """
                self.sparql.setQuery(path_query)
                self.sparql.setMethod('POST')
                self.sparql.query()
    def store_procedure_entities(self, procedure_id, procedure_entities):
        print("Storing procedure entities for ID:", procedure_id)
        procedure_uri = f"<https://attack.mitre.org/procedures/{procedure_id}>"
        # Store ORG entities
        if procedure_entities.get("ORG"):
            # for org in procedure_entities["ORG"]:
                org_literal = Literal(procedure_entities["ORG"]).n3()  # Convert each org to a literal
                print("Storing ORG:", org_literal)
                org_query = f"""
                PREFIX ex: <https://attack.mitre.org/>
                 DELETE {{ {procedure_uri} ex:org ?oldCountry }}
                INSERT  {{ {procedure_uri} ex:org {org_literal} }} 
                WHERE {{ {procedure_uri} ex:description ?desc }}
                """
                self.sparql.setQuery(org_query)
                self.sparql.setMethod('POST' )
                self.sparql.query()
        # Store Malware entities
        if procedure_entities.get("Malware"):
            # for malware in procedure_entities["Malware"]:
                malware_literal = Literal(procedure_entities['Malware']).n3()  # Convert each malware to a literal
                print("Storing Malware:", malware_literal)
                malware_query = f"""
                PREFIX ex: <https://attack.mitre.org/>
                 DELETE {{ {procedure_uri} ex:procedureMalware ?oldCountry }}
                INSERT  {{ {procedure_uri}  ex:procedureMalware {malware_literal}  }}
                  WHERE {{ {procedure_uri} ex:description ?desc }}
                """
                self.sparql.setQuery(malware_query)
                self.sparql.setMethod('POST')
                self.sparql.query()
        # Store Tools entities
        if procedure_entities.get("Tools"):
            # for tool in procedure_entities["Tools"]:
                tool_literal = Literal(procedure_entities['Tools']).n3()  # Convert each tool to a literal
                print("Storing Tool:", tool_literal)
                tool_query = f"""
                PREFIX ex: <https://attack.mitre.org/>
             DELETE {{ {procedure_uri} ex:tool ?oldCountry }}
                INSERT  {{
                    {procedure_uri} ex:tool {tool_literal}  
                }}
              WHERE {{ {procedure_uri} ex:description ?desc }} 
                """
                self.sparql.setQuery(tool_query)
                self.sparql.setMethod('POST')
                try:
            # Execute the query
                    self.sparql.query()
                    print("Tool stored successfully.")
                except Exception as e:
                    print("Error executing SPARQL query:", e)
# Store Detections  in Graph DB
    def store_detection_entities(self, detection_id, detection_entities):
        print("Storing procedure entities for ID:", detection_id)
        detection_uri = f"<https://attack.mitre.org/detections/{detection_id}>"
        
        # Store ORG entities
        if detection_entities.get("ORG"):
            # for org in procedure_entities["ORG"]:
                org_literal = Literal(detection_entities["ORG"]).n3()  # Convert each org to a literal
                print("Storing ORG:", org_literal)
                org_query = f"""
                PREFIX ex: <https://attack.mitre.org/>
                 DELETE {{ {detection_uri} ex:detectsORG ?OlddetectsORG }}
                INSERT  {{ {detection_uri} ex:detectsORG {org_literal} }} 
                WHERE {{ {detection_uri} ex:detects ?desc }} 
                """
                self.sparql.setQuery(org_query)
                self.sparql.setMethod('POST' )
                self.sparql.query()

        # Store Malware entities
        if detection_entities.get("Malware"):
            # for malware in procedure_entities["Malware"]:
                malware_literal = Literal(detection_entities['Malware']).n3()  # Convert each malware to a literal
                print("Storing Malware:", malware_literal)
                malware_query = f"""
                PREFIX ex: <https://attack.mitre.org/>
                 DELETE {{ {detection_uri} ex:detectsMalware ?OlddetectsMalware }}
                INSERT  {{ {detection_uri}  ex:detectsMalware {malware_literal}  }}
                WHERE {{ {detection_uri} ex:detects ?desc }} 
                """
                self.sparql.setQuery(malware_query)
                self.sparql.setMethod('POST')
                self.sparql.query()

        # Store Tools entities
        if detection_entities.get("Tools"):
            # for tool in procedure_entities["Tools"]:
                tool_literal = Literal(detection_entities['Tools']).n3()  # Convert each tool to a literal
                print("Storing Tool:", tool_literal)
                tool_query = f"""
                PREFIX ex: <https://attack.mitre.org/>
             DELETE {{ {detection_uri} ex:detectsTool ?olddetectsTool }}
                INSERT  {{
                    {detection_uri} ex:detectsTool {tool_literal}  

                }}
             WHERE {{ {detection_uri} ex:detects ?desc }} 
                """
                self.sparql.setQuery(tool_query)
                self.sparql.setMethod('POST')
                try:
            # Execute the query
                    self.sparql.query()
                    print("Tool stored successfully.")
                except Exception as e:
                    print("Error executing SPARQL query:", e)
    def store_campaigns_entities(self,campaigns_uri , campaigns_entities):
        # Ensure group_uri is enclosed in angle brackets if it's a full URI
        campaigns_uri = f"<https://attack.mitre.org/campaigns/{campaigns_uri}>"
        if not campaigns_uri.startswith("<"):
            campaigns_uri = f"<{campaigns_uri}>"

        # Store Group Name / Organization
        if campaigns_entities.get("GroupName"):
            campaigns_name_literal = Literal(campaigns_entities['GroupName']).n3()
            campaigns_name_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {campaigns_uri} ex:groupName ?oldName }}
            INSERT {{ {campaigns_uri} ex:groupName {campaigns_name_literal} }}
            WHERE {{ {campaigns_uri} ex:description ?desc }}
            """
            self.sparql.setQuery(campaigns_name_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Dates
        if campaigns_entities.get("Date"):
            date_literal = Literal(campaigns_entities['Date']).n3()
            date_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {campaigns_uri} ex:date ?oldDate }}
            INSERT {{ {campaigns_uri} ex:date {date_literal} }}
            WHERE {{ {campaigns_uri} ex:description ?desc }}
            """
            self.sparql.setQuery(date_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Country / Location
        if campaigns_entities.get("Country"):
            country_literal = Literal(campaigns_entities['Country']).n3()
            country_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {campaigns_uri} ex:country ?oldCountry }}
            INSERT {{ {campaigns_uri} ex:country {country_literal} }}
            WHERE {{ {campaigns_uri} ex:description ?desc }}
            """
            self.sparql.setQuery(country_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Motivation (Financial Gain, Trade, etc.)
        if campaigns_entities.get("Motivation"):
            motivation_literal = Literal(campaigns_entities['Motivation']).n3()
            motivation_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {campaigns_uri} ex:motivation ?oldMotivation }}
            INSERT {{ {campaigns_uri} ex:motivation {motivation_literal} }}
            WHERE {{ {campaigns_uri} ex:description ?desc }}
            """
            self.sparql.setQuery(motivation_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

        # Store Aliases
        for alias in campaigns_entities.get("Aliases", []):
            alias_literal = Literal(alias).n3()
            alias_query = f"""
            PREFIX ex: <https://attack.mitre.org/>
            DELETE {{ {campaigns_uri} ex:alias ?oldAlias }}
            INSERT {{ {campaigns_uri} ex:alias {alias_literal} }}
            WHERE {{ {campaigns_uri} ex:description ?desc }}
            """
            self.sparql.setQuery(alias_query)
            self.sparql.setMethod('POST')
            self.sparql.query()

# Store Detections 






 