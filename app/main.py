import os
import sys
import traceback

def print_header():
    print("\n" + "="*70)
    print("Distributed Data Management and Consistency Models")
    print("="*70)

def print_menu():
    """Print the menu"""
    print("\nExperiment menu:")
    print("─"*70)
    print("  Part A: Basic Setup")
    print("    1. Run the basic setup and data model demonstration")
    print("")
    print("  Part B: Replication Strategy Experiment")
    print("    2. Write Concern performance comparison")
    print("    3. Primary node failover demonstration")
    print("    4. Data Propagation demonstration")
    print("")
    print("  Part C: Consistency Model Experiment")
    print("    5. Strong Consistency Experiment")
    print("    6. Eventual Consistency Experiment")
    print("    7. Consistency Model Performance Comparison")
    print("    8. Causal Consistency Experiment")
    print("")
    print("  Comprehensive")
    print("    9. Run all Part B experiments")
    print("    10. Run all Part C experiments")
    print("")
    print("    Q. Exit")
    print("─"*70)


def run_part_a():
    print("\n" + "="*70)
    print("Start Part A: Basic Setup")
    print("="*70)
    from mongodb_client import main as part_a_main
    part_a_main()

def run_part_b_all():
    print("\nStart Part B: Replication Strategy Experiment...")
    from replication import ReplicationExperiments
    
    experiments = ReplicationExperiments()
    try:
        experiments.show_replica_info()
        
        input("\nPress Enter to continue: Write Concern Experiment...")
        experiments.write_concerns()
        
        input("\nPress Enter to continue: Data Propagation Experiment...")
        experiments.data_propagation_test()
        
        input("\nPress Enter to continue: Failover Experiment...")
        experiments.leader_failover()
        
        print("\n All Part B experiments completed!")
    finally:
        experiments.close()

def run_part_b_write_concern():
    """only run the Write Concern experiment"""
    from replication import ReplicationExperiments
    experiments = ReplicationExperiments()
    try:
        experiments.show_replica_info()
        experiments.write_concerns()
    finally:
        experiments.close()

def run_part_b_data_propagation():
    """only run the Data Propagation experiment"""
    from replication import ReplicationExperiments
    experiments = ReplicationExperiments()
    try:
        experiments.show_replica_info()
        experiments.data_propagation_test()
    finally:
        experiments.close()

def run_part_b_failover():
    """only run the Failover experiment"""
    from replication import ReplicationExperiments
    experiments = ReplicationExperiments()
    try:
        experiments.show_replica_info()
        experiments.leader_failover()
    finally:
        experiments.close()


def run_part_c_all():
    """run all the Part C experiments"""
    print("\nStart Part C: Consistency Model Experiment...")
    from consistency import ConsistencyExperiments
    
    experiments = ConsistencyExperiments()
    try:
        input("\nPress Enter to continue: Strong Consistency Experiment...")
        experiments.experiment_1_strong_consistency()
        
        input("\nPress Enter to continue: Eventual Consistency Experiment...")
        experiments.experiment_2_eventual_consistency()
        
        input("\nPress Enter to continue: Consistency Comparison Experiment...")
        experiments.experiment_3_consistency_comparison()

        input("\nPress Enter to continue: Causal Consistency Experiment...")
        experiments.experiment_4_causal_consistency()
        
        print("\n All Part C experiments completed!")
    finally:
        experiments.close()

def run_part_c_strong():
    """only run the Strong Consistency experiment"""
    from consistency import ConsistencyExperiments
    experiments = ConsistencyExperiments()
    try:
        experiments.experiment_1_strong_consistency()
    finally:
        experiments.close()

def run_part_c_eventual():
    """only run the Eventual Consistency experiment"""
    from consistency import ConsistencyExperiments
    experiments = ConsistencyExperiments()
    try:
        experiments.experiment_2_eventual_consistency()
    finally:
        experiments.close()

def run_part_c_comparison():
    """only run the Consistency Comparison experiment"""
    from consistency import ConsistencyExperiments
    experiments = ConsistencyExperiments()
    try:
        experiments.experiment_3_consistency_comparison()
    finally:
        experiments.close()

def run_part_c_causal():
    """only run the Causal Consistency experiment"""
    from consistency import ConsistencyExperiments
    experiments = ConsistencyExperiments()
    try:
        experiments.experiment_4_causal_consistency()
    finally:
        experiments.close()



def main():
    print_header()
    
    while True:
        print_menu()
        choice = input("\nPlease select the operation (1-10, Q): ").strip().upper()
        
        try:
            if choice == '1':
                run_part_a()
            elif choice == '2':
                run_part_b_write_concern()
            elif choice == '3':
                run_part_b_failover()
            elif choice == '4':
                run_part_b_data_propagation()
            elif choice == '5':
                run_part_c_strong()
            elif choice == '6':
                run_part_c_eventual()
            elif choice == '7':
                run_part_c_comparison()
            elif choice == '8':
                run_part_c_causal()
            elif choice == '9':
                run_part_b_all()
            elif choice == '10':
                run_part_c_all()
            elif choice == 'Q':
                print("\n Goodbye!")
                break
            else:
                print("\nInvalid choice, please try again")
            
            # wait for user to view the result
            if choice != 'Q':
                input("\nPress Enter to return to the main menu...")
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled")
            input("Press Enter to return to the main menu...")
        except Exception as e:
            print(f"\nError: {e}")
            traceback.print_exc()
            input("Press Enter to return to the main menu...")

if __name__ == "__main__":
    main()