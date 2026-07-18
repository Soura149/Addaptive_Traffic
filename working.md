# Main Scripts Overview (The `src/` Directory)

This document provides a clear breakdown of the core operational scripts that run the Reinforcement Learning (RL) traffic simulation. Following our recent refactoring, these critical files are all securely located in the `src/` directory.

### 1. `q_learning_agent.py` (The Brain)
**What it does:** This is the core logic of the RL Agent. 
- It defines the **State Space** (how the agent "sees" the intersection, e.g., current queue lengths and waiting times).
- It defines the **Action Space** (how the agent can change the traffic lights).
- It calculates the **Reward Function** (punishing the agent heavily for queue lengths exceeding the 7-car limit, and penalizing it for massive delays).
- It contains the Q-table logic, updating its "knowledge" after every decision based on the resulting rewards.

### 2. `run_experiments.py` (The Training Loop)
**What it does:** This script manages the actual training process.
- It spins up the SUMO simulator over multiple "episodes".
- It forces the untrained agent to interact with the intersection, explore different light combinations, and learn from its mistakes.
- After running thousands of simulation steps, it extracts the learned behavior and saves it as the "frozen" `q_table.json` file in the `sumofiles/` directory.

### 3. `test_variations.py` (The Evaluator)
**What it does:** This script tests how well the agent actually learned.
- It disables learning (freezes the Q-table) so the agent is forced to purely use its optimized policy.
- It dynamically generates traffic at four different volume tiers (200, 400, 800, 1200 cars) using a strict 3:1 asymmetric flow imbalance (heavy West-East traffic, light North-South traffic).
- It logs the agent's performance (maximum queues, average waiting times) at each volume tier and outputs the data to the CSV logs in `sumofiles/`.

### 4. `route_generator.py` (The Traffic Controller)
**What it does:** This script creates the dynamic traffic flow for SUMO to simulate.
- Instead of using a static, pre-programmed traffic file, this script dynamically generates an XML route file (`Traci.rou.xml`) for each specific episode or evaluation tier.
- It uses deterministic seeds (to ensure reproducible tests) and controls the exact ratio of cars traveling West-East vs North-South.

### 5. `traffic_data_collector.py` (The Sensor Network)
**What it does:** This acts as the bridge between the agent and the SUMO TraCI (Traffic Control Interface) API.
- It continuously queries the simulation for live, real-time data like: "How many cars are currently waiting in the West-East lane?" and "What is the maximum waiting time of the oldest car?".
- It feeds this sensory data back to the `q_learning_agent.py` so the brain can make informed decisions.
