```javascript
const { Nuxt } = require('nuxt-start');

let nuxtConfig = require('../nuxt.config.js');
nuxtConfig.dev = false; // Ensure the dev mode is disabled

const nuxt = new Nuxt(nuxtConfig);

exports.handler = async (event, context) => {
  const { path, httpMethod, headers, queryStringParameters, body } = event;

  const result = await nuxt.renderRoute(path, {
    req: {
      method: httpMethod,
      headers,
      url: path,
      query: queryStringParameters,
      body,
    },
    res: {
      setHeader: () => {},
      end: () => {},
    },
  });

  return {
    statusCode: result.html ? 200 : 404,
    headers: {
      'Content-Type': 'text/html',
    },
    body: result.html || 'Not Found',
  };
};
```