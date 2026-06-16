```python
import boto3
import json

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    # Replace 'your-bucket-name' and 'your-key' with actual bucket name and key
    response = s3.get_object(Bucket='your-bucket-name', Key='your-key')
    n = int(response['Body'].read().decode('utf-8'))
    
    # Trigger the next function in the chain
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName='aluFunction',  # Replace with the actual function name
        InvocationType='Event',
        Payload=json.dumps({'n': n})
    )
    
    return {
        'statusCode': 200,
        'body': 'Configuration loaded and next function triggered'
    }
```