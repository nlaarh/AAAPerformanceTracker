#!/bin/bash

# GitHub Repository Creation Script for AAAPerformanceTracker
# Replace YOUR_GITHUB_TOKEN with your actual GitHub token

GITHUB_TOKEN="YOUR_GITHUB_TOKEN"
REPO_NAME="AAAPerformanceTracker"
REPO_DESCRIPTION="A comprehensive Flask-based web application for CEO and executive performance evaluation featuring 360-degree review capabilities, role-based access control, and AI-powered performance analysis."

echo "Creating GitHub repository: $REPO_NAME"

# Create repository using GitHub API
curl -L \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/user/repos \
  -d "{
    \"name\": \"$REPO_NAME\",
    \"description\": \"$REPO_DESCRIPTION\",
    \"private\": false,
    \"has_issues\": true,
    \"has_projects\": true,
    \"has_wiki\": true,
    \"auto_init\": false
  }"

echo "Repository created successfully!"
echo "Next steps:"
echo "1. git remote add origin https://github.com/yourusername/$REPO_NAME.git"
echo "2. git push -u origin main"