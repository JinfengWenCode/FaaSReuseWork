import boto3
import json
import os

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    # Modify this ARN to the actual ARN of the doAlu function
    alu_function_arn = 'arn:aws:lambda:REGION:ACCOUNT_ID:function:doAlu'
    
    # Simulate parallel invocation of the doAlu function
    responses = []
    for _ in range(10):  # Example: invoke 10 parallel instances
        response = lambda_client.invoke(
            FunctionName=alu_function_arn,
            InvocationType='Event'  # Asynchronous invocation
        )
        responses.append(response)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Parallel invocations started'})
    }