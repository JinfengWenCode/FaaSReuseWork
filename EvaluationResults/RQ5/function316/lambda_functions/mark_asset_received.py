import json
import boto3

dynamodb = boto3.resource('dynamodb')
ASSETS_TABLE = 'Assets'

def lambda_handler(event, context):
    table = dynamodb.Table(ASSETS_TABLE)
    
    for record in event['Records']:
        asset_id = record['s3']['object']['key']
        
        # Update asset status to RECEIVED
        table.update_item(
            Key={'asset_id': asset_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'RECEIVED'}
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Asset marked as RECEIVED')
    }