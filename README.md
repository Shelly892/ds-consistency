# Distributed Data Management and Consistency Models

A comprehensive analysis of distributed data management using MongoDB replica sets, focusing on replication strategies and consistency models to understand CAP theorem trade-offs.

## Project Overview

This lab demonstrates the fundamental trade-offs in distributed database systems through practical experiments with MongoDB replica sets. The project explores:

- **Replication Strategies**: Write concerns, data propagation, and failover mechanisms
- **Consistency Models**: Strong vs. Eventual consistency with performance analysis
- **CAP Theorem**: Practical understanding of Consistency, Availability, and Partition tolerance
- **Distributed Transactions**: ACID vs. Saga pattern analysis

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    MongoDB Replica Set                    │
│                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   mongo1    │    │   mongo2    │    │   mongo3    │    │
│  │  (PRIMARY)  │◄──►│ (SECONDARY) │◄──►│ (SECONDARY) │    │
│  │   Port 27017│    │   Port 27018│    │   Port 27019│    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└───────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Shelly892/ds-consistency.git
   ```

2. **Start the MongoDB cluster**

   ```bash
   docker-compose up -d --build
   ```

3. **Run experiments**
   ```bash
   docker exec -it python-app python main.py
   ```

## Project Structure

```
ds-lab2/
├── app/
│   ├── main.py                 # Main experiment orchestrator
│   ├── mongodb_client.py       # Basic MongoDB operations
│   ├── replication.py          # Part B: Replication experiments
│   ├── consistency.py          # Part C: Consistency model experiments
│   └── requirements.txt        # Python dependencies
│   └── Dockerfile              # docker file
├── docker-compose.yml          # MongoDB cluster configuration
├── LAB_REPORT.md              # Comprehensive analysis report
└── README.md                  # This file
```

## Experiments

#### Part A: Basic Setup

- MongoDB connection and basic CRUD operations
- Data model demonstration

#### Part B: Replication Strategy

- **Write Concern Performance**: w=1 vs w="majority" vs w=3
- **Data Propagation**: Primary → Secondary replication analysis
- **Failover Testing**: Primary node failure and recovery

#### Part C: Consistency Models

- **Strong Consistency (CP)**: WriteConcern(w="majority") + ReadConcern("majority")
- **Eventual Consistency (AP)**: WriteConcern(w=1) + ReadPreference(SECONDARY)
- **Performance Comparison**: 50-70% improvement with eventual consistency
- **Causal Consistency**: Operation ordering and dependencies

## Key Findings

| Configuration | Latency | Data Safety | Use Case                    |
| ------------- | ------- | ----------- | --------------------------- |
| w=1           | ~6ms    | Low         | High-throughput scenarios   |
| w="majority"  | ~10ms   | High        | Balanced performance-safety |
| w=3           | ~14ms   | Highest     | Critical data integrity     |

**Performance Results:**

- Eventual consistency: **50-70% faster** than strong consistency
- Strong consistency: **Complete unavailability** during network partitions
- Eventual consistency: **Partial functionality** maintained during partitions

## Technical Details

- **Database**: MongoDB 7.0 with replica set configuration
- **Containerization**: Docker Compose for multi-node cluster
- **Language**: Python 3.11 with PyMongo driver
- **Environment**: Local Docker containers simulating distributed nodes

## Experiment Menu

```
Experiment menu:
──────────────────────────────────────────────────────────────────────
  Part A: Basic Setup
    1. Run the basic setup and data model demonstration

  Part B: Replication Strategy Experiment
    2. Write Concern performance comparison
    3. Primary node failover demonstration
    4. Data Propagation demonstration

  Part C: Consistency Model Experiment
    5. Strong Consistency Experiment
    6. Eventual Consistency Experiment
    7. Consistency Model Performance Comparison
    8. Causal Consistency Experiment

  Comprehensive
    9. Run all Part B experiments
    10. Run all Part C experiments
```
