import os
import json
from datetime import datetime

def write_audit(event: dict, path: str = "logs/") -> str:
    if not os.path.exists(path):
        os.makedirs(path)

    filename = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(path, filename)

    with open(filepath, 'w') as f:
        json.dump(event, f)

    return filepath
