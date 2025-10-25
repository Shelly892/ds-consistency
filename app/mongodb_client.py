from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import time
from datetime import datetime

class DistributedLabClient:
    def __init__(self):
        """Initialize the MongoDB replica set connection"""
        # Connection string - contains all 3 nodes
        self.connection_string = "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0"
        self.client = None
        self.db = None
        self.users_collection = None
        
    def connect(self):
        """Connect to the MongoDB replica set"""
        try:
            print("Connect to the MongoDB replica set...")
            self.client = MongoClient(self.connection_string)
            
            # Test connection
            self.client.admin.command('ping')
            print("Successfully connected to the replica set!")
            
            # Select the database and collection
            self.db = self.client['lab2_distributed_db']
            self.users_collection = self.db['user_profiles']
            
            # Show the replica set status
            self.show_replica_status()
            
        except ConnectionFailure as e:
            print(f"Connection failed: {e}")
            raise
    
    def show_replica_status(self):
        """Show the replica set status"""
        print("\nReplica set status:")
        try:
            status = self.client.admin.command("replSetGetStatus")
            for member in status['members']:
                state = member['stateStr']
                name = member['name']
                print(f"  - {name}: {state}")
        except Exception as e:
            print(f"  Failed to get status: {e}")
    
    def create_sample_data(self):
        """Create sample user data"""
        print("\nInserting sample user data...")
        
        # Define sample users
        sample_users = [
            {
                "user_id": 1001,
                "username": "alice_wang",
                "email": "alice@example.com",
                "last_login_time": datetime.now(),
                "profile": {
                    "age": 25,
                    "city": "Dublin"
                }
            },
            {
                "user_id": 1002,
                "username": "bob_chen",
                "email": "bob@example.com",
                "last_login_time": datetime.now(),
                "profile": {
                    "age": 30,
                    "city": "Beijing"
                }
            },
            {
                "user_id": 1003,
                "username": "carol_li",
                "email": "carol@example.com",
                "last_login_time": datetime.now(),
                "profile": {
                    "age": 28,
                    "city": "Shanghai"
                }
            }
        ]
        
        # Clear existing data (for testing)
        self.users_collection.delete_many({})
        
        # Insert data
        result = self.users_collection.insert_many(sample_users)
        print(f"Successfully inserted {len(result.inserted_ids)} users")
        
        # Show the inserted data
        print("\nCurrent user list:")
        for user in self.users_collection.find():
            print(f"  - {user['username']} (ID: {user['user_id']}) - {user['email']}")
    
    def read_user(self, user_id):
        """Read a single user"""
        user = self.users_collection.find_one({"user_id": user_id})
        if user:
            print(f"\nRead user: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Last login: {user['last_login_time']}")
        else:
            print(f"\nUser ID not found: {user_id}")
        return user
    
    def close(self):
        """Close the connection"""
        if self.client:
            self.client.close()
            print("\nDisconnected")


def main():
    # Create client
    client = DistributedLabClient()
    
    try:
        # Connect
        client.connect()
        
        # Create sample data
        client.create_sample_data()
        
        # Read a user
        client.read_user(1001)
        
        print("\nPart A completed!")
        
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()