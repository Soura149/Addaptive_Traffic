import csv
from collections import defaultdict
import json

print('--- EVALUATION LOG ANALYSIS ---')
eval_stats = defaultdict(lambda: {'count': 0, 'wait': 0, 'queue': 0, 'reward': 0})
with open('evaluation_log.csv', 'r') as f:
    for row in csv.DictReader(f):
        state = row['state']
        action = row['action']
        key = f'{state} -> {action}s'
        eval_stats[key]['count'] += 1
        eval_stats[key]['wait'] += float(row['old_waiting_time'])
        eval_stats[key]['queue'] += float(row['old_queue'])
        eval_stats[key]['reward'] += float(row['reward'])

for k, v in eval_stats.items():
    print(f'{k}: count={v["count"]}, avg_wait={v["wait"]/v["count"]:.2f}, avg_queue={v["queue"]/v["count"]:.2f}, avg_reward={v["reward"]/v["count"]:.4f}')

print('\n--- DECISION LOG (TRAINING) ANALYSIS ---')
train_stats = defaultdict(lambda: {'count': 0, 'wait': 0, 'queue': 0, 'reward': 0})
with open('decision_log.csv', 'r') as f:
    for row in csv.DictReader(f):
        state = row['state']
        action = row['action']
        key = f'{state} -> {action}s'
        train_stats[key]['count'] += 1
        train_stats[key]['wait'] += float(row['old_waiting_time'])
        train_stats[key]['queue'] += float(row['old_queue'])
        train_stats[key]['reward'] += float(row['reward'])

print('Rewards for 10s and 30s in key states during training:')
for state in ['Medium*Medium*NoStarvation', 'Low*Medium*NoStarvation']:
    for action in ['10', '30']:
        key = f'{state} -> {action}s'
        if key in train_stats:
            v = train_stats[key]
            print(f'{key}: count={v["count"]}, avg_reward={v["reward"]/v["count"]:.4f}')

print('\n--- Q-TABLE ---')
with open('q_table.json', 'r') as f:
    q = json.load(f)
    for state, actions in q.items():
        print(f'{state}:')
        for action, value in actions.items():
            print(f'  {action}s: {value:.4f}')
