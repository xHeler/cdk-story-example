import json
import boto3
import os
import requests

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_API_ENDPOINT = 'https://api.openai.com/v1/engines/davinci/completions'

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME')
table = dynamodb.Table(TABLE_NAME)


def generate_text_from_openai(prompt):
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        'prompt': prompt,
        'max_tokens': 2000
    }

    response = requests.post(OPENAI_API_ENDPOINT, headers=headers, json=data)
    return response.json()['choices'][0]['text']


def handler(event, context):
    for record in event['Records']:
        story_id = record['body']

        content = generate_text_from_openai(
            "Write a fairy tale. The style of the fable is scify. The fable should consist of 3 chapters, and each chapter is to have 200-250 words of description so that illustrations can be easily created. The writing form is to be in JSON form, and each chapter will contain an image named IMAGE_(chapter number) added later. Please start the story with the first chapter.")

        table.update_item(
            Key={'id': story_id},
            UpdateExpression="set isTextGenerated=:t, content=:c",
            ExpressionAttributeValues={':t': True, ':c': content},
            ReturnValues="UPDATED_NEW"
        )

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'success'})
    }
