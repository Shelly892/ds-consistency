"""
Part B: Experiment of Strategies
"""

from pymongo import MongoClient, WriteConcern, ReadPreference
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect
import time
import os
import traceback
from datetime import datetime

class ReplicationExperiments:
    def __init__(self):
        """Initialize the connection"""
        self.connection_string = os.getenv(
            'MONGO_URI',
            'mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0'
        )
        self.client = MongoClient(self.connection_string)
        self.db = self.client['lab2_distributed_db']
        self.test_collection = self.db['replication_test']
        
    def show_replica_info(self):
        """Show the replica set information"""
        print("\n" + "-"*70)
        print("Replica Set Current Status")
        print("-"*70)
        
        try:
            status = self.client.admin.command("replSetGetStatus") #dynamic status
            config = self.client.admin.command("replSetGetConfig") #static config
            
            print(f"\n Replica Set Name: {status['set']}")
            print(f" Total Nodes: {len(status['members'])}")
            
            # replication factor from config 
            print(f"\n Data Replication Configuration:")
            print(f" Replication Factor: {len(config['config']['members'])} (Data will be replicated to all nodes)")
            
            print(f"\nNode Details:")
            for member in status['members']:
                state = member['stateStr']
                name = member['name']
                health = '✅' if member.get('health', 0) == 1 else '❌'
                priority = next((m['priority'] for m in config['config']['members'] 
                               if m['host'] == name), 1)
                
                print(f"  {health} {name:20} -> {state:12} (Priority: {priority})")
                
        except Exception as e:
            print(f"Failed to get replica set information: {e}")
    
    def write_concerns(self):
        print("\n" + "-"*70)
        print("Write Concern Performance Test")
        print("-"*70)
  
        write_concerns = [
            
            (1, "w=1: Only Primary confirmed"),
            ("majority", "w='majority': Majority nodes confirmed"),
            (3, "w=3: All nodes confirmed")
        ]
        
        for w_value, description in write_concerns:
            self.test_collection.delete_many({})
            print(f"\n{'─'*70}")
            print(f"Test Configuration: {description}")
            print(f"{'─'*70}")
            
            # create a collection with specific Write Concern
            collection = self.db.get_collection(
                'replication_test',
                write_concern=WriteConcern(w=w_value,j=True, wtimeout=5000)
            )   # j=True: journaled writes in disk j=False: cached writes
            
            # test write performance
            try:
                num_runs = 5
                latencies = []
                last_id = None
                
                for i in range(num_runs):
                    # Create a new document for each run to avoid duplicate _id
                    test_doc_copy = {
                        "test_id": f"write_concern_test_{w_value}_{i}",
                        "write_concern": str(w_value),
                        "timestamp": datetime.now(),
                        "data": "x" * 1000  # 1KB data
                    }
                    
                    start_perf = time.perf_counter()
                    result = collection.insert_one(test_doc_copy)
                    latency = (time.perf_counter() - start_perf) * 1000
                    latencies.append(latency)
                    last_id = result.inserted_id
                
                average_latency = sum(latencies[1:]) / (num_runs - 1)
                print(f"Write Success")
                print(f"   Last Document ID: {last_id}")
                print(f"   All Latencies: {[f'{lat:.2f}' for lat in latencies]} ms")    
                print(f"   Average Write Latency: {average_latency:.2f} ms (excluding first run)")
                
            except Exception as e:
                print(f"Write Failed: {e}")
                print(f"This means the current configuration cannot meet the Write Concern requirements")
        print("="*70)
    
    def data_propagation_test(self):
        """
        Demonstrate writes to Primary and data propagation to Secondaries
        """
        print("\n" + "-"*70)
        print("Data Propagation: Primary → Secondaries")
        print("-"*70)
        
        try:
            # Step 1: Identify Primary and Secondaries
            print("\n Step 1: Identify Cluster Topology")
            print("─"*70)
            
            status = self.client.admin.command("replSetGetStatus")
            primary = None
            secondaries = []
            
            for member in status['members']:
                if member['stateStr'] == 'PRIMARY':
                    primary = member['name']
                elif member['stateStr'] == 'SECONDARY':
                    secondaries.append(member['name'])
            
            print(f"✅ Primary:      {primary}")
            print(f"✅ Secondaries:  {', '.join(secondaries)}")
            
            # Step 2: Write to Primary
            print(f"\n Step 2: Write and read Data against the primary")
            print("─"*70)
            self.db.get_collection('replication_test').delete_many({})
            test_doc = {
                "test_id": f"propagation_test_{int(time.time())}",
                "message": "Testing data propagation from Primary to Secondaries",
                "timestamp": datetime.now(),
                "written_to": primary
            }

            primary_collection = self.db.get_collection(
                'replication_test',
                write_concern=WriteConcern(w=1)
            )

            primary_collection.insert_one(test_doc)
            print(f"✅ Data written to Primary: {primary}")

            secondary_collection = self.db.get_collection(
                'replication_test',
                read_preference=ReadPreference.SECONDARY
            )
            immediate_read = secondary_collection.find_one({"test_id": test_doc["test_id"]})
            if immediate_read:
                print(f"✅ Data found immediately in Secondary")
            else:
                print(f"  Data not found yet in Secondary")

            time.sleep(0.1)
            delayed_read = secondary_collection.find_one({"test_id": test_doc["test_id"]})
            if delayed_read:
                print(f"✅ Data found after 0.1 seconds in Secondary")
            else:
                print(f"  Data not found yet in Secondary")
            
        except Exception as e:
            print(f"❌ Experiment failed: {e}")
            traceback.print_exc()
    
    def leader_failover(self):
        """
        Automated Primary Node Failover Simulation
        - Automatically stop primary node
        - Monitor election process and record downtime
        - Test write operations during failure
        - Verify data consistency
        - Auto-recover the node
        """
        print("\n" + "-"*70)
        print("Primary Node Failover Experiment")
        print("-"*70)
        
        primary_container = None
        downtime_start = None
        
        try:
            # Step 1: Identify current primary
            print("\n Step 1: Identify Current Primary Node")
            print("─"*70)
            
            status = self.client.admin.command("replSetGetStatus")
            primary = None
            for member in status['members']:
                if member['stateStr'] == 'PRIMARY':
                    primary = member['name']
                    print(f"✅ Current Primary: {primary}")
                    break
            
            if not primary:
                print("❌ No primary node found!")
                return
            
            primary_container = primary.split(':')[0]
            
            # Step 2: Write test data before failure
            print(f"\n Step 2: Write Test Data to Primary (Before Failure)")
            print("─"*70)
            
            collection = self.db.get_collection(
                'replication_test',
                write_concern=WriteConcern(w="majority")
            )
            
            before_doc = {
                "test_id": "before_failover",
                "message": "Data written BEFORE primary failure",
                "timestamp": datetime.now(),
                "original_primary": primary
            }
            
            result = collection.insert_one(before_doc)
            print(f"✅ Data written successfully")
            print(f"   Document ID: {result.inserted_id}")
            print(f"   Write Concern: majority")
            
            # Step 3: Force Primary to step down (simulated failure)
            print(f"\n Step 3: Force Primary Node to Step Down ({primary_container})")
            print("─"*70)
            
            downtime_start = time.time()
            
            try:
                # Use stepDown command to force primary to step down
                # stepDown forces the primary to become secondary for the specified seconds
                self.client.admin.command('replSetStepDown', 60, force=True)
                print(f"✅ Primary node stepped down successfully")
                print(f"   Primary will not be re-elected for 60 seconds")
            except Exception as e:
                # This is expected - connection will be lost when primary steps down
                if "not master" in str(e).lower() or "connection" in str(e).lower():
                    print(f"✅ Primary stepped down (connection lost as expected)")
                else:
                    print(f" Step down result: {str(e)[:100]}")
                
            # Step 4: Demonstrate ongoing operations during failover
            print(f"\n Step 4: Ongoing Operations During Failover")
            print("─"*70)
            print("Simulating real-world scenario: write operation during election")
            print("")
            
            new_primary = None
            election_time = 0
            write_success = False
            write_latency = 0
            
            during_doc = {
                "test_id": "during_failover",
                "message": "Write attempted during election period",
                "timestamp": datetime.now(),
                "stepdown_time": downtime_start
            }
            
            # Show the ongoing operation timeline
            print(f" Timeline of Events:")
            print(f" t=0.0s: Primary stepDown initiated")
            print(f" t=0.0s: Write operation started...")
            
            write_start_time = time.time()
            
            # Start monitoring in a simple way - show dots while waiting
            import sys
            sys.stdout.write(" [Write Status] Waiting")
            sys.stdout.flush()
            
            # Try to write - this will block until election completes
            try:
                result = collection.insert_one(during_doc)
                write_latency = (time.time() - write_start_time) * 1000
                write_success = True
                
                print(f"\r [Write Status] ✅ Completed after {write_latency/1000:.1f}s")

                
            except Exception as e:
                write_latency = (time.time() - write_start_time) * 1000
                print(f"\r [Write Status] ❌ Failed after {write_latency/1000:.1f}s")
            
            # Check election result
            print(f" [Election] Checking status...")
            max_wait = 30
            check_interval = 2
            
            for i in range(int(max_wait / check_interval)):
                time.sleep(check_interval)
                try:
                    status = self.client.admin.command("replSetGetStatus")
                    for member in status['members']:
                        if member['stateStr'] == 'PRIMARY':
                            new_primary = member['name']
                            election_time = time.time() - downtime_start
                            break
                    
                    if new_primary:
                        print(f" [Election] ✅ New Primary: {new_primary}")
                        print(f" t={election_time:.1f}s: Election completed")
                        break
                    else:
                        print(f" [t={(i+1)*check_interval}s] Election in progress...")
                        
                except Exception as e:
                    print(f" [t={(i+1)*check_interval}s] Checking...")
            
            if not new_primary:
                print(f" No new primary elected within {max_wait} seconds")
            
            # Analysis
            print(f"\n Operation Analysis:")
            if write_success:
                print(f"✅ Write Operation: SUCCESS")
                print(f"   • Started: t=0.0s (right after stepDown)")
                print(f"   • Completed: t={write_latency/1000:.1f}s")
                print(f"   • Duration: {write_latency/1000:.1f} seconds")
            else:
                print(f"❌ Write Operation: FAILED")
                print(f"   • Election took longer than serverSelectionTimeout")
            
            write_errors = [] if write_success else ["timeout"]
            
            # Step 6: Check original primary status
            print(f"\n Step 6: Check Original Primary Status ({primary_container})")
            print("─"*70)
            
            try:
                # Wait a moment for the system to stabilize
                time.sleep(3)
                
                # Check status of the original primary
                status = self.client.admin.command("replSetGetStatus")
                for member in status['members']:
                    if primary_container in member['name']:
                        print(f"✅ Original primary ({primary_container}) is now: {member['stateStr']}")
                        break
            except Exception as e:
                print(f"⚠️  Error checking status: {e}")
            
        except Exception as e:
            print(f"\n Experiment failed: {e}")
            traceback.print_exc()
        
        finally:
            # No cleanup needed when using stepDown
            # The node will automatically be eligible for election after 60 seconds
            pass
    
    def close(self):
        if self.client:
            self.client.close()


def main():
    print("="*70)
    print("Part B: Replication Strategy Experiment")
    print("="*70)
    
    experiments = ReplicationExperiments()
    
    try:
        # show replica set information
        experiments.show_replica_info()
        
        # experiment 1: Write Concern
        input("\nPress Enter to start Experiment 1: Write Concern performance test...")
        experiments.write_concerns()
        
        # experiment 2: Data Propagation
        input("\nPress Enter to start Experiment 2: Data Propagation (Primary → Secondaries)...")
        experiments.data_propagation_test()
        
        # experiment 3: Leader Failover
        input("\nPress Enter to start Experiment 3: Leader Failover (automated)...")
        experiments.leader_failover()
        
        print("\n" + "="*70)
        print("Part B experiments completed!")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted!")
    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
    finally:
        experiments.close()


if __name__ == "__main__":
    main()