from pycti import OpenCTIApiClient
import os
import logging
from ..config.entities import STIX_ENTITIES

logger = logging.getLogger(__name__)
class OpenCTIService:
    def __init__(self):
        self.client = OpenCTIApiClient(
            url=os.getenv("OPENCTI_URL"),
            token=os.getenv("OPENCTI_TOKEN")
        )
        self.valid_entities = [e.lower().replace("-", "_") for e in STIX_ENTITIES]

        self.entity_method_map = {
            "Threat-Actor": "threat_actor",
            "Intrusion-Set": "intrusion_set",
            "Campaign": "campaign",
            "Malware": "malware",
            "Tool": "tool",
            "Attack-Pattern": "attack_pattern",
            "Course-Of-Action": "course_of_action",
            "Indicator": "indicator",
            "Observed-Data": "observed_data",
            "Report": "report",
            "Vulnerability": "vulnerability",
            "Identity": "identity",
            "Location": "location",
            "Infrastructure": "infrastructure",
            "Opinion": "opinion",
            "Note": "note"
        }

    def get_all_stix_data(self):
        """Fetch all STIX data from OpenCTI with proper pagination"""
        data = {}
        logger.info("Starting OpenCTI data synchronization")

        # Proper filter structure required by OpenCTI API
        base_filters = {
            "mode": "and",
            "filters": [],
            "filterGroups": []
        }

        # Fetch entities
        for stix_type in STIX_ENTITIES:
            if stix_type == "Relationship":
                continue

            try:
                method_name = self.entity_method_map.get(stix_type)
                if not method_name or not hasattr(self.client, method_name):
                    logger.warning(f"No method mapping for {stix_type}, skipping")
                    continue

                entities = []
                end_of_pages = False
                after = None
                
                while not end_of_pages:
                    result = self.client.__getattribute__(method_name).list(
                        first=500,
                        after=after,
                        withPagination=True,
                        filters=base_filters  # Use proper filter structure
                    )
                    entities.extend(result.get("entities", []))
                    after = result.get("pagination", {}).get("endCursor")
                    end_of_pages = not result.get("pagination", {}).get("hasNextPage", False)

                    logger.debug(
                        f"Fetched page of {stix_type}: {len(result.get('entities', []))} items "
                        f"(Total: {len(entities)})"
                    )
                # print("entities are :",entities)
                data[stix_type] = entities
                logger.info(f"Successfully fetched {len(entities)} {stix_type} records")
                
            except Exception as e:
                logger.error(f"Failed to fetch {stix_type}: {str(e)}")
                continue

        # Fetch relationships separately
        try:
            relationships = []
            after = None
            while True:
                result = self.client.stix_core_relationship.list(
                    first=500,
                    after=after,
                    withPagination=True,
                    filters=base_filters  # Apply to relationships too
                )
                relationships.extend(result.get("entities", []))
                after = result.get("pagination", {}).get("endCursor")
                
                if not result.get("pagination", {}).get("hasNextPage", False):
                    break
                
                logger.debug(
                    f"Fetched relationship page: {len(result.get('entities', []))} items "
                    f"(Total: {len(relationships)})"
                )

            data["Relationship"] = relationships
            logger.info(f"Successfully fetched {len(relationships)} relationships")
            
        except Exception as e:
            logger.error(f"Failed to fetch relationships: {str(e)}")

        logger.info("Completed OpenCTI data synchronization")
        return data