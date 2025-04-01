// This script will be executed when the MongoDB container is first initialized

db = db.getSiblingDB('admin');

// Create the application user with appropriate permissions
db.createUser({
  user: process.env.MONGO_INITDB_ROOT_USERNAME,
  pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
  roles: [
    { role: 'root', db: 'admin' }
  ]
});

db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE);

// Create the application database and collections
db.createCollection('users');
db.createCollection('messages');

print('MongoDB initialization completed successfully'); 