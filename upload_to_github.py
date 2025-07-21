#!/usr/bin/env python3
import os
import requests
import base64
import subprocess
import sys

def get_github_token():
    return os.environ.get('GITHUB_TOKEN')

def upload_file_to_github(owner, repo, file_path, github_token):
    """Upload a single file to GitHub repository"""
    
    # Read file content
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # Encode content in base64
    encoded_content = base64.b64encode(content).decode('utf-8')
    
    # GitHub API URL
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    
    # Check if file exists to get SHA
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get existing file SHA if it exists
    response = requests.get(url, headers=headers)
    sha = None
    if response.status_code == 200:
        sha = response.json()['sha']
    
    # Prepare commit data
    data = {
        'message': f'Update {file_path} - Text alignment fixes',
        'content': encoded_content,
        'branch': 'main'
    }
    
    if sha:
        data['sha'] = sha
    
    # Upload file
    response = requests.put(url, json=data, headers=headers)
    
    if response.status_code in [200, 201]:
        print(f"✅ Successfully uploaded {file_path}")
        return True
    else:
        print(f"❌ Failed to upload {file_path}: {response.status_code}")
        print(response.text)
        return False

def main():
    github_token = get_github_token()
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment variables")
        sys.exit(1)
    
    owner = "nlaarh"
    repo = "AAAPerformanceTracker"
    
    # Files that were modified for the text alignment fix
    files_to_upload = [
        "templates/view_all_officer_reviews.html",
        "static/css/modern.css", 
        "replit.md",
        "DEPLOYMENT_CHANGES_SUMMARY.md"
    ]
    
    print(f"🚀 Uploading text alignment fixes to GitHub repo: {owner}/{repo}")
    
    success_count = 0
    for file_path in files_to_upload:
        if os.path.exists(file_path):
            if upload_file_to_github(owner, repo, file_path, github_token):
                success_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n📊 Upload Summary: {success_count}/{len(files_to_upload)} files uploaded successfully")
    
    if success_count == len(files_to_upload):
        print("🎉 All text alignment fixes successfully pushed to GitHub!")
    else:
        print("⚠️  Some files failed to upload")

if __name__ == "__main__":
    main()