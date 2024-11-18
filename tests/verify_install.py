import os
import sys
from pathlib import Path

def print_environment_info():
    """Print relevant environment information for debugging."""
    print("=== Environment Information ===")
    print(f"Python Version: {sys.version}")
    print(f"Python Path: {sys.path}")
    print("\n=== Package Locations ===")
    
    try:
        import worksheets
        print(f"Worksheets package location: {worksheets.__file__}")
    except ImportError as e:
        print(f"Could not import worksheets: {e}")
    
    print("\n=== Directory Structure ===")
    project_root = Path.cwd()
    for path in project_root.rglob("*/__init__.py"):
        print(f"Found package: {path}")

    print("\n=== Installed Packages ===")
    import pkg_resources
    for package in pkg_resources.working_set:
        if package.key in ['worksheets', 'neu-llm-avatars']:
            print(f"{package.key}: {package.version} at {package.location}")

if __name__ == "__main__":
    print_environment_info()