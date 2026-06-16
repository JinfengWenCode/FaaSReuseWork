```javascript
export default {
  // Other Nuxt.js configurations
  buildModules: [
    // Other build modules
    '@nuxtjs/serverless',
  ],
  target: 'server', // Ensure the target is set to 'server' for SSR
  serverMiddleware: [
    // Add any server middleware if needed
  ],
}
```