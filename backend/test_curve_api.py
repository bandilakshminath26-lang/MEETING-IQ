import urllib.request
import json

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/agent/learning-curve',
    data=json.dumps({'customer_id': 'CUST001'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode('utf-8'))
print('Keys:', list(data.keys()))
print('Stages count:', len(data['stages']))
for s in data['stages']:
    print(f"Stage {s['stage_number']}: {s['title']} ({s['memories_available']} mems, {s['commitments_tracked']} promises)")
    print(f"  Same Q: {s.get('same_question')}")
    print(f"  Agent Knows: {s.get('agent_knows')[:2]}")
    print(f"  What Learned: {s.get('what_learned')[:2]}")
    print(f"  Response: {s.get('agent_response')[:60]}...")
print('\nBehavior Change:')
print(data.get('behavior_change'))
print('\nEvidence Counts:')
print(data.get('evidence_counts'))
