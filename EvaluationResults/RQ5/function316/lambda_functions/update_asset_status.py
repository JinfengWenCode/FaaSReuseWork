import json
import boto3

dynamodb = boto3.resource('dynamodb')
ASSETS_TABLE = 'Assets'

def lambda_handler(event, context):
    asset_id = event['pathParameters']['asset_id']
    table = dynamodb.Table(ASSETS_TABLE)
    
    # Update asset status to UPLOADED
    table.update_item(
        Key={'asset_id': asset_id},
        UpdateExpression='SET #status = :status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':status': 'UPLOADED'}
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Asset marked as UPLOADED')
    }