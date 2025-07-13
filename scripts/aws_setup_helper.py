#!/usr/bin/env python3
"""
AWS Setup Helper for Textract Table Analyzer
Helps users configure AWS credentials and test the setup
"""

import os
import boto3
import json
from pathlib import Path
import sys

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    print("Checking AWS credentials configuration...")
    
    # Check environment variables
    env_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    env_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    env_region = os.getenv('AWS_DEFAULT_REGION')
    
    print(f"Environment variables:")
    print(f"  AWS_ACCESS_KEY_ID: {'✓ Set' if env_access_key else '✗ Not set'}")
    print(f"  AWS_SECRET_ACCESS_KEY: {'✓ Set' if env_secret_key else '✗ Not set'}")
    print(f"  AWS_DEFAULT_REGION: {env_region if env_region else '✗ Not set'}")
    
    # Check AWS credentials file
    aws_credentials_path = Path.home() / '.aws' / 'credentials'
    aws_config_path = Path.home() / '.aws' / 'config'
    
    print(f"\nAWS files:")
    print(f"  ~/.aws/credentials: {'✓ Exists' if aws_credentials_path.exists() else '✗ Not found'}")
    print(f"  ~/.aws/config: {'✓ Exists' if aws_config_path.exists() else '✗ Not found'}")
    
    return env_access_key and env_secret_key

def test_aws_textract():
    """Test AWS Textract connection"""
    print("\nTesting AWS Textract connection...")
    
    try:
        # Try to create a Textract client
        client = boto3.client('textract')
        
        # Get the caller identity to verify credentials
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        
        print(f"✓ Successfully connected to AWS")
        print(f"  Account ID: {identity['Account']}")
        print(f"  User ARN: {identity['Arn']}")
        print(f"  Region: {client.meta.region_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to connect to AWS: {e}")
        return False

def setup_environment_variables():
    """Interactive setup for environment variables"""
    print("\nSetting up environment variables...")
    print("Enter your AWS credentials (they will be exported to your shell):")
    
    access_key = input("AWS Access Key ID: ").strip()
    secret_key = input("AWS Secret Access Key: ").strip()
    region = input("AWS Region (default: us-east-1): ").strip() or "us-east-1"
    
    if not access_key or not secret_key:
        print("✗ Access key and secret key are required")
        return False
    
    # Create export commands
    export_commands = [
        f'export AWS_ACCESS_KEY_ID="{access_key}"',
        f'export AWS_SECRET_ACCESS_KEY="{secret_key}"',
        f'export AWS_DEFAULT_REGION="{region}"'
    ]
    
    print("\nTo set these environment variables, run the following commands:")
    print("=" * 60)
    for cmd in export_commands:
        print(cmd)
    print("=" * 60)
    
    # Save to a file for convenience
    env_file = Path('aws_env_setup.sh')
    with open(env_file, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# AWS Environment Variables Setup\n")
        f.write("# Run: source aws_env_setup.sh\n\n")
        for cmd in export_commands:
            f.write(cmd + "\n")
    
    print(f"\nCommands saved to {env_file}")
    print(f"You can run: source {env_file}")
    
    return True

def create_aws_credentials_file():
    """Create AWS credentials file"""
    print("\nCreating AWS credentials file...")
    
    access_key = input("AWS Access Key ID: ").strip()
    secret_key = input("AWS Secret Access Key: ").strip()
    region = input("AWS Region (default: us-east-1): ").strip() or "us-east-1"
    
    if not access_key or not secret_key:
        print("✗ Access key and secret key are required")
        return False
    
    # Create .aws directory
    aws_dir = Path.home() / '.aws'
    aws_dir.mkdir(exist_ok=True)
    
    # Create credentials file
    credentials_file = aws_dir / 'credentials'
    with open(credentials_file, 'w') as f:
        f.write("[default]\n")
        f.write(f"aws_access_key_id = {access_key}\n")
        f.write(f"aws_secret_access_key = {secret_key}\n")
    
    # Create config file
    config_file = aws_dir / 'config'
    with open(config_file, 'w') as f:
        f.write("[default]\n")
        f.write(f"region = {region}\n")
    
    print(f"✓ Created {credentials_file}")
    print(f"✓ Created {config_file}")
    
    return True

def check_textract_permissions():
    """Check if user has Textract permissions"""
    print("\nChecking Textract permissions...")
    
    try:
        client = boto3.client('textract')
        
        # Try to make a minimal call to check permissions
        # This will fail if permissions are not set up
        response = client.detect_document_text(
            Document={'Bytes': b'dummy_data'}
        )
        
    except client.exceptions.InvalidDocumentException:
        # This is expected - we sent dummy data
        print("✓ Textract permissions are correctly configured")
        return True
    except Exception as e:
        error_msg = str(e)
        if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
            print("✗ Insufficient permissions for Textract")
            print("Required permissions:")
            print("  - textract:AnalyzeDocument")
            print("  - textract:DetectDocumentText")
            return False
        else:
            print(f"✓ Textract permissions appear to be configured (got expected error: {error_msg})")
            return True

def main():
    """Main setup function"""
    print("AWS Textract Setup Helper")
    print("=" * 30)
    
    while True:
        print("\nOptions:")
        print("1. Check current AWS configuration")
        print("2. Set up environment variables")
        print("3. Create AWS credentials file")
        print("4. Test AWS Textract connection")
        print("5. Check Textract permissions")
        print("6. Exit")
        
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == '1':
            check_aws_credentials()
        elif choice == '2':
            setup_environment_variables()
        elif choice == '3':
            create_aws_credentials_file()
        elif choice == '4':
            test_aws_textract()
        elif choice == '5':
            check_textract_permissions()
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main() 