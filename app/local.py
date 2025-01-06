from url_shortener import create_app, DynamoDBRepository
import os
import boto3
from botocore.config import Config

TABLE_NAME = os.environ.get("TABLE_NAME")

config = Config(
   connect_timeout = 1.0,
   read_timeout = 1.0
)

dynamodb = boto3.client("dynamodb", config=config, endpoint_url="http://localhost:8000")
response = dynamodb.describe_table(
    TableName=TABLE_NAME
)
if not response.get("Table"):
    dynamodb.create_table(
        KeySchema=[
            {
                'AttributeName': 'short_code',
                'KeyType': 'HASH'
            },
        ],   
        AttributeDefinitions=[
            {
                'AttributeName': 'short_code',
                'AttributeType': 'S'
            }          
        ],
        TableName=TABLE_NAME,
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5,
        }
        )
app = create_app(dynamodb_repository=DynamoDBRepository(TABLE_NAME, dynamodb_client=dynamodb))




