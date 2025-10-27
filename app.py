from flask import Flask, render_template, request
import boto3
import datetime
import os
from dotenv import load_dotenv

# --- Load environment variables from .env file ---
load_dotenv()


print("AWS Region:", os.getenv("REGION"))

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
REGION = os.getenv("REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")
TABLE_NAME = os.getenv("TABLE_NAME")

app = Flask(__name__)

# --- AWS Clients ---
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION or "ap-south-1"

)

textract = boto3.client(
    'textract',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION or "ap-south-1"

)

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION or "ap-south-1"

)

table = dynamodb.Table(TABLE_NAME)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']

    if file.filename == '':
        return 'No file selected!'

    # Upload to S3
    s3.upload_fileobj(file, BUCKET_NAME, file.filename)

    # Textract
    response = textract.detect_document_text(
        Document={'S3Object': {'Bucket': BUCKET_NAME, 'Name': file.filename}}
    )

    # Extract text
    extracted_text = ''
    for item in response['Blocks']:
        if item['BlockType'] == 'LINE':
            extracted_text += item['Text'] + '\n'

    # Store in DynamoDB
    table.put_item(
        Item={
            'FileName': file.filename,
            'ExtractedText': extracted_text,
            'UploadedAt': str(datetime.datetime.now())
        }
    )

    return render_template('index.html', extracted_text=extracted_text)


if __name__ == '__main__':
    app.run(debug=True)
