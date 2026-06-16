```python
import boto3
import threading

def load_configuration():
    s3 = boto3.client('s3')
    # Replace 'your-bucket-name' and 'your-key' with actual bucket name and key
    response = s3.get_object(Bucket='your-bucket-name', Key='your-key')
    n = int(response['Body'].read().decode('utf-8'))
    return n

def compute_phase(n):
    def arithmetic_task():
        result = 0
        for _ in range(n):
            result += 1  # Simulate some arithmetic operation

    threads = []
    for _ in range(100):
        thread = threading.Thread(target=arithmetic_task)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

def lambda_handler(event, context):
    n = load_configuration()
    compute_phase(n)
    return {
        'statusCode': 200,
        'body': 'Computation completed successfully'
    }
```