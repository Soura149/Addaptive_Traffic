# 🚦 Intelligent Traffic Control: Performance Comparison Matrix

> **Executive Summary**: This report evaluates the exact numeric performance of the optimized RL Agent against established fixed-time baselines across ascending traffic volumes. The metrics reflect isolated test runs capturing throughput, delay, and queue volatility.

---

### 🚗 Scenario: 200 Total Vehicles

| Control Model | Avg Wait Time (s) | Cumulative Throughput | Max Queue (veh) | Queue SD |
| :--- | :---: | :---: | :---: | :---: |
| **RL Agent** |  4.90 |  200 |   3 | 2.80 |
| Fixed 10s |  4.10 |  200 |   7 | 2.50 |
| Fixed 20s |  9.37 |  200 |   7 | 2.50 |
| Fixed 30s | 14.97 |  200 |   7 | 2.50 |
| Fixed 45s | 24.83 |  200 |   7 | 2.50 |

<br>

### 🚗 Scenario: 400 Total Vehicles

| Control Model | Avg Wait Time (s) | Cumulative Throughput | Max Queue (veh) | Queue SD |
| :--- | :---: | :---: | :---: | :---: |
| **RL Agent** |  9.47 |  400 |   6 | 2.80 |
| Fixed 10s |  8.20 |  400 |   7 | 2.50 |
| Fixed 20s | 18.73 |  400 |   7 | 2.50 |
| Fixed 30s | 29.93 |  400 |   7 | 2.50 |
| Fixed 45s | 49.67 |  400 |   7 | 2.50 |

<br>

### 🚗 Scenario: 800 Total Vehicles

| Control Model | Avg Wait Time (s) | Cumulative Throughput | Max Queue (veh) | Queue SD |
| :--- | :---: | :---: | :---: | :---: |
| **RL Agent** | 13.60 |  800 |   7 | 2.80 |
| Fixed 10s | 16.40 |  800 |   7 | 2.50 |
| Fixed 20s | 37.47 |  800 |   7 | 2.50 |
| Fixed 30s | 59.87 |  800 |   7 | 2.50 |
| Fixed 45s | 99.33 |  800 |   7 | 2.50 |

<br>

### 🚗 Scenario: 1200 Total Vehicles

| Control Model | Avg Wait Time (s) | Cumulative Throughput | Max Queue (veh) | Queue SD |
| :--- | :---: | :---: | :---: | :---: |
| **RL Agent** | 32.50 | 1200 |   7 | 3.10 |
| Fixed 10s | 24.60 | 1200 |   7 | 2.50 |
| Fixed 20s | 56.20 | 1200 |   7 | 2.50 |
| Fixed 30s | 89.80 | 1200 |   7 | 2.50 |
| Fixed 45s | 149.00 | 1200 |   7 | 2.50 |

<br>

