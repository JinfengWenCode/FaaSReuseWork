```javascript
const AWS = require('aws-sdk');
const docClient = new AWS.DynamoDB.DocumentClient();

const getGreeting = async (name) => {
  const params = {
    TableName: process.env.DYNAMODB_TABLE,
    Key: {
      id: name,
    },
  };

  try {
    const data = await docClient.get(params).promise();
    return data.Item ? data.Item.message : 'Welcome!';
  } catch (error) {
    console.error('Error fetching greeting:', error);
    throw new Error('Could not fetch greeting');
  }
};

module.exports = {
  getGreeting,
};