import mangum # lambda adapter
from url_shortener import create_app, DynamoDBRepository
import os
from botocore.config import Config
import boto3

TABLE_NAME = os.environ.get("TABLE_NAME")

config = Config(
   connect_timeout = 1.0,
   read_timeout = 1.0
)

dynamodb = boto3.client("dynamodb", config=config)
handler = mangum.Mangum(
    create_app(dynamodb_repository=DynamoDBRepository(TABLE_NAME, dynamodb_client=dynamodb))
)