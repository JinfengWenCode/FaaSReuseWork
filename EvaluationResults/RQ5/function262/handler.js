```javascript
const { ApolloServer, gql } = require('apollo-server-lambda');
const { getGreeting } = require('./dynamodb');

// Define the GraphQL schema
const typeDefs = gql`
  type Query {
    greeting(name: String!): String
  }
`;

// Define the resolvers
const resolvers = {
  Query: {
    greeting: async (_, { name }) => {
      const message = await getGreeting(name);
      return `Hello, ${name}! ${message}`;
    },
  },
};

// Create the Apollo Server
const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: true,
  playground: true,
});

// Export the handler
exports.graphqlHandler = server.createHandler();