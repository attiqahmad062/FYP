import scrapy
import re
from scrapy import Request
import PyPDF2
import io
import os
references = []
from tutorial.pipelines import GroupTable, TechniquesTable,SoftwareTable,CampaignsTable,SubTechniques,ProcedureExamples,Mitigations ,Detections
class MITREAttackSpider(scrapy.Spider):
    name = 'mitreattack'
    start_urls = ['https://attack.mitre.org/groups/']
    def extract_text_from_pdf(self, pdf_content):
        try:
            from PyPDF2 import PdfReader
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            return " ".join(page.extract_text() for page in pdf_reader.pages)
        except Exception as e:
            self.log(f"Error extracting text from PDF: {e}")
            return ""
    def save_pdf(self, response):
        pdf_text = self.extract_text_from_pdf(response.body)
        if pdf_text:
            references.append({"link": response.url, "body": pdf_text.strip()})
        

    def parse_html_reference(self, response):
        title = response.css('title::text').get(default='No Title')
        raw_body = ' '.join(response.css('body *::text').getall()).strip()

        # Clean the body text: remove excessive spaces and non-text characters
        def clean_text(text):
            text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces, tabs, or newlines with a single space
            text = re.sub(r'[^\w\s.,!?\-]', '', text)  # Remove special characters except basic punctuation
            return text.strip()

        body = clean_text(raw_body)
        link=response.url
        link = link.encode("utf-8").decode("utf-8")
        body = body.encode("utf-8").decode("utf-8") if body else ""
        if not body:
            self.log(f"Body content is missing for {link}. Verify if JavaScript is required.")
            references.append({"link":link, "body": ""})
        else:
            self.log(f"Processed HTML Reference: {title}")

            # Check if the reference already exists
            references.append({"link": link, "body": body})
            # existing_ref = next((ref for ref in references if ref['link'] == response.url), None)

            # if not existing_ref:
            #     # Add a new reference if it doesn't exist
            #     references.append({"link": response.url, "body": body})
            # else:
            #     # Update the body if the reference already exists
            #     print("Updating existing reference: ", response.url)
            #     existing_ref['body'] = body

            # self.log(f"Parsed and cleaned HTML content from: {response.url}")

    # def parse_html_reference(self, response):
    #     title = response.css('title::text').get(default='No Title')
    #     body = ' '.join(response.css('body *::text').getall()).strip()
    #     # print("body is ",body)
    #     if not body:
    #             self.log(f"Body content is missing for {response.url}. Verify if JavaScript is required.")
    #     else:
    #             self.log(f"Processed HTML Reference: {title}")
    #              # Save or further process the body content as needed
    #             # with open(f"html_refs/{os.path.basename(response.url)}.txt", "w") as f:
    #             #  f.write(f"Title:")
    #             # content = body.decode('utf-8')
    #             # references_string.append(["body",content])
    #             # references.append({"link": response.url, "body": body})
    #             existing_ref = next((ref for ref in references if ref['link'] == response.url), None)
    #             if not existing_ref:
    #                 # Add a new reference if it doesn't exist
    #                 # print("Appending reference: ", response.url, body.strip())
    #                 references.append({"link": response.url, "body": body})
    #             else:
    #                 # Update the body if the reference already exists
    #                 print("Updating existing reference: ", response.url)
    #                 existing_ref['body'] = body.strip()
    #             self.log(f"Parsed HTML content from: {response.url}")
    #             # self.log(f"Parsed HTML content from: {body}")
    def parse(self, response):# crawl the main page of groups
        # Extracting data from the table with class name 'table'
        groupTable = response.css('table.table tr')
        for row in groupTable:
            column1_data = row.css('td:nth-child(1) a::text').get()
            column1_url = row.css('td:nth-child(1) a::attr(href)').get()
            column2_data = row.css('td:nth-child(2) a::text').get()
            column3_data = row.css('td:nth-child(3)::text').get()
           # Extract all text from the summary column, including text inside links
            column4_data_list = row.css('td:nth-child(4)').xpath('.//text()').getall()
            column4_data = ' '.join([text.strip() for text in column4_data_list if text.strip()])
            column1_url = row.css('td:nth-child(1) a::attr(href)').extract_first()
            # Creating an absolute URL
            column1_url_absolute = response.urljoin(column1_url.strip()) if column1_url else None
            # Extracting data from the table with class name 'grouptable'
            # yield GroupTable ({
            #     'MittreName': column1_data.strip() if column1_data else None,
            #     'Url': column1_url_absolute,
            #     'GroupName': column2_data.strip() if column2_data else None,
            #     'AssociatedGroups': column3_data.strip() if column3_data else None,
            #     'Summary': column4_data.strip() if column4_data else None,
            #     })

