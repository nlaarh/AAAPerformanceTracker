#!/bin/bash

echo "Fixing git lock issues and committing changes..."

# Remove git lock files
rm -f .git/index.lock
rm -f .git/config.lock  
rm -f .git/gc.pid.lock
rm -f .git/refs/tags/v3.0-workflow-progress-milestone.lock

echo "Removed git lock files"

# Check git status
echo "Current git status:"
git status

# Add all changes
echo "Adding all changes..."
git add .

# Commit the changes
echo "Committing text alignment fixes..."
git commit -m "Fix: Resolved text alignment issue in assessment response display

- Completely rewrote response display sections in view_all_officer_reviews.html
- Replaced Bootstrap form classes with simple inline styles
- Added permanent CSS rules in modern.css to prevent alignment issues
- Text responses (ACCOMPLISHMENTS, FOCUS, IMPROVEMENT OPPORTUNITIES) now display with consistent left alignment
- Fixed refresh issue where Bootstrap CSS was overriding inline styles

Changes:
- templates/view_all_officer_reviews.html: Simplified response display with inline styles
- static/css/modern.css: Added backup CSS rules for text alignment
- replit.md: Updated with formatting fix documentation"

echo "Changes committed successfully!"

# Show final status
git status
git log --oneline -5