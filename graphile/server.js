const express = require('express');
const { postgraphile } = require('postgraphile');

const app = express();

app.use(
  postgraphile(
    process.env.DATABASE_URL || 'postgres://postgres:postgres@db:5432/postgres',
    'public', // schema
    {
      jwtSecret: "geheim",
      jwtPgTypeIdentifier: "public.jwt_token",
      dynamicJson: true,
      defaultRole: "user_role",
      showErrorStack: true,
      enhanceGraphiql: true,
      allowExplain: true,
      watchPg: true,
      graphiql: true,
      enableQueryBatching: true,
      subscriptions: true,
      classicIds: true,
      live: true,
      extendedErrors: [
        'severity',
        'code',
        'detail',
        'hint',
        'position',
        'internalPosition',
        'internalQuery',
        'where',
        'schema',
        'table',
        'column',
        'dataType',
        'constraint',
        'file',
        'line',
        'routine',
      ],
      exportGqlSchemaPath: '/tmp/schema/schema.graphql'
    }
  )
);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