#             # Follow the URL to the group's page and parse the table data
            if column1_url_absolute:
              yield response.follow(column1_url_absolute, self.parse_group_page)
    def parse_group_page(self, response):
        id_= response.xpath('//span[contains(text(), "ID:")]/following-sibling::text()').get().strip()
            # Extracting First Seen
        first_seen = response.xpath('//span[contains(text(), "First Seen:")]/following-sibling::text()').get()
        first_seen_text = response.xpath('//span[contains(text(), "First Seen:")]/following-sibling::text()').get()
        first_seen = first_seen_text.strip() if first_seen_text else ''
        # Extracting Last Seen
        last_seen_text = response.xpath('//span[contains(text(), "Last Seen:")]/following-sibling::text()').get()
        last_seen = last_seen_text.strip() if last_seen_text else ''
        contributors_text = response.xpath('//span[contains(text(), "Contributors:")]/following-sibling::text()').get()
        contributors = contributors_text.strip() if contributors_text else ''
        # Extracting Version
        version_text = response.xpath('//span[contains(text(), "Version")]/following-sibling::text()').get()
        version = version_text.strip() if version_text else ''
        # Extracting Created
        created_text = response.xpath('//span[contains(text(), "Created:")]/following-sibling::text()').get()
        created = created_text.strip() if created_text else ''
        # Extracting Last Modified
        last_modified_text = response.xpath('//span[contains(text(), "Last Modified:")]/following-sibling::text()').get()
        last_modified = last_modified_text.strip() if last_modified_text else ''
        # yield {
        #     'ID': id_,
        #     "Contributors":contributors,
        #     # 'First_Seen': first_seen,
        #      'Version': version,
        #      'Created': created,
        #     'Last Modified': last_modified
        # }
        techniqueTable = response.css('table.techniques-used tr')
        for row in techniqueTable:
            domain_data = row.css('td:nth-child(1)::text').get()
            id_data = row.css('td:nth-child(2) a::text').get()
            technique_url = row.css('td:nth-child(2) a::attr(href)').get()
            # references = []   

            if len(row.css('td')) >= 5:
                sub_id_data = row.css('td:nth-child(3) a::text').get()
                name_data = ' '.join(row.css('td:nth-child(4) *::text').getall()).strip()
                use_data = ' '.join(row.css('td:nth-child(5) *::text').getall()).strip()
                references_tag = 'td:nth-child(5) a'
            else:
                sub_id_data = None
                name_data = ' '.join(row.css('td:nth-child(3) *::text').getall()).strip()
                use_data = ' '.join(row.css('td:nth-child(4) *::text').getall()).strip()
                references_tag = 'td:nth-child(4) a'

            # Extract references only from the current row
            for link in row.css(references_tag):
                href = link.css('::attr(href)').get()
                text = link.css('::text').get()

                if text and text.strip().startswith('[') and text.strip().endswith(']'):
                        if not any(ref['link'] == href for ref in references):
                            ref = href
                            # references.append({"link": href, "body": ""})
                            if ref.endswith('.pdf'):
                                self.log(f"Queuing PDF download: {ref}")
                                yield Request(ref, callback=self.save_pdf)
                            elif ref.endswith('.html') or ref.endswith('.htm'):
                                self.log(f"Queuing HTML parsing: {ref}")
                                yield Request(ref, callback=self.parse_html_reference)
                                
                            else:
                                self.log(f"Unsupported file type: {ref}")  
            technique_url = response.urljoin(technique_url.strip()) if technique_url else None
            # references_string = ' '.join(references)
            # yield TechniquesTable( {
            #     'GroupId':id_.strip() if id_data else None,
            #     'Domain': domain_data.strip() if domain_data else None,
            #     'Name': name_data.strip() if name_data else None,
            #     'TID': id_data.strip() if id_data else None,
            #     'SubId': sub_id_data.strip() if sub_id_data else None,
            #     'Use': use_data if use_data else None,
            #     # "References": references
            # })
            if technique_url:
                yield response.follow(technique_url, self.parse_techniques)
        # # Software Table:
        softwareTable = response.css('table.table-alternate tr')
        for index, row in enumerate(softwareTable, start=1):
            # Extracting data from each column in the row
            id_data = ' '.join(row.css('td:nth-child(1) *::text').getall()).strip()
            name_data = ' '.join(row.css('td:nth-child(2) *::text').getall()).strip()
            # references_data = ' '.join(row.css('td:nth-child(3) *::text').getall()).strip()
            references_data = row.css('td:nth-child(3) span sup a::attr(href)').get()
            # Extracting techniques
            techniques_data = []
            techniques_nodes = row.css('td:nth-child(4) *::text').getall()
            for node in techniques_nodes:
                techniques_data.append(node.strip())
            # Check if ID starts with 'S'
            if id_data and id_data.startswith('S') and id_data[1:].isdigit():
                yield SoftwareTable({
                    'GroupId':id_.strip() if id_data else None,
                    'SID': id_data if id_data else None,
                    'Name': name_data if name_data else None,
                    'References': references_data if references_data else None,
                    'Techniques': ' '.join(techniques_data) if techniques_data else None,
                })
