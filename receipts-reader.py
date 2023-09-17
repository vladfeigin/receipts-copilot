import os, pathlib, time
from io import BytesIO
from PIL import Image, ImageDraw

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from dotenv import load_dotenv
import openai



load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
OPENAI_DEPLOYMENT_ENDPOINT = os.getenv("OPENAI_DEPLOYMENT_ENDPOINT")
OPENAI_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
OPENAI_DEPLOYMENT_VERSION = os.getenv("OPENAI_DEPLOYMENT_VERSION")

COMPUTER_VISION_ENDPOINT = os.getenv("COMPUTER_VISION_ENDPOINT")
COMPUTER_VISION_KEY = os.getenv("COMPUTER_VISION_KEY")

key = COMPUTER_VISION_KEY
endpoint = COMPUTER_VISION_ENDPOINT

client = ComputerVisionClient(endpoint=endpoint, credentials=CognitiveServicesCredentials(key))




images_list = []
cropped_images_paths = []
cropped_images_list = []
working_directory = pathlib.Path ("./")
os.makedirs(os.path.join ("./", 'cropped_images'), exist_ok=True)

# Create an Image object from each image in a the Images folder.
for image_path in working_directory.glob('images/*.jpg'):  # assume all images are jpg
    imageObject = Image.open(image_path)
    images_list.append(imageObject)
    cropped_images_paths.append(pathlib.Path (str(image_path).replace('images', 'cropped_images')))

# Crop each image in your list at the same place
for image in images_list:
    # Don't exceed your image height and width
    w, h = image.size
    print('Image width & height:', w, h)

    cropped = image.crop((150,100,1500,1500)) # edges: left, top, right, bottom
    cropped_images_list.append(cropped)
    
    
for i in range(len(cropped_images_list)):
    # Convert cropped images back to PIL.JpegImagePlugin.JpegImageFile type
    b = BytesIO()
    cropped_images_list[i].save(b, format="jpeg")
    cropped_images_list[i] = Image.open(b)
    # Save cropped image to file.
    cropped_images_list[i].save(cropped_images_paths[i], format="jpeg")    
    b.close()


for cropped_image_path in cropped_images_paths:
    cropped_bytes = open(cropped_image_path, "rb")
    # Call API
    result = client.recognize_printed_text_in_stream(cropped_bytes)   
    
    print(f"result={result}\n")
    
    for region in result.regions:
            for line in region.lines:
                for word in line.words:
                    #print("Extracted text:")
                    print(word.text)
                    #print()
                    #print('Bounding box for each word:')
                    #print(word.bounding_box)
    print()    