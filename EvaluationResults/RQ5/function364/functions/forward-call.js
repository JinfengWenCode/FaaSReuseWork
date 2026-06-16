```javascript
exports.handler = function(context, event, callback) {
    // Create a new TwiML response
    const twiml = new Twilio.twiml.VoiceResponse();

    // Forward the call to another phone number
    const forwardToNumber = '+1234567890'; // Replace with the number you want to forward the call to
    twiml.dial(forwardToNumber);

    // Return the TwiML response
    callback(null, twiml);
};
```