#         # campaigns   
        # if response.css('h2#campaigns'):
        #     for row in response.xpath('//*[@id="v-attckmatrix"]/div[2]/div/div/div/div[3]'):
        #         yield  CampaignsTable({
        #             'GroupId':id_.strip() if id_data else None,
        #             'ID': row.css('td:nth-child(1) a::text').get(),
        #             'Name': row.css('td:nth-child(2) a::text').get(),
        #             'FirstSeen': row.css('td:nth-child(3) *::text').get(),
        #             'LastSeen': row.css('td:nth-child(4) *::text').get(),
        #             # 'References': row.css('td:nth-child(5)  p sup a::attr(href)').get(),
        #              'Techniques': row.css('td:nth-child(6) a::attr(href)').getall(),
        #         })
# #         #associated groups (aliasDescription)
#         if response.css('h2#aliasDescription'):
#             for row in response.xpath('//*[@id="v-attckmatrix"]/div[2]/div/div/div/div[2]/table/tbody/tr'):
#                 name = row.xpath('./td[1]/text()').get()
#                 cleaned_name = re.sub(r'\W+', '', name) if name else name
#                 description = row.xpath('/html/body/div[1]/div[3]/div[2]/div/div[2]/div/div/div/div[2]/table/tbody/tr[1]/td[2]/p/span/sup/a/@href').get()
#                 yield {
#                     'Name': cleaned_name,
#                     'Description': description
#                 }
    # def parse_techniques(self, response):
        #  subtechniques
        # for row in response.xpath('//div[@id="subtechniques-card-body"]//table//tbody/tr'):
        #     yield SubTechniques( {
        #         'ID': row.xpath('td[1]/a/text()').get(),
        #         'Name': row.xpath('td[2]/a/text()').get(),
        #     })
        #     technique_url = response.urljoin(technique_url.strip()) if technique_url else None
        #     references_string = ' '.join(references)
        #     yield TechniquesTable( {
        #         'Domain': domain_data.strip() if domain_data else None,
        #         'Name': name_data.strip() if name_data else None,
        #         'STID': id_data.strip() if id_data else None,
        #         'SubId': sub_id_data.strip() if sub_id_data else None,
        #         'Use': use_data if use_data else None,
        #         "References": references_string
        #     })
            # if technique_url:
            #     yield response.follow(technique_url, self.parse_techniques)
        # Software Table:
        # softwareTable = response.css('table.table-alternate tr')
        # for index, row in enumerate(softwareTable, start=1):
        #     # Extracting data from each column in the row
        #     id_data = ' '.join(row.css('td:nth-child(1) *::text').getall()).strip()
        #     name_data = ' '.join(row.css('td:nth-child(2) *::text').getall()).strip()
        #     # references_data = ' '.join(row.css('td:nth-child(3) *::text').getall()).strip()
        #     references_data = row.css('td:nth-child(3) span sup a::attr(href)').get()
        #     # Extracting techniques
        #     techniques_data = []
        #     techniques_nodes = row.css('td:nth-child(4) *::text').getall()
        #     for node in techniques_nodes:
        #         techniques_data.append(node.strip())
            # Check if ID starts with 'S'
            # if id_data and id_data.startswith('S') and id_data[1:].isdigit():
                # yield SoftwareTable( {
                #     'SID': id_data if id_data else None,
                #     'Name': name_data if name_data else None,
                #     'References': references_data if references_data else None,
                #     'Techniques': ' '.join(techniques_data) if techniques_data else None,
                # } )
