```javascript
'use strict';

const AWS = require('aws-sdk');
const uuid = require('uuid');

const dynamoDb = new AWS.DynamoDB.DocumentClient();
const tableName = process.env.DYNAMODB_TABLE || 'MyCronJobTable';

module.exports.cronJobHandler = async (event) => {
  const timestamp = new Date().toISOString();
  const params = {
    TableName: tableName,
    Item: {
      id: uuid.v4(),
      createdAt: timestamp,
    },
  };

  try {
    await dynamoDb.put(params).promise();
    console.log(`Record inserted at ${timestamp}`);
  } catch (error) {
    console.error('Error inserting record:', error);
  }
};
```