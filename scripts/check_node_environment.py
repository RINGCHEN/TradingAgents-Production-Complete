#!/usr/bin/env python3
"""
Quick Node.js Environment Check Script
Validates current Node.js environment for Frontend Testing Setup
"""

import subprocess
import sys
from pathlib import Path

def check_node_environment():
    """Quick check of Node.js environment"""
    print("🔍 Checking Node.js Environment for Frontend Testing...")
    print("-" * 50)
    
    issues = []
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        print(f"✅ Node.js: {version}")
        
        # Check if version is 18+
        version_num = version.lstrip('v').split('.')[0]
        if int(version_num) < 18:
            issues.append(f"Node.js version {version} is too old. Need 18+")
            print(f"⚠️  Warning: Node.js {version} < 18.0.0")
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        issues.append("Node.js not installed")
        print("❌ Node.js: Not found")
    
    # Check npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        print(f"✅ npm: {version}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        issues.append("npm not installed")
        print("❌ npm: Not found")
    
    # Check workspace structure
    workspace_root = Path(__file__).parent.parent
    frontend_dir = workspace_root / "frontend"
    
    print(f"\n📁 Workspace Structure:")
    print(f"Root: {workspace_root}")
    print(f"Frontend: {frontend_dir}")
    
    if not frontend_dir.exists():
        print("⚠️  Frontend directory will be created")
    else:
        print("✅ Frontend directory exists")
    
    # Check existing package.json
    package_json = frontend_dir / "package.json"
    if package_json.exists():
        print("✅ package.json exists")
    else:
        print("⚠️  package.json will be created")
    
    # Summary
    print("\n" + "=" * 50)
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n💡 To fix:")
        if "Node.js not installed" in str(issues):
            print("  1. Install Node.js 18+ from https://nodejs.org/")
        print("  2. Run: python scripts/setup_node_environment.py")
        return False
    else:
        print("✅ Environment looks good!")
        print("Ready to run: python scripts/setup_node_environment.py")
        return True

if __name__ == "__main__":
    success = check_node_environment()
    sys.exit(0 if success else 1)