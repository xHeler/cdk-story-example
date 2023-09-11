from aws_cdk import (
    Stack,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigateway
)
from constructs import Construct

class AwsCdkLambdaSqsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the Lambda function
        hello_lambda = _lambda.Function(
            self, 'HelloLambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler='index.handler',
            code=_lambda.Code.from_inline(
                """
                def handler(event, context):
                    return {
                        'statusCode': 200,
                        'body': '{"message": "Hello, World!"}'
                    }
                """
            )
        )

        # Define the API Gateway
        api = apigateway.RestApi(
            self, 'Endpoint',
            default_cors_preflight_options={
                'allow_origins': apigateway.Cors.ALL_ORIGINS,
                'allow_methods': apigateway.Cors.ALL_METHODS
            }
        )

        # Add the "/api/test" endpoint and link it to the Lambda function
        lambda_integration = apigateway.LambdaIntegration(hello_lambda)
        api_resource = api.root.add_resource('api').add_resource('test')
        api_resource.add_method('GET', lambda_integration)

        # Print the API endpoint URL
        CfnOutput(self, "EndpointURL",
                  value=api.url,
                  description="The URL of the API Gateway endpoint")
