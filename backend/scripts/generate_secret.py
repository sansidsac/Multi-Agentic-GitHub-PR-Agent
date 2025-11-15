"""
Script to generate a secure webhook secret
"""
import secrets
import sys

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
    
    secret = secrets.token_urlsafe(32)
    print("\n" + "="*80)
    print("Generated Webhook Secret")
    print("="*80)
    print(f"\n{secret}\n")
    print("Add this to your .env file:")
    print(f"GITHUB_WEBHOOK_SECRET={secret}")
    print("\nAnd use it when setting up the GitHub webhook.")
    print("="*80 + "\n")
