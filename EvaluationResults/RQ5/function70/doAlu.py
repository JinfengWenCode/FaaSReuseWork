import json

def lambda_handler(event, context):
    # Simulate a CPU-intensive ALU operation
    result = 0
    for i in range(1000000):
        result += i * i
    
    return {
        'statusCode': 200,
        'body': json.dumps({'result': result})
    }