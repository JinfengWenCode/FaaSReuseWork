```javascript
module.exports.serviceBusQueueTrigger = async function (context, myQueueItem) {
    context.log('Service Bus queue trigger function processed message:', myQueueItem);
    // Add your processing logic here
};
```