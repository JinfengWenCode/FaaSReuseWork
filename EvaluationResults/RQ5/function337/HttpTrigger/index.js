```javascript
module.exports = async function (context, req) {
    context.log('HTTP trigger function processed a request.');

    // Read name from query string or request body
    const name = (req.query.name || (req.body && req.body.name));

    if (name) {
        // If name is provided, return a greeting
        context.res = {
            // status: 200, /* Defaults to 200 */
            body: `Hello, ${name}!`
        };
    } else {
        // If name is not provided, return a bad request response
        context.res = {
            status: 400,
            body: "Please pass a name on the query string or in the request body"
        };
    }
};
```