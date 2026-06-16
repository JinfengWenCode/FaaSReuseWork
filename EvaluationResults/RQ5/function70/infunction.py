import json
import threading

def alu_operation(start, end, result_list, index):
    result = 0
    for i in range(start, end):
        result += i * i
    result_list[index] = result

def lambda_handler(event, context):
    num_threads = 4
    range_per_thread = 1000000 // num_threads
    threads = []
    results = [0] * num_threads
    
    for i in range(num_threads):
        start = i * range_per_thread
        end = (i + 1) * range_per_thread
        thread = threading.Thread(target=alu_operation, args=(start, end, results, i))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    total_result = sum(results)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'result': total_result})
    }