#         # campaigns 
        if response.css('h2#campaigns'):
            for row in response.xpath('//*[@id="v-attckmatrix"]/div[2]/div/div/div/div[3]'):
                yield  CampaignsTable({
                    'CID': row.css('td:nth-child(1) a::text').get(),
                    'Name': row.css('td:nth-child(2) a::text').get(),
                    'FirstSeen': row.css('td:nth-child(3) *::text').get(),
                    'LastSeen': row.css('td:nth-child(4) *::text').get(),
                    'References': row.css('td:nth-child(5)  p sup a::attr(href)').get(),
                     'Techniques': row.css('td:nth-child(6) a::attr(href)').getall(),
                })
#         #associated groups (aliasDescription)
        # if response.css('h2#aliasDescription'):
        #     for row in response.xpath('//*[@id="v-attckmatrix"]/div[2]/div/div/div/div[2]/table/tbody/tr'):
        #         name = row.xpath('./td[1]/text()').get()
        #         cleaned_name = re.sub(r'\W+', '', name) if name else name
        #         description = row.xpath('/html/body/div[1]/div[3]/div[2]/div/div[2]/div/div/div/div[2]/table/tbody/tr[1]/td[2]/p/span/sup/a/@href').get()
        #         yield {
        #             'Name': cleaned_name,
        #             'Description': description
        #         }
    def parse_techniques(self, response):
        id_= response.xpath('//span[contains(text(), "ID:")]/following-sibling::text()').get().strip()
        #  subtechniques
        # for row in response.xpath('//div[@id="subtechniques-card-body"]//table//tbody/tr'):
        #     yield SubTechniques( {
        #         'ID': row.xpath('td[1]/a/text()').get(),
        #         'Name': row.xpath('td[2]/a/text()').get(),
        #     })
            
# #         # procedure examples
        # if response.css('h2#examples'):
        #         rows = response.xpath('/html/body/div[1]/div[3]/div[2]/div/div[2]/div/div/div/div[2]/table')
        #         for row in rows:
        #                 # Extract the data from each cell in the row
        #                 id = row.css('td:nth-child(1) a::text').get()
        #                 name = row.css('td:nth-child(2) a::text').get()
        #                 description = row.css('td:nth-child(3) p::text').get()
# #         # procedure examples
        if response.css('h2#examples'):
                rows = response.xpath('/html/body/div[1]/div[3]/div[2]/div/div[2]/div/div/div/div[2]/table')

                for row in rows:
                        references = []   
                        # Extract references only from the current row
                        # Extract the data from each cell in the row
                        id = row.css('td:nth-child(1) a::text').get()
                        name = row.css('td:nth-child(2) a::text').get()
                        description = row.css('td:nth-child(3) p::text').get()
                        references_tag = 'td:nth-child(3) a'
                        for link in row.css(references_tag):
                            href = link.css('::attr(href)').get()
                            text = link.css('::text').get()  
                            if text and text.strip().startswith('[') and text.strip().endswith(']'):
                                if href not in references:
                                    references.append(href)
                        references_string = ' '.join(references)
                    #     yield ProcedureExamples( {
                    #         'TechniqueId':id_,
                    #         'PID': id,
                    #         'Name': name,
                    #         'Description': description,
                    #         "References": references_string
                    # })
