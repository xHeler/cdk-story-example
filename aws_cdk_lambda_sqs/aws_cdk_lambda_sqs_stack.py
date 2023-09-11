from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_dynamodb as ddb,
    aws_apigateway as apigw,
    aws_sqs as sqs,
    aws_lambda_event_sources as lambda_event_sources
)
from constructs import Construct
import os
from dotenv import load_dotenv


class AwsCdkLambdaSqsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        load_dotenv()

        # Define DynamoDB table
        story_table = ddb.Table(
            self, 'StoryTable',
            partition_key=ddb.Attribute(
                name='id', type=ddb.AttributeType.STRING),
            attributes=[
                ddb.Attribute(name='content', type=ddb.AttributeType.STRING)
            ],
            removal_policy=RemovalPolicy.DESTROY  # Remove table when stack is deleted
        )

        # Define SQS Queue
        story_queue = sqs.Queue(
            self, "StoryQueue"
        )

        # Define the GenerateStory Lambda
        generate_story_lambda = _lambda.Function(
            self, 'GenerateStoryFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='handler.handler',
            code=_lambda.Code.from_asset('lambdas/generate_story'),
            environment={
                "TABLE_NAME": story_table.table_name,
                "QUEUE_URL": story_queue.queue_url,
            }
        )

        # Grant the necessary permissions
        story_table.grant_write_data(generate_story_lambda)
        story_queue.grant_send_messages(generate_story_lambda)

        # Define API Gateway with a Lambda proxy integration for GenerateStory Lambda
        api = apigw.RestApi(self, "storiesApi",
                            description="API for generating stories.")
        generate_story = api.root.add_resource(
            'api').add_resource('stories').add_resource('generate')
        generate_story.add_method(
            'GET', apigw.LambdaIntegration(generate_story_lambda))

        # Define the TextGeneration Lambda
        text_generation_lambda = _lambda.Function(
            self, 'TextGenerationFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='handler.handler',
            code=_lambda.Code.from_asset('lambdas/text_generation'),
            environment={
                "TABLE_NAME": story_table.table_name,
                "OPENAI_API_KEY": os.getenv('API_KEY')
            }
        )

        # Define the Status Stories lambda
        status_lambda = _lambda.Function(
            self, 'StatusLambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler='handler.handler',
            code=_lambda.Code.from_asset('lambdas/status'),
            environment={
                'STORY_TABLE_NAME': story_table.table_name
            }
        )

        # Define API Gateway for Status Stories lambda
        status_resource = api.root.add_resource(
            "stories").add_resource("{id}").add_resource("status")
        status_integration = apigw.LambdaIntegration(status_lambda)
        status_resource.add_method("GET", status_integration)

        # Grant the necessary permissions
        story_table.grant_write_data(text_generation_lambda)
        story_table.grant_read_data(status_lambda)

        # Use SQS as an event source for TextGeneration Lambda
        text_generation_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(story_queue))
