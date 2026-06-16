```typescript
import express from 'express';

const app = express();
const port = process.env.PORT || 8080;

app.get('/', (req, res) => {
  res.send('Hello, World from Google Cloud Run!');
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
```