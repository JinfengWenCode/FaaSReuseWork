import json
import boto3
import uuid
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

ASSETS_TABLE = 'Assets'
BUCKET_NAME = 'your-s3-bucket-name'

def lambda_handler(event, context):
    asset_id = str(uuid.uuid4())
    table = dynamodb.Table(ASSETS_TABLE)
    
    # Create asset entry in DynamoDB
    table.put_item(
        Item={
            'asset_id': asset_id,
            'status': 'CREATED'
        }
    )
    
    # Generate presigned URL for upload
    try:
        response = s3_client.generate_presigned_url('put_object',
                                                    Params={'Bucket': BUCKET_NAME,
                                                            'Key': asset_id},
                                                    ExpiresIn=3600)
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps('Error generating presigned URL')
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({'upload_url': response, 'asset_id': asset_id})
    }