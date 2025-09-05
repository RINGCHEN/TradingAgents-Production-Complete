#!/usr/bin/env python3
"""
HuggingFace Token Setup Helper
"""

from huggingface_hub import login, whoami
import os

def setup_token():
    """Setup HuggingFace token"""
    print("HuggingFace Token Setup")
    print("=" * 30)
    
    # Check if already logged in
    try:
        user = whoami()
        print(f"Already logged in as: {user['name']}")
        return True
    except:
        pass
    
    print("You need to provide your HuggingFace token.")
    print("Get it from: https://huggingface.co/settings/tokens")
    print("")
    
    # Get token from user (you'll need to provide this)
    token = input("Enter your HuggingFace token: ").strip()
    
    if not token:
        print("No token provided")
        return False
    
    try:
        # Login with token
        login(token=token, add_to_git_credential=True)
        
        # Verify login
        user = whoami()
        print(f"Login successful! Logged in as: {user['name']}")
        
        # Test LLaMA access
        from huggingface_hub import model_info
        test_model = "meta-llama/Llama-3.2-1B-Instruct"
        
        try:
            info = model_info(test_model)
            print(f"LLaMA access confirmed: {test_model}")
            return True
        except Exception as e:
            print(f"Cannot access LLaMA model: {e}")
            print("Please check your model access permissions")
            return False
            
    except Exception as e:
        print(f"Login failed: {e}")
        return False

if __name__ == "__main__":
    if setup_token():
        print("\nToken setup successful!")
        print("Now you can run: python scripts/llama_quick_setup.py")
    else:
        print("\nToken setup failed. Please try again.")