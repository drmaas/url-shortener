from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_dynamodb as dynamodb,    
    Duration,
    RemovalPolicy,
)
from constructs import Construct

class UrlShortenerCdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
            
        # Create the DynamoDB table
        table = dynamodb.Table(
            self,
            "UrlShortenerTable",
            partition_key=dynamodb.Attribute(name="short_code", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST, # On-demand capacity
            removal_policy= RemovalPolicy.DESTROY, # Only for dev environments
            read_capacity=5,  # Set read capacity to 5 for free tier
            write_capacity=5, # Set write capacity to 5 for free tier
        )            
            
        # Define the Lambda function
        function = _lambda.Function(
            self,
            "UrlShortenerFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.handler",
            code=_lambda.Code.from_asset("./app"), # Path to your FastAPI code
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={  # Set environment variables here
                "TABLE_NAME": table.table_name,  # Access the table name
                "LOG_LEVEL": "INFO"
            },
        )
        
        # Grant Lambda read/write access to the DynamoDB table
        table.grant_read_write_data(function)
        
        # Create the IAM role for API Gateway
        api_gateway_role = iam.Role(
            self,
            "ApiGatewayLambdaRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
        )

        # Grant Lambda invoke permission to the API Gateway role
        function.grant_invoke(api_gateway_role)
            
        # Create the API Gateway REST API from the OpenAPI spec
        api = apigw.RestApi(
            self,
            "UrlShortenerApi",
            rest_api_name="UrlShortenerService",
            description="API for shortening URLs",
            deploy_options=apigw.StageOptions(stage_name="prod")
        )
        
        # Integrate all paths with the lambda function
        api.root.add_proxy(
            default_integration=apigw.LambdaIntegration(function, proxy=True, integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                    ),
                    apigw.IntegrationResponse(
                        selection_pattern="4\\d{2}", # Matches 4xx Errors
                        status_code="400",
                        response_parameters={
                            "method.response.header.Content-Type": "'application/json'",
                        },
                        response_templates={
                            "application/json": "$input.path('$.errorMessage')",
                        }
                    ),
                    apigw.IntegrationResponse(
                        selection_pattern="5\\d{2}", # Matches 5xx Errors
                        status_code="500",
                        response_parameters={
                            "method.response.header.Content-Type": "'application/json'",
                        },
                        response_templates={
                            "application/json": "$input.path('$.errorMessage')",
                        }
                    )
                ]),
            any_method=True, # Allow all HTTP methods
        )        
