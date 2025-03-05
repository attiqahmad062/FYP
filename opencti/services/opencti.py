from pycti import OpenCTIApiClient

class OpenCTIService:
    def __init__(self, url, token):
        self.client = OpenCTIApiClient(url=url, token=token)
    
    def get_all_entities(self):
        """Fetch all STIX objects with relationships"""
        return self.client.opencti_helper.list_entities(
            entity_type="all",
            filters=[],
            pagination={"first": 1000},
            with_pagination=False
        )