# #         #mitigations
        # if response.css('h2#mitigations'):
        #     rows = response.xpath('//*[@id="v-attckmatrix"]/div[2]/div/div/div/div[3]/table')
        #     for row in rows: 
        #         id = row.css('td:nth-child(1) a::text').get()
        #         mitigation = row.css('td:nth-child(2) a::text').get()
        #         description = row.css('td:nth-child(3) p::text').get()
        #         mitigation_url = row.css('td:nth-child(2) a::attr(href)').get()
        #         technique_url=response.urljoin(technique_url.strip()) if technique_url else None
        #         if id.__contains__('M'):
        #                 yield ProcedureExamples( {
        #                     'ID': id,
        #                     'Name': name,
        #                     'Description': description
        #             })
# #         #mitigations
        if response.css('h2#mitigations'):
            rows = response.xpath('//*[@id="v-attckmatrix"]/div[2]/div/div/div/div[3]/table')
            for row in rows: 
                id = row.css('td:nth-child(1) a::text').get()
                references=[]
                mitigation = row.css('td:nth-child(2) a::text').get()
                description = row.css('td:nth-child(3) p::text').get()
                references_tag = 'td:nth-child(3) a'
                for link in row.css(references_tag):
                            href = link.css('::attr(href)').get()
                            text = link.css('::text').get()  
                            if text and text.strip().startswith('[') and text.strip().endswith(']'):
                                if href not in references:
                                    references.append(href)
                references_string = ' '.join(references)
                # mitigation_url = row.css('td:nth-child(2) a::attr(href)').get()
                # technique_url=response.urljoin(technique_url.strip()) if technique_url else None
                if id.__contains__('M'):        
                   yield Mitigations({
                    'MID': id,
                     'TechniqueId':id_,
                    'Mitigation': mitigation,
                    'Description': description,
                   "References": references_string
                })
# #         #detections 
        # if response.css('h2#detection'):
        #      rows = response.css('table.table.datasources-table.table-bordered tbody tr')
        #      for row in rows:
        #         # Extract the data from each cell in the row
        #         id = row.css('td:nth-child(1) a::text').get()
        #         data_source = row.css('td:nth-child(2) a::text').get()
        #         data_component = row.css('td:nth-child(3) a::text').get()
        #         detects = row.css('td:nth-child(4) p::text').get()
        #         # Yield the extracted   data
        #         # yield   {
        #         #     'ID': id,
        #         #     'DataSource': data_source,
        #         #     'DataComponent': data_component,
        #         #     'Detects': detects
        #         # }
        #         yield Mitigations({
        #             'ID': id,
        #             'Mitigation': mitigation,
        #             'Description': description
        #         })
# #         #detections
        if response.css('h2#detection'):
             rows = response.css('table.table.datasources-table.table-bordered tbody tr')
             for row in rows:
                # Extract the data from each cell in the row
                references=[]
                id = row.css('td:nth-child(1) a::text').get()
                data_source = row.css('td:nth-child(2) a::text').get()
                data_component = row.css('td:nth-child(3) a::text').get()
                detects = row.css('td:nth-child(4) p::text').get()
                references_tag = 'td:nth-child(4) a'
                for link in row.css(references_tag):
                            href = link.css('::attr(href)').get()
                            text = link.css('::text').get()  
                            if text and text.strip().startswith('[') and text.strip().endswith(']'):
                                if href not in references:
                                    references.append(href)
                references_string = ' '.join(references)

                # Yield the extracted   data
                # yield  Detections( {
                #     'DID': id,
                #     'TechniqueId':id_,
                #     'DataSource': data_source,
                #     'DataComponent': data_component,
                #     'Detects': detects,
                #     "References": references_string
                # }) 
                