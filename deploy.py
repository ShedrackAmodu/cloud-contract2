#!/usr/bin/env python3
"""
Deployment script for privacy_smartcontracts on PythonAnywhere.

This script automates pushing changes to GitHub, triggering auto-deployment on PythonAnywhere.

Prerequisites:
1. PythonAnywhere web app linked to GitHub repo with auto-pull and reload enabled.
2. Environment variables set in PythonAnywhere web app settings.

Usage:
    python deploy.py --commit "Your commit message" [--force]

Options:
    --commit TEXT    Commit message for any local changes
    --force          Force push to GitHub (use with caution)
"""
import subprocess
import argparse
import sys

def run_command(command):
    """Run a shell command and return the process result."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd='.')
    return result

def main():
    parser = argparse.ArgumentParser(description="Deploy to PythonAnywhere via GitHub")
    parser.add_argument('--commit', type=str, help='Commit message for changes')
    parser.add_argument('--force', action='store_true', help='Force push to GitHub')
    args = parser.parse_args()

    print("Starting deployment process...")

    # Check if there are uncommitted changes
    status_result = run_command('git status --porcelain')
    if status_result.returncode != 0:
        print(f"Error checking git status: {status_result.stderr}")
        sys.exit(1)

    has_changes = bool(status_result.stdout.strip())

    if has_changes:
        if not args.commit:
            print("You have uncommitted changes. Please provide a commit message with --commit")
            sys.exit(1)

        print("Adding and committing changes...")
        add_result = run_command('git add .')
        if add_result.returncode != 0:
            print(f"Error adding files: {add_result.stderr}")
            sys.exit(1)

        commit_result = run_command(f'git commit -m "{args.commit}"')
        if commit_result.returncode != 0:
            print(f"Error committing: {commit_result.stderr}")
            sys.exit(1)

        print("Changes committed successfully.")
    else:
        if args.commit:
            print("No changes to commit, but commit message provided. Skipping commit.")
        else:
            print("No changes to commit.")

    # Get current branch
    branch_result = run_command('git rev-parse --abbrev-ref HEAD')
    if branch_result.returncode != 0:
        print(f"Error getting current branch: {branch_result.stderr}")
        sys.exit(1)

    current_branch = branch_result.stdout.strip()
    print(f"Current branch: {current_branch}")

    # Push to GitHub
    push_cmd = f'git push origin {current_branch}'
    if args.force:
        push_cmd += ' --force'

    print(f"Pushing to GitHub ({current_branch})...")
    push_result = run_command(push_cmd)
    if push_result.returncode != 0:
        print(f"Push failed: {push_result.stderr}")
        sys.exit(1)

    print("Push successful!")
    print("\nDeployment process completed.")
    print("PythonAnywhere should automatically pull and reload your web app.")
    print("Check your PythonAnywhere web app console or logs for any deployment issues.")
    print("\nIf auto-deployment doesn't work, ensure:")
    print("- Web app is linked to GitHub repo")
    print("- 'Reload every time the app's Git repository is updated' is checked")
    print("- Environment variables are set in web app settings")

if __name__ == "__main__":
    main()
