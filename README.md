# coworker-python-client

Python client voor de Ritense Coworker API.

> **Let op:** dit is een private repository. Vraag toegang aan [@mathijs-ritense](https://github.com/mathijs-ritense).

## Installatie

```bash
pip install git+ssh://git@github.com/mathijs-ritense/coworker-python-client.git
```

## Gebruik 

```python
from coworker import CoworkerClient

client = CoworkerClient(
    base_url="https://coworker.example.com/api/v1",
    username="...",
    password="...",
    case_id="mijn-case",
)

coworkers = client.get_coworkers()
session_id = client.create_session(coworkers[0]["id"])

for token in client.stream_message(session_id, "Hallo!"):
    print(token, end="", flush=True)
```
