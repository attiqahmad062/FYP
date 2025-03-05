from flask import Blueprint, render_template, request, jsonify
from ner.scrapy_runner import run_scrapy_spider  # Example of importing your scrapy runner

# Define a Blueprint for the NER functionality
ner_bp = Blueprint('ner', __name__)

# Define a route to interact with NER functionality

@ner_bp.route('/run_ner', methods=['POST'])
def run_ner():
    # Process incoming request, e.g., run a scrapy crawl or NER task
    result = run_scrapy_crawler()  # This is an example; you'll adjust it to fit your actual logic
    return jsonify({"result": result})

# You can define more routes if needed
