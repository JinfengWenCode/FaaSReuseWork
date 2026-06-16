```python
import json

def lambda_handler(event, context):
    # Parse the GitHub event
    try:
        body = json.loads(event['body'])
        pull_request = body.get('pull_request', {})
        pr_body = pull_request.get('body', '')
    except (KeyError, json.JSONDecodeError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid GitHub event data'})
        }
    
    # Check if the pull request body starts with the required Trello card link
    if pr_body.startswith("Related trello card: https://trello.com/"):
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Check passed'})
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Check failed: Pull request body must start with "Related trello card: https://trello.com/"'})
        }
```