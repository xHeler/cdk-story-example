import json
import boto3
import uuid
import os

dynamodb = boto3.resource('dynamodb')
sqs_client = boto3.client('sqs')

TABLE_NAME = os.environ.get('TABLE_NAME')
QUEUE_URL = os.environ.get('QUEUE_URL')
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    # Input validation can be added here
    story_id = str(uuid.uuid4())

    # Insert into DynamoDB
    table.put_item(
        Item={
            'id': story_id,
            'isVoiceGenerated': False,
            'isTextGenerated': False,
            'isImagesGenerated': False
        }
    )

    # Send message to SQS
    sqs_client.send_message(QueueUrl=QUEUE_URL, MessageBody=story_id)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'id': story_id})
    }
