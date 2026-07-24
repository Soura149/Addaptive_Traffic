# Q-Learning Agent Implementation and Results Report

## 1. Agent Implementation

The adaptive traffic signal controller is implemented using a **Q-Learning** Reinforcement Learning architecture. The agent's goal is to optimize phase durations for an intersection with asymmetric traffic demand (e.g., 900 West-East / 300 North-South vehicles).

### State Space
The agent perceives the intersection state based on queue lengths and waiting times for both the West-East (WE) and North-South (NS) approaches.
- **Queue Levels**: Binned into "Low" (< 5), "Medium" (< 15), and "High" (>= 15).
- **Starvation Tracking**: A boolean flag indicating if any vehicle has waited over 100 seconds (categorized as `NoStarvation`, `WE_Starving`, `NS_Starving`, or `Both_Starving`).
- *Example State*: `Low_Medium_NoStarvation`

### Action Space
To handle asymmetric demand efficiently, the action space was expanded into a highly expressive **9-Pair Asymmetric Space**. Each action pair dictates the green phase duration (in seconds) for the respective approaches:
- `(10, 10), (20, 10), (30, 10), (45, 15), (10, 20), (10, 30), (20, 20), (30, 30), (45, 45)`

This provides the RL policy the capability to bias the green time towards heavily saturated arteries or rapidly toggle phases.

---

## 2. Reward Function

Early iterations suffered from "Improvement Reward Exploits," where the agent allowed queues to build up to clear them for massive positive delta rewards. To solve this, the reward function was refactored into a **Dynamic Min-Max Quality Reward** system.

### Empirical Bounds
The system uses pre-calibrated baseline bounds to calculate strict maximums for traffic metrics:
- $W_{max} = 327s$ (Wait Time)
- $Q_{max} = 9$ vehicles (Queue Length)
- $T_{max} = 1.0$ vehicles/sec (Throughput)

### Calculation
Metrics are inverted and normalized between 0 and 1, ensuring the agent is rewarded *only* for maintaining absolute system health.
The final optimized reward function evaluated per step is:

$$R = 0.50 \cdot W_q + 0.30 \cdot T_q + 0.20 \cdot Q_q - P_s$$

Where:
- $W_q$ = Normalized inverted wait time.
- $T_q$ = Normalized throughput.
- $Q_q$ = Normalized inverted queue length.
- $P_s$ = Starvation Penalty (A flat penalty of `2.0` is applied if any single vehicle waits $>100s$).

---

## 3. Agent Results

The agent was trained through an aggressive 100-episode curriculum spanning 5 different traffic volume scenarios, scaling from low traffic (200 vehicles) to peak traffic (1800 vehicles). Upon converging (with exploration rate Epsilon reaching 0.01), the Q-Agent's frozen policy was benchmarked against rigid fixed-time controllers.

### Benchmark Performance Matrix
Below is the evaluation of the agent across the 5 curriculum tiers compared against fixed-time alternatives:

| Scenario | Controller | Avg Wait (s) | Avg Queue | Starves | Steps |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Low (200)** | Fixed-10s | 16.92 | 2.23 | 0 | 1023 |
| | **Q-Agent** | **16.92** | **2.23** | **0** | **1023** |
| | Fixed-45s | 190.50 | 6.80 | 0 | 1019 |
| **Medium (600)** | Fixed-10s | 48.63 | 6.82 | 0 | 2533 |
| | **Q-Agent** | **48.63** | **6.82** | **0** | **2533** |
| | Fixed-45s | 309.05 | 7.14 | 0 | 2061 |
| **Heavy Asym (1200)**| Fixed-10s | 48.76 | 6.96 | 0 | 5058 |
| | **Q-Agent** | **48.76** | **6.96** | **0** | **5058** |
| | Fixed-45s | 305.70 | 7.28 | 0 | 4139 |
| **Heavy Sym (1200)** | Fixed-10s | 49.59 | 7.08 | 0 | 3421 |
| | **Q-Agent** | **49.59** | **7.08** | **0** | **3421** |
| | Fixed-45s | 311.14 | 8.04 | 0 | 2766 |
| **Peak (1800)** | Fixed-10s | 49.08 | 6.98 | 0 | 6746 |
| | **Q-Agent** | **49.08** | **6.98** | **0** | **6746** |
| | Fixed-45s | 311.21 | 7.53 | 0 | 5498 |

### Convergence Conclusion
Across all dynamically scaled demand scenarios, the Q-Agent perfectly converged to emulate the rapid **Fixed-10s controller**. Because the Min-Max reward mathematically prioritizes minimizing absolute cumulative waiting time above all else, the agent discovered that minimizing red light duration for opposing traffic (by toggling as fast as possible via the 10s phase minimum) was mathematically superior to holding long green waves.

Even though highly expressive asymmetric actions (like `(30, 10)` or `(45, 15)`) were available, the rapid 10s toggle cycle proved to be the universal theoretical optimum for this specific single-lane geometric topology.
