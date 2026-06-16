import json

def lambda_handler(event, context):
    # Log the received event
    print("Received event: " + json.dumps(event, indent=2))
    
    # Extract the SNS message
    for record in event['Records']:
        sns_message = record['Sns']['Message']
        print("SNS Message: " + sns_message)
    
    # Return a success message
    return {
        'statusCode': 200,
        'body': json.dumps('SNS event processed successfully!')
    }