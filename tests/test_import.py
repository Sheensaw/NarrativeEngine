try:
    from src.core.models import ProjectModel
    print("Import Successful")
except Exception as e:
    print(f"Import Failed: {e}")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
