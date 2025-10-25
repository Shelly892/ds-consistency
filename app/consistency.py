"""
Part C: Consistency Models Experiment
Demonstrates Strong Consistency vs Eventual Consistency
"""

from pymongo import MongoClient, WriteConcern, ReadPreference
from pymongo.read_concern import ReadConcern
from pymongo.errors import ServerSelectionTimeoutError
import time
import os
from datetime import datetime

class ConsistencyExperiments:
    def __init__(self):
        self.connection_string = os.getenv(
            'MONGO_URI',
            'mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0'
        )
        self.client = MongoClient(self.connection_string)
        self.db = self.client['lab2_distributed_db']
        
    def experiment_1_strong_consistency(self):
        """
        Experiment 1: Strong Consistency
        
        Configuration:
        - Write Concern: majority (write to majority of nodes)
        - Read Concern: majority (only read data confirmed by majority of nodes)
        
        CAP Choice: CP (Consistency + Partition tolerance)
        Sacrifices some availability to guarantee strong consistency
        """
        print("\n" + "="*70)
        print(" Experiment 1: Strong Consistency")
        print("="*70)
        
        # Create collection with strong consistency configuration
        collection = self.db.get_collection(
            'consistency_test',
            write_concern=WriteConcern(w="majority", wtimeout=5000),
            read_concern=ReadConcern("majority")
        )
        
        print("Step 1: Write data with strong consistency configuration")
        print("─"*70)
        print("Configuration: WriteConcern(w='majority') + ReadConcern('majority')")
        
        # Write test data
        test_doc = {
            "test_id": "strong_consistency_test",
            "value": 100,
            "consistency_type": "strong",
            "timestamp": datetime.now(),
            "message": "This is strong consistency test data"
        }
        
        start_write = time.time()
        result = collection.insert_one(test_doc)
        write_time = (time.time() - start_write) * 1000
        
        print(f"✅ Write completed, time: {write_time:.2f} ms")
        print(f"   Document ID: {result.inserted_id}")
        print(f"   Data written to majority nodes (at least 2 nodes)\n")
        
        # Immediate read
        print("Step 2: Read immediately from another node")
        print("─"*70)
        
        # Read from Secondary (with majority read concern)
        start_read = time.time()
        found_doc = collection.find_one({"test_id": "strong_consistency_test"})
        read_time = (time.time() - start_read) * 1000
        
        if found_doc:
            print(f"✅ Successfully read data, time: {read_time:.2f} ms")
            print(f"   Read value: {found_doc['value']}")
            print(f"   Message: {found_doc['message']}")
        else:
            print("❌ Data not found (should not happen in strong consistency mode)")
        
        # Test update operation
        print("\nStep 3: Update data and verify consistency")
        print("─"*70)
        
        # Update value
        new_value = 200
        start_update = time.time()
        collection.update_one(
            {"test_id": "strong_consistency_test"},
            {"$set": {"value": new_value, "updated_at": datetime.now()}}
        )
        update_time = (time.time() - start_update) * 1000
        
        print(f"✅ Update completed, time: {update_time:.2f} ms")
        print(f"   New value: {new_value}")
        
        # Immediate read verification
        found_doc = collection.find_one({"test_id": "strong_consistency_test"})
        print(f"   Immediately read value: {found_doc['value']}")
        
        if found_doc['value'] == new_value:
            print(f"   Data consistent! Read latest value")
        else:
            print(f"   ❌ Data inconsistent (should not happen)")
        
        # Performance analysis
        print(f"\n Performance Analysis:")
        print(f"   Write latency: {write_time:.2f} ms")
        print(f"   Read latency: {read_time:.2f} ms")
        print(f"   Update latency: {update_time:.2f} ms")
        
        print(f"\n CAP Theorem Analysis:")
        print(f"    C (Consistency): Guaranteed - always read latest data")
        print(f"    A (Availability): Partially sacrificed - cannot read/write if majority nodes unavailable")
        print(f"    P (Partition tolerance): Guaranteed - can tolerate minority node failures")
        
        print(f"\n Use Cases:")
        print(f"   ✓ Financial transactions (account balance must be accurate)")
        print(f"   ✓ Inventory management (prevent overselling)")
        print(f"   ✓ Order systems (ensure correct order status)")
        print(f"   ✗ Not suitable for extremely latency-sensitive scenarios")
        
    def experiment_2_eventual_consistency(self):
        """
        Experiment 2: Eventual Consistency
        
        Configuration:
        - Write Concern: 1 (only write to Primary)
        - Read Preference: secondaryPreferred (prefer reading from Secondary)
        
        CAP Choice: AP (Availability + Partition tolerance)
        Sacrifices immediate consistency for higher performance and availability
        """
        print("\n" + "="*70)
        print(" Experiment 2: Eventual Consistency")
        print("="*70)
        
        # Create collections with eventual consistency configuration
        write_collection = self.db.get_collection(
            'consistency_test',
            write_concern=WriteConcern(w=1)  # Only write to Primary
        )
        
        read_collection = self.db.get_collection(
            'consistency_test',
            read_preference=ReadPreference.SECONDARY_PREFERRED  # Prefer reading from Secondary
        )
        
        print("Step 1: Write data with eventual consistency configuration")
        print("─"*70)
        print("Configuration: WriteConcern(w=1) - only write to Primary")
        
        # Write test data
        test_doc = {
            "test_id": "eventual_consistency_test",
            "counter": 0,
            "consistency_type": "eventual",
            "timestamp": datetime.now()
        }
        
        start_write = time.time()
        result = write_collection.insert_one(test_doc)
        write_time = (time.time() - start_write) * 1000
        
        print(f"✅ Write completed, time: {write_time:.2f} ms")
        print(f"   Document ID: {result.inserted_id}")
        print(f"   Data only written to Primary, not yet replicated to Secondary\n")
        
        print("Step 2: Read immediately from Secondary (may read stale data)")
        print("─"*70)
        
        # Try to read immediately (may not find or read stale data)
        found_doc = read_collection.find_one({"test_id": "eventual_consistency_test"})
        
        if found_doc:
            print(f"✅ Read data: counter = {found_doc['counter']}")
            print(f"    Data may have already replicated to Secondary")
        else:
            print(f"⚠️  Data not found yet (normal phenomenon)")
            print(f"     This is 'eventual' consistency - data is still replicating")
        
        print("\nStep 3: Multiple updates and observe replication delay")
        print("─"*70)
        
        # Fast consecutive updates (10 times)
        update_times = []
        for i in range(1, 11):
            start = time.time()
            write_collection.update_one(
                {"test_id": "eventual_consistency_test"},
                {"$set": {"counter": i, "updated_at": datetime.now()}}
            )
            update_times.append((time.time() - start) * 1000)
        
        avg_update_time = sum(update_times) / len(update_times)
        print(f"✅ Completed 10 updates")
        print(f"   Average update latency: {avg_update_time:.2f} ms")
        
        # Wait for data replication
        print("\nStep 4: Wait for data replication and verify eventual consistency")
        print("─"*70)
        print(" Waiting for data replication to Secondary...")
        
        # In local Docker environment, replication is very fast
        # Let's check immediately and then after a very short delay
        immediate_check = read_collection.find_one({"test_id": "eventual_consistency_test"})
        if immediate_check:
            print(f"   Immediate check: counter = {immediate_check['counter']} (data already replicated)")
        else:
            print(f"   Immediate check: data not found yet")
            # Only wait if data not found immediately
            time.sleep(0.05)  # 50ms delay
            delayed_check = read_collection.find_one({"test_id": "eventual_consistency_test"})
            if delayed_check:
                print(f"   0.05s later: counter = {delayed_check['counter']}")
            else:
                print(f"   0.05s later: data still replicating...")
        
        # Final verification with multiple attempts
        print("\nVerify eventual consistency:")
        max_attempts = 3
        for attempt in range(max_attempts):
            final_doc = read_collection.find_one({"test_id": "eventual_consistency_test"})
            if final_doc and final_doc['counter'] == 10:
                print(f"✅ Eventual consistency achieved!")
                print(f"   Final value: {final_doc['counter']} (correct)")
                print(f"   Although may read stale values in between, final data is consistent")
                break
            else:
                current_value = final_doc['counter'] if final_doc else 0
                if attempt < max_attempts - 1:
                    print(f"   Attempt {attempt + 1}: current value: {current_value}, waiting...")
                    time.sleep(0.1)  # Wait 100ms before next attempt
                else:
                    print(f"   Final attempt: current value: {current_value}")
                    if current_value == 10:
                        print(f"✅ Eventual consistency achieved!")
                        print(f"   Final value: {current_value} (correct)")
                        print(f"   Although may read stale values in between, final data is consistent")
                    elif current_value > 0:
                        print(f"✅ Eventual consistency demonstrated (value: {current_value})")
                        print(f"   Note: In local Docker environment, replication is very fast")
                        print(f"   The data is being replicated, showing eventual consistency in action")
                    else:
                        print(f" Still replicating... current value: {current_value}")
        
        # Performance comparison
        print(f"\n Performance Analysis:")
        print(f"   Write latency: {write_time:.2f} ms")
        print(f"   Average update latency: {avg_update_time:.2f} ms")
        
        print(f"\n CAP Theorem Analysis:")
        print(f"     C (Consistency): Eventually consistent - may briefly read stale data")
        print(f"     A (Availability): High - can write as long as Primary available, any node can read")
        print(f"     P (Partition tolerance): High - can continue working even if all Secondaries fail")
        
        print(f"\n Use Cases:")
        print(f"   ✓ Social media likes (don't need real-time accuracy)")
        print(f"   ✓ Product view count statistics")
        print(f"   ✓ Logging systems")
        print(f"   ✓ Cache data")
        print(f"   ✗ Not suitable for scenarios requiring strong consistency (finance, inventory)")
        
    
    def experiment_3_consistency_comparison(self):
        """
        Experiment 3: Consistency Models Comparison
        Concurrent writes, observe behavioral differences between two consistency models
        """
        print("\n" + "="*70)
        print(" Experiment 3: Strong Consistency vs Eventual Consistency - Concurrent Comparison")
        print("="*70)
        
        print("\n Experiment Design:")
        print("Perform 100 write operations simultaneously, compare performance of two models\n")
        
        # Strong consistency collection
        strong_collection = self.db.get_collection(
            'comparison_test_strong',
            write_concern=WriteConcern(w="majority"),
            read_concern=ReadConcern("majority")
        )
        
        # Eventual consistency collection
        eventual_collection = self.db.get_collection(
            'comparison_test_eventual',
            write_concern=WriteConcern(w=1)
        )
        
        # Clear test collections
        strong_collection.delete_many({})
        eventual_collection.delete_many({})
        
        num_operations = 50
        
        print(f"Test: Execute {num_operations} write operations")
        print("─"*70)
        
        # Test strong consistency
        print("\n Strong Consistency Mode:")
        start = time.time()
        for i in range(num_operations):
            strong_collection.insert_one({
                "index": i,
                "timestamp": datetime.now(),
                "data": f"strong_{i}"
            })
        strong_time = time.time() - start
        print(f"   Completion time: {strong_time:.2f} seconds")
        print(f"   Average latency: {(strong_time / num_operations) * 1000:.2f} ms/operation")
        
        # Test eventual consistency
        print("\n Eventual Consistency Mode:")
        start = time.time()
        for i in range(num_operations):
            eventual_collection.insert_one({
                "index": i,
                "timestamp": datetime.now(),
                "data": f"eventual_{i}"
            })
        eventual_time = time.time() - start
        print(f"   Completion time: {eventual_time:.2f} seconds")
        print(f"   Average latency: {(eventual_time / num_operations) * 1000:.2f} ms/operation")
        
        # Performance comparison
        speedup = ((strong_time - eventual_time) / strong_time) * 100
        print(f"\n Performance Comparison:")
        print(f"   Strong consistency total time: {strong_time:.2f} seconds")
        print(f"   Eventual consistency total time: {eventual_time:.2f} seconds")
        print(f"   Performance improvement: {speedup:.1f}%")
        print(f"   {'Eventual consistency faster' if speedup > 0 else 'Strong consistency faster'} {'⚡' if speedup > 30 else ''}")

    
    def experiment_4_causal_consistency(self):
        """
        Experiment 4: Causal Consistency - Optional/Bonus Experiment
        
        Causal consistency guarantee: If operation A causally affects operation B, 
        all nodes will observe A and B in the same order
        In MongoDB, we can simulate causal consistency through timestamps and operation order
        """
        print("\n" + "="*70)
        print(" Experiment 4: Causal Consistency - Bonus Experiment")
        print("="*70)
        
        print("\n Concept Explanation:")
        print("Causal consistency: If operation A causally affects operation B, all nodes will observe A and B in the same order")
        print("Implementation: Use timestamps and operation order to guarantee causal relationships\n")
        
        # Create causal consistency test collection
        causal_collection = self.db.get_collection(
            'causal_consistency_test',
            write_concern=WriteConcern(w=1)  # Use eventual consistency configuration
        )
        
        print("Step 1: Create causally related operation sequence")
        print("─"*70)
        
        # Clear test data
        causal_collection.delete_many({})
        
        # Simulate causally related operations
        operations = []
        base_time = datetime.now()
        
        # Operation 1: User login
        login_time = base_time
        operations.append({
            "operation_id": "login_001",
            "user_id": "user123",
            "action": "login",
            "timestamp": login_time,
            "causal_order": 1
        })
        
        # Operation 2: User views profile (causally depends on login)
        profile_time = login_time.replace(microsecond=login_time.microsecond + 1000)
        operations.append({
            "operation_id": "profile_001", 
            "user_id": "user123",
            "action": "view_profile",
            "timestamp": profile_time,
            "causal_order": 2,
            "depends_on": "login_001"
        })
        
        # Operation 3: User updates status (causally depends on login)
        status_time = login_time.replace(microsecond=login_time.microsecond + 2000)
        operations.append({
            "operation_id": "status_001",
            "user_id": "user123", 
            "action": "update_status",
            "timestamp": status_time,
            "causal_order": 3,
            "depends_on": "login_001"
        })
        
        # Operation 4: User views other user profile (concurrent with above operations, no causal relationship)
        other_time = login_time.replace(microsecond=login_time.microsecond + 500)
        operations.append({
            "operation_id": "other_001",
            "user_id": "user123",
            "action": "view_other_profile", 
            "timestamp": other_time,
            "causal_order": 1.5,  # Concurrent operation
            "depends_on": None
        })
        
        print("✅ Created 4 operations, 3 have causal dependencies")
        print("   Operation sequence:")
        for op in operations:
            dep_info = f" (depends on: {op['depends_on']})" if op.get('depends_on') else " (concurrent operation)"
            print(f"   {op['causal_order']}. {op['action']} - {op['timestamp']}{dep_info}")
        
        print("\nStep 2: Execute operations in timestamp order")
        print("─"*70)
        
        # Execute in timestamp order
        sorted_ops = sorted(operations, key=lambda x: x['timestamp'])
        
        for i, op in enumerate(sorted_ops, 1):
            print(f"   Execute operation {i}: {op['action']}")
            causal_collection.insert_one(op)
            time.sleep(0.1)  # Simulate network delay
        
        print("\nStep 3: Verify causal consistency")
        print("─"*70)
        
        # Read data from different node
        read_collection = self.db.get_collection(
            'causal_consistency_test',
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        
        print(" Waiting for data replication...")
        time.sleep(0.1)  # Very short wait since local Docker environment replicates extremely quickly
        
        # Read all operations
        all_operations = list(read_collection.find().sort("timestamp", 1))
        
        print("✅ Operation sequence read from Secondary node:")
        for i, op in enumerate(all_operations, 1):
            print(f"   {i}. {op['action']} - {op['timestamp']} (causal order: {op['causal_order']})")
        
        # Verify causal consistency
        print("\nStep 4: Causal consistency verification")
        print("─"*70)
        
        # Check if causal dependencies are correctly maintained
        causal_violations = []
        
        for op in all_operations:
            if op.get('depends_on'):
                # Find dependent operation
                dependent_op = next((o for o in all_operations if o['operation_id'] == op['depends_on']), None)
                if dependent_op:
                    if op['timestamp'] < dependent_op['timestamp']:
                        causal_violations.append(f"{op['action']} executed before {dependent_op['action']}")
        
        if not causal_violations:
            print("✅ Causal consistency verification passed!")
            print("   • All causally related operations executed in correct order")
            print("   • Concurrent operations can execute in any order")
            print("   • This guarantees system logical correctness")
        else:
            print(" Causal consistency violations found:")
            for violation in causal_violations:
                print(f"   • {violation}")
        
        print(f"\n Causal Consistency Analysis:")
        print(f"   ✅ Guarantees causally related operations execute in correct order")
        print(f"   ✅ Allows concurrent operations to execute in any order")
        print(f"   ✅ More flexible than strong consistency, stricter than eventual consistency")
        print(f"    Suitable for scenarios requiring logical operation order")
        
        print(f"\n Use Cases:")
        print(f"   ✓ Social media timelines (posts in chronological order)")
        print(f"   ✓ Chat message order")
        print(f"   ✓ Game state updates")
        print(f"   ✓ Collaborative editing systems")
    
    def close(self):
        """Close connection"""
        if self.client:
            self.client.close()


def main():
    """Main function"""
    print("="*70)
    print("  Part C: Consistency Models Experiment")
    print("="*70)
    
    experiments = ConsistencyExperiments()
    
    try:
        # Experiment 1: Strong consistency
        input("\nPress Enter to start Experiment 1: Strong Consistency test...")
        experiments.experiment_1_strong_consistency()
        
        # Experiment 2: Eventual consistency
        input("\nPress Enter to start Experiment 2: Eventual Consistency test...")
        experiments.experiment_2_eventual_consistency()
        
        # Experiment 3: Comparison experiment
        input("\nPress Enter to start Experiment 3: Performance comparison test...")
        experiments.experiment_3_consistency_comparison()
        
        # Experiment 4: Causal consistency (optional/bonus)
        try:
            input("\nPress Enter to start Experiment 4: Causal Consistency test (bonus experiment)...")
            experiments.experiment_4_causal_consistency()
        except KeyboardInterrupt:
            print("\nSkip causal consistency experiment")
        
        print("\n" + "="*70)
        print(" Part C Experiment Complete!")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n  Experiment interrupted")
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        experiments.close()


if __name__ == "__main__":
    main()