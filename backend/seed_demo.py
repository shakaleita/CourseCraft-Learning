"""Insert optional synthetic demonstration records (safe to rerun)."""
from fastapi.testclient import TestClient
from main import app

SEEDS = [{'title': 'React Architecture', 'instructor': 'Sam Example', 'category': 'Development', 'lessons': 12}, {'title': 'API Security', 'instructor': 'Taylor Example', 'category': 'Security', 'lessons': 8}]
client=TestClient(app)
if client.get('/api/items').json():
    print('Existing records found; skipping seed.')
else:
    for record in SEEDS:
        result=client.post('/api/items',json=record)
        result.raise_for_status()
    print('Added',len(SEEDS),'synthetic sample records.')
