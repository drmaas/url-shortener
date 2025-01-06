import fastapi
import random
import string
import boto3
from typing import Optional, Dict, Protocol
from pydantic import BaseModel, HttpUrl
import datetime
    
app = fastapi.FastAPI()

class DynamoDBRepositoryInterface(Protocol):
    def put_item(self, item: Dict): ...
    def get_item(self, key: Dict) -> Optional[Dict]: ...
    def update_item(self, key: Dict, update_expression: str, expression_attribute_values: Dict): ...

class DynamoDBRepository:
    def __init__(self, table_name: str, dynamodb_client=None):
        self.table_name = table_name
        self.dynamodb = dynamodb_client or boto3.client("dynamodb")

    def put_item(self, item: Dict):
        item = {
            "short_code": { "S": item["shortCode"] },
            "long_url": { "S": item["longUrl"] },
            "created_at": { "S": item["createdAt"] },
            "clicks": { "N": item["clicks"] },
            "custom": { "BOOL": item["custom"] },
        }
        self.dynamodb.put_item(TableName=self.table_name, Item=item)

    def get_item(self, key: str) -> Optional[Dict]:
        response = self.dynamodb.get_item(TableName=self.table_name, Key={"short_code": { "S": key}})
        item = response.get("Item")
        return {
            "shortCode": item["short_code"]["S"],
            "longUrl": item["long_url"]["S"],
            "createdAt": item["created_at"]["S"],
            "clicks": item["clicks"]["N"],
            "custom": item["custom"]["BOOL"],
        } if item else None

    def update_item(self, key: Dict, update_expression: str, expression_attribute_values: Dict):
        updated_key = {"short_code": { "S": key["shortCode"] }}
        self.dynamodb.update_item(
            TableName=self.table_name,
            Key=updated_key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )

def create_app(dynamodb_repository: DynamoDBRepositoryInterface): # Takes repository directly
    app.dynamodb_repository = dynamodb_repository
    return app

def generate_short_code(length: int = 8) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))

class ShortenRequest(BaseModel):
    longUrl: HttpUrl

class ShortenResponse(BaseModel):
    shortUrl: str

class OriginalUrlResponse(BaseModel):
    longUrl: HttpUrl

class ClickStatsResponse(BaseModel):
    clicks: int
    lastClicked: Optional[str] = None

@app.post("/url", response_model=ShortenResponse)
async def shorten_url(request: ShortenRequest):
    long_url = str(request.longUrl)

    short_code = generate_short_code()
    while app.dynamodb_repository.get_item(short_code):
        short_code = generate_short_code()

    item = {
        "shortCode": short_code,
        "longUrl": long_url,
        "createdAt": datetime.datetime.now().isoformat(),
        "clicks": "0",
        "custom": False,
    }
    app.dynamodb_repository.put_item(item)

    return {"shortUrl": f"http://testserver/{short_code}"} # Use testserver

@app.get("/{short_code}", response_class=fastapi.responses.RedirectResponse)
async def redirect_url(short_code: str):
    item = app.dynamodb_repository.get_item(short_code)
    if not item:
        raise fastapi.HTTPException(status_code=404, detail="Short code not found")

    long_url = item["longUrl"]
    app.dynamodb_repository.update_item({"shortCode": short_code}, "SET clicks = clicks + :val", {":val": 1})

    return long_url

@app.get("/url/{short_code}", response_model=OriginalUrlResponse)
async def get_original_url(short_code: str):
    item = app.dynamodb_repository.get_item(short_code)
    if not item:
        raise fastapi.HTTPException(status_code=404, detail="Short code not found")
    return {"longUrl": item["longUrl"]}

@app.get("/stats/{short_code}", response_model=ClickStatsResponse)
async def get_click_stats(short_code: str):
    item = app.dynamodb_repository.get_item(short_code)
    if not item:
        raise fastapi.HTTPException(status_code=404, detail="Short code not found")
    clicks = item["clicks"]
    return {"clicks": clicks, "lastClicked": None}  # last clicked is a placeholder
