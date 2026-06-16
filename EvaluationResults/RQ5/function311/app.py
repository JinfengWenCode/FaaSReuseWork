```python
from flask import Flask, jsonify, request
import boto3
import os
import uuid

app = Flask(__name__)

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE')
table = dynamodb.Table(table_name)

@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    item_id = str(uuid.uuid4())
    item = {
        'id': item_id,
        'data': data
    }
    table.put_item(Item=item)
    return jsonify(item), 201

@app.route('/items/<string:item_id>', methods=['GET'])
def get_item(item_id):
    response = table.get_item(Key={'id': item_id})
    item = response.get('Item')
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify(item)

@app.route('/items', methods=['GET'])
def list_items():
    response = table.scan()
    items = response.get('Items', [])
    return jsonify(items)

@app.route('/items/<string:item_id>', methods=['DELETE'])
def delete_item(item_id):
    table.delete_item(Key={'id': item_id})
    return jsonify({'message': 'Item deleted'})

if __name__ == '__main__':
    app.run(debug=True)