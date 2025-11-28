import json
import os

PROJECT_FILE = "test.json"

def migrate_project():
    if not os.path.exists(PROJECT_FILE):
        print(f"Project file {PROJECT_FILE} not found.")
        return

    with open(PROJECT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = data.get("graph", {})
    nodes_list = graph.get("nodes", [])
    
    # 1. Build Title -> ID Map
    title_to_id = {}
    for node_data in nodes_list:
        title = node_data.get("title")
        node_id = node_data.get("id")
        if title and node_id:
            title_to_id[title] = node_id
    
    print(f"Found {len(title_to_id)} nodes.")

    updated_count = 0

    # 2. Iterate and Update
    for node_data in nodes_list:
        content = node_data.get("content", {})
        choices = content.get("choices", [])
        
        for choice in choices:
            target = choice.get("target_node_id")
            
            if target in title_to_id:
                new_id = title_to_id[target]
                if new_id != target:
                    print(f"Migrating choice in '{node_data.get('title')}' : '{target}' -> '{new_id}'")
                    choice["target_node_id"] = new_id
                    updated_count += 1
            
            # Also check replacement data if any
            rep_data = choice.get("replacement_data", {})
            rep_target = rep_data.get("target_node_id")
            if rep_target in title_to_id:
                new_id = title_to_id[rep_target]
                if new_id != rep_target:
                    print(f"Migrating replacement in '{node_data.get('title')}' : '{rep_target}' -> '{new_id}'")
                    rep_data["target_node_id"] = new_id
                    updated_count += 1

        # 3. Update Macros (spawn, movePnj, goto, button)
        logic = node_data.get("logic", {})
        events = logic.get("on_enter", [])
        
        # Helper to update events recursively if needed (though usually flat)
        for event in events:
            params = event.get("parameters", {})
            macro_type = event.get("type")
            
            if macro_type in ["spawn", "movePnj", "goto", "button"]:
                target = params.get("target")
                if target in title_to_id:
                    new_id = title_to_id[target]
                    if new_id != target:
                        print(f"Migrating macro '{macro_type}' in '{node_data.get('title')}' : '{target}' -> '{new_id}'")
                        params["target"] = new_id
                        updated_count += 1

    if updated_count > 0:
        with open(PROJECT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Migration complete. {updated_count} targets updated.")
    else:
        print("No legacy targets found to migrate.")

if __name__ == "__main__":
    migrate_project()
