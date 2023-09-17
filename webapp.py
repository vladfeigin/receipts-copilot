from flask import Flask, request, jsonify
import os, pathlib, time
from io import BytesIO
from PIL import Image, ImageDraw

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from dotenv import load_dotenv
import openai

import logging

#Flask application name
app = Flask(__name__)

logging.basicConfig(filename='applog.log', level=logging.INFO)
load_dotenv()

#computer vision configuration
COMPUTER_VISION_ENDPOINT = os.getenv("COMPUTER_VISION_ENDPOINT")
COMPUTER_VISION_KEY = os.getenv("COMPUTER_VISION_KEY")

#openai configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_DEPLOYMENT_ENDPOINT = os.getenv("OPENAI_DEPLOYMENT_ENDPOINT")
OPENAI_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
OPENAI_DEPLOYMENT_VERSION = os.getenv("OPENAI_DEPLOYMENT_VERSION")

# Configure OpenAI API
openai.api_type = "azure"
openai.api_version = OPENAI_DEPLOYMENT_VERSION
openai.api_base = OPENAI_DEPLOYMENT_ENDPOINT
openai.api_key = OPENAI_API_KEY

#init computer vision client
client = ComputerVisionClient(endpoint=COMPUTER_VISION_ENDPOINT, credentials=CognitiveServicesCredentials(COMPUTER_VISION_KEY))

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp'}

#systen prompt for openai
system_template = '''You are company financial department assistant. Your main task is to summarize the receipts.
The summary must contain all common information required for expense reimbursement.
More specifically is should contain the following information:
1. Date of the receipt
2. Vendor derails: name, address, phone number, all other information that can be useful
3. Transaction details: total amount, currency, payment method, last 4 digits of the card, date of the transaction, transaction ID, service description
If some of the information is missing, please indicate that it is missing.
Output result as python json object with the fields listed above.
'''
#run from command line: flask --app webapp run
#curl -X POST -F "image=@./images/IMG_0211.jpg" -v http://127.0.0.1:5000/submit-receipt
@app.route('/submit-receipt', methods=['POST'])
def upload_image():
    app.logger.info("submit-receipt has been called...==>")
    
    if 'image' not in request.files:
        return jsonify(error='No image file uploaded'), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify(error='No selected file'), 400

    if not file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        return jsonify(error='Invalid file type'), 400

    try:
        extracted_text = extract_text_from_image(file)
        print(extracted_text)
        summary = summarize_text(extracted_text)
        print(summary)
        #return jsonify(success='Image loaded successfully'), 200
        app.logger.info("submit-receipt has been finished....")
        return (summary), 200
    
    except Exception as e:
        return jsonify(error=str(e)), 400


def extract_text_from_image(file):
    app.logger.info("extract_text_from_image has been called....")
    file.stream.seek(0)  # Reset file pointer to the beginning
    # Call Azure OCR API
    result = client.recognize_printed_text_in_stream(file)  
    bag_of_words = [word.text for region in result.regions for line in region.lines for word in line.words]
    app.logger.info("extract_text_from_image has been finished....")
    return " ".join(bag_of_words)

...
                   
    
def summarize_text(text):
    app.logger.info("summarize_text has been called....")
    if text == "":
        return "No text to summarize."
    
    # prepare prompt
    messages = [{"role": "system", "content": f"{system_template}"},
            {"role": "user", "content": f"{text}"}]

    answer = openai.ChatCompletion.create(engine=OPENAI_DEPLOYMENT_NAME,

                                      messages=messages,)
    app.logger.info("summarize_text has been finished....")
    return    answer.choices[0].message.content
    
if __name__ == '__main__':
    app.run(debug=True)
