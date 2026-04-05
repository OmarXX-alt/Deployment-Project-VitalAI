import os
from pymongo import MongoClient

class DatabaseConnection:
    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app):
        """
        Initialize the MongoDB connection using the Flask app configuration.
        """
        # Get MongoDB URI from environment variable or use default local connection
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/vital_ai")
        app.config.setdefault("MONGO_URI", mongo_uri)
        
        # Initialize the MongoClient. The client maintains a connection pool internally.
        self.client = MongoClient(app.config["MONGO_URI"])
        
        # Get the default database (extracted from URI) or fallback to 'vital_ai'
        self.db = self.client.get_default_database(default='vital_ai')

        # Test the connection to ensure it's successful
        try:
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

        # Attach the database to the app context if needed
        app.db = self.db

# Global instance to be imported and used across your application
db = DatabaseConnection()

def get_db():
    """
    Utility function to get the current database instance.
    """
    return db.db
