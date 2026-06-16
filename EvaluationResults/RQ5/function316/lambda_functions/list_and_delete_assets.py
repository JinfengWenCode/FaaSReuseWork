import json
import boto3

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
ASSETS_TABLE = 'Assets'
BUCKET_NAME = 'your-s3-bucket-name'

def lambda_handler(event, context):
    http_method = event['httpMethod']
    table = dynamodb.Table(ASSETS_TABLE)
    
    if http_method == 'GET':
        # List assets
        response = table.scan()
        return {
            'statusCode': 200,
            'body': json.dumps(response['Items'])
        }
    
    elif http_method == 'DELETE':
        asset_id = event['pathParameters']['asset_id']
        
        # Delete asset from DynamoDB
        table.delete_item(Key={'asset_id': asset_id})
        
        # Delete asset from S3
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=asset_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Asset deleted')
        }
    
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('Unsupported method')
        }