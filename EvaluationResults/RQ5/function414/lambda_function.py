```python
import json
import boto3
from urllib.parse import unquote_plus

s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')

def lambda_handler(event, context):
    # Log the received event
    print("Received event: " + json.dumps(event, indent=2))
    
    # Iterate over each record in the event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        
        # Check if the file is a png or jpg
        if key.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                # Call Rekognition to detect labels
                response = rekognition_client.detect_labels(
                    Image={
                        'S3Object': {
                            'Bucket': bucket,
                            'Name': key
                        }
                    },
                    MaxLabels=10
                )
                
                # Extract labels
                labels = [label['Name'] for label in response['Labels']]
                print(f"Detected labels for {key}: {labels}")
                
                # Convert labels to S3 tags
                tags = [{'Key': f'Label{i+1}', 'Value': label} for i, label in enumerate(labels)]
                
                # Add tags to the S3 object
                s3_client.put_object_tagging(
                    Bucket=bucket,
                    Key=key,
                    Tagging={
                        'TagSet': tags
                    }
                )
                print(f"Tags added to {key}: {tags}")
                
            except Exception as e:
                print(f"Error processing object {key} from bucket {bucket}. Error: {str(e)}")
        else:
            print(f"Skipped non-image file: {key}")

    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete.')
    }
```