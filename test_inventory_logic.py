from src.engine.variable_store import VariableStore

def test_inventory():
    store = VariableStore()
    
    # Mock observer
    changes = []
    def on_change(name, val):
        changes.append((name, val))
    
    store.add_observer(on_change)
    
    print("Adding 'sword' x1...")
    store.add_item("sword", 1)
    
    print("Adding 'sword' x2...")
    store.add_item("sword", 2)
    
    inv = store.get_var("inventory")
    print(f"Final Inventory: {inv}")
    
    if inv.get("sword") == 3:
        print("✅ SUCCESS: Quantity is 3")
    else:
        print(f"❌ FAILURE: Quantity is {inv.get('sword')}")

    print(f"Observer notifications: {len(changes)}")
    if len(changes) >= 2:
        print("✅ SUCCESS: Observers notified")
    else:
        print("❌ FAILURE: Observers NOT notified correctly")

if __name__ == "__main__":
    test_inventory()
