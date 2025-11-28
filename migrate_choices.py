import json
import os
import uuid

PROJECT_FILE = "test.json"

def migrate_choices():
    if not os.path.exists(PROJECT_FILE):
        print(f"Project file {PROJECT_FILE} not found.")
        return

    with open(PROJECT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = data.get("graph", {})
    nodes_list = graph.get("nodes", [])
    
    updated_count = 0

    for node_data in nodes_list:
        content = node_data.get("content", {})
        choices = content.get("choices", [])
        
        for choice in choices:
            if "id" not in choice or not choice["id"]:
                new_id = str(uuid.uuid4())
                print(f"Adding ID to choice '{choice.get('text')}' in node '{node_data.get('title')}': {new_id}")
                choice["id"] = new_id
                updated_count += 1
            
            # Check replacement data
            rep_data = choice.get("replacement_data", {})
            if rep_data and ("id" not in rep_data or not rep_data["id"]):
                 # Replacement choices usually don't need tracking for one-shot unless they are also one-shot
                 # But good practice to have IDs
                 pass

    if updated_count > 0:
        with open(PROJECT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Migration complete. {updated_count} choices updated with IDs.")
    else:
        print("No choices needed ID migration.")

if __name__ == "__main__":
    migrate_choices()
