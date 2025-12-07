try:
    from src.core.lore_manager import LoreManager
    print("Import Successful")
except Exception as e:
    print(f"Import Failed: {e}")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
