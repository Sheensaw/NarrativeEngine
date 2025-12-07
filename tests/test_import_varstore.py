try:
    from src.engine.variable_store import VariableStore
    print("Import Successful")
except Exception as e:
    print(f"Import Failed: {e}")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
