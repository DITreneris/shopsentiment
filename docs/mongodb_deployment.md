# MongoDB Atlas Deployment Guide

This guide provides step-by-step instructions for deploying the ShopSentiment application with MongoDB Atlas, a fully managed cloud database service.

## Prerequisites

- Account on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- ShopSentiment application code
- Python 3.8+ installed locally
- Git installed locally
- Basic knowledge of command-line operations

## Setting Up MongoDB Atlas

### 1. Create a MongoDB Atlas Account

If you don't already have one, sign up for a MongoDB Atlas account at [https://www.mongodb.com/cloud/atlas/register](https://www.mongodb.com/cloud/atlas/register).

### 2. Create a New Cluster

1. Log in to your MongoDB Atlas account
2. Click "Build a Database"
3. Select your preferred plan:
   - For development or low-traffic applications, the "Shared" (Free) option is sufficient
   - For production, consider a "Dedicated" cluster
4. Choose your preferred cloud provider and region (select a region close to your target users)
5. Name your cluster (e.g., "shopsentiment-cluster")
6. Click "Create Cluster"

### 3. Set Up Database Security

#### Create a Database User

1. In the left menu, click "Database Access" under "Security"
2. Click "Add New Database User"
3. Enter a username and strong password
4. Set user privileges:
   - For simplicity, you can select "Atlas Admin" role
   - For better security, create a user with read and write access only to the specific database
5. Click "Add User"

#### Configure Network Access

1. In the left menu, click "Network Access" under "Security"
2. Click "Add IP Address"
3. For development, you can allow access from anywhere by clicking "Allow Access from Anywhere"
4. For production, add only specific IP addresses from which your application will connect
5. Click "Confirm"

### 4. Get Connection String

1. In the clusters view, click "Connect"
2. Select "Connect your application"
3. Choose your driver (Python) and version
4. Copy the connection string (it will look like `mongodb+srv://username:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`)
5. Replace `<password>` with your database user's password

## Configuring the ShopSentiment Application

### 1. Update Environment Variables

Edit your `.env` file to include the MongoDB connection details:

```
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=shopsentiment
```

Replace the `MONGODB_URI` with your actual connection string.

### 2. Install MongoDB Dependencies

Ensure all required MongoDB dependencies are installed:

```bash
pip install pymongo dnspython flask-pymongo
```

These packages should already be listed in your `requirements.txt` file.

## Data Migration

If you're migrating from SQLite to MongoDB, use the provided migration script:

```bash
python scripts/migrate_to_mongodb.py --sqlite-path=data/shopsentiment.db --mongo-uri=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

This script will:
1. Connect to your SQLite database
2. Export data from SQLite tables
3. Transform the data into MongoDB document format
4. Import the data into MongoDB collections

## Testing the MongoDB Connection

Run the integration test to verify your MongoDB connection:

```bash
python -m tests.test_mongodb_integration
```

This test will create test data in your MongoDB database and verify that all operations work correctly.

## Production Deployment Considerations

### 1. Connection Pooling

MongoDB Atlas automatically manages connection pooling. The PyMongo driver will handle connections efficiently by default.

### 2. Indexing Strategy

The application automatically creates indexes on frequently queried fields. If you identify performance issues or have specific query patterns, consider adding custom indexes.

### 3. Monitoring

MongoDB Atlas provides monitoring tools:
1. In your Atlas dashboard, click on the "Metrics" tab for your cluster
2. Set up alerts for critical metrics
3. Consider setting up additional application-level monitoring

### 4. Backup Strategy

MongoDB Atlas provides automated backups:
1. Go to the "Backup" section in the left menu
2. Configure backup schedule and retention policy
3. For the free tier, point-in-time recovery isn't available, so consider implementing application-level backups for critical data

## Troubleshooting

### Connection Issues

1. Verify the connection string is correct
2. Check that the IP address is whitelisted in Network Access
3. Ensure the database user credentials are correct
4. Check for network issues or firewalls blocking connections

### Performance Issues

1. Check the MongoDB Atlas monitoring dashboard for resource utilization
2. Review query patterns and ensure appropriate indexes exist
3. Consider upgrading your cluster tier if consistently hitting resource limits

## Additional Resources

- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB University](https://university.mongodb.com/) - Free courses on MongoDB

## Migration Rollback Plan

If you need to roll back from MongoDB to SQLite:

1. Ensure your SQLite database backup is available
2. Update your `.env` file to remove the MongoDB configuration
3. Restart your application to use SQLite
4. If needed, restore your SQLite database from backup 