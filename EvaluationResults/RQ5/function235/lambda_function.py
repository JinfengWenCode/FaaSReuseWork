```python
import boto3
import os
import subprocess
from urllib.parse import unquote_plus

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Extract bucket name and object key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']['object']['key'])
    
    # Define local paths
    download_path = f'/tmp/{os.path.basename(key)}'
    gif_path = f'/tmp/{os.path.splitext(os.path.basename(key))[0]}.gif'
    
    # Download the video file from S3
    s3_client.download_file(bucket, key, download_path)
    
    # Convert the video to GIF using FFmpeg
    ffmpeg_command = [
        '/opt/bin/ffmpeg',  # Path to FFmpeg in the Lambda layer
        '-i', download_path,
        '-vf', 'fps=10,scale=320:-1:flags=lanczos',
        '-c:v', 'gif',
        gif_path
    ]
    
    subprocess.run(ffmpeg_command, check=True)
    
    # Upload the GIF back to S3
    gif_key = f'converted/{os.path.splitext(key)[0]}.gif'
    s3_client.upload_file(gif_path, bucket, gif_key)
    
    return {
        'statusCode': 200,
        'body': f'Successfully converted {key} to GIF and uploaded to {gif_key}'
    }
```