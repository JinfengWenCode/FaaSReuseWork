import json
import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
BUCKET_NAME = 'your-s3-bucket-name'

def lambda_handler(event, context):
    asset_id = event['pathParameters']['asset_id']
    ttl = int(event['queryStringParameters'].get('ttl', 3600))
    
    # Generate presigned URL for download
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': BUCKET_NAME,
                                                            'Key': asset_id},
                                                    ExpiresIn=ttl)
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps('Error generating presigned URL')
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({'download_url': response})
    }