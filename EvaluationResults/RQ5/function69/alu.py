```python
import threading

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
    n = event['n']
    compute_phase(n)
    return {
        'statusCode': 200,
        'body': 'Computation completed successfully'
    }
```