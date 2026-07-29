#!/usr/bin/env python3
import os
import re
import json
import sys
import random
import subprocess
from datetime import datetime

# Regex pattern to match "[YYYY-MM-DD] GDP Credit: <random string/number>"
BILLING_PATTERN = re.compile(r"\[(?P<date>\d{4}-\d{2}-\d{2})\]\s*GDP\s+Credit:", re.IGNORECASE)

def generate_project_id():
    """Generates a project ID in the format: adk-2-tutorial-XXXX (where XXXX is 4 random digits)."""
    random_digits = f"{random.randint(0, 9999):04d}"
    return f"adk-2-tutorial-{random_digits}"

def get_billing_accounts():
    """Fetches open billing accounts using gcloud command line tool."""
    print("Fetching billing accounts via gcloud...")
    try:
        result = subprocess.run(
            ["gcloud", "billing", "accounts", "list", "--format=json"],
            check=True,
            capture_output=True,
            text=True,
        )
        accounts = json.loads(result.stdout)
        return accounts
    except FileNotFoundError:
        print("Error: 'gcloud' CLI command not found. Please ensure Google Cloud SDK is installed.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error fetching billing accounts: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing billing accounts JSON: {e}")
        return None

def find_latest_matching_billing_account(accounts):
    """Finds open billing accounts matching '[YYYY-MM-DD] GDP Credit:' pattern

    and returns the account object with the newest (latest) date.
    """
    matching_accounts = []
    for acc in accounts:
        # Filter for open billing accounts
        if not acc.get("open", True):
            continue

        display_name = acc.get("displayName", "")
        match = BILLING_PATTERN.search(display_name)
        if match:
            date_str = match.group("date")
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                raw_name = acc.get("name", "")
                account_id = raw_name.replace("billingAccounts/", "")
                matching_accounts.append((parsed_date, date_str, account_id, display_name, acc))
            except ValueError:
                continue

    if not matching_accounts:
        return None

    # Sort by date descending to get the latest date first
    matching_accounts.sort(key=lambda x: x[0], reverse=True)
    return matching_accounts[0]

def create_gcp_project(project_id):
    """Creates a new GCP project with the specified Project ID."""
    print(f"\nCreating GCP project '{project_id}'...")
    try:
        subprocess.run(
            [
                "gcloud",
                "projects",
                "create",
                project_id,
                f"--name={project_id}",
            ],
            check=True,
        )
        print(f"Successfully created GCP project '{project_id}'.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating GCP project '{project_id}': {e}")
        return False

def link_project_to_billing(project_id, billing_account_id):
    """Links the GCP project to the specified Billing Account ID."""
    print(f"\nLinking project '{project_id}' to billing account '{billing_account_id}'...")
    try:
        subprocess.run(
            [
                "gcloud",
                "billing",
                "projects",
                "link",
                project_id,
                f"--billing-account={billing_account_id}",
            ],
            check=True,
        )
        print(f"Successfully linked '{project_id}' to billing account '{billing_account_id}'.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error linking billing account to project: {e}")
        return False

def set_active_gcloud_project(project_id):
    """Sets the active gcloud project and saves the Project ID to ~/project_id.txt."""
    print(f"\nSetting active gcloud configuration project to '{project_id}'...")
    subprocess.run(["gcloud", "config", "set", "project", project_id])

    project_file = os.path.expanduser("~/project_id.txt")
    try:
        with open(project_file, "w") as f:
            f.write(project_id + "\n")
        print(f"Saved Project ID to {project_file}")
    except Exception as e:
        print(f"Warning: Could not save Project ID to {project_file}: {e}")

def main():
    print("=== Starting GCP Project Creation & Billing Enablement ===")
    
    accounts = get_billing_accounts()
    if accounts is None:
        sys.exit(1)

    latest_account = find_latest_matching_billing_account(accounts)
    if not latest_account:
        print("\n----------------- ACTION REQUIRED -----------------")
        print("No open billing account matching the pattern '[YYYY-MM-DD] GDP Credit:' was found.")
        print("\nAvailable open billing accounts found:")
        found_any = False
        for acc in accounts:
            if acc.get("open", True):
                found_any = True
                print(f" - ID: {acc.get('name')}, Name: '{acc.get('displayName')}'")
        if not found_any:
            print(" (None)")
        print("---------------------------------------------------")
        sys.exit(1)

    parsed_date, date_str, account_id, display_name, acc_obj = latest_account
    print(f"\nFound latest matching billing account:")
    print(f" - Display Name: {display_name}")
    print(f" - Date:         {date_str}")
    print(f" - Account ID:   {account_id}")

    project_id = generate_project_id()
    print(f"\nGenerated Project ID: {project_id}")

    if not create_gcp_project(project_id):
        sys.exit(1)

    if not link_project_to_billing(project_id, account_id):
        sys.exit(1)

    set_active_gcloud_project(project_id)
    print(f"\n=== Billing Setup Complete! Project '{project_id}' is ready to use. ===")

if __name__ == "__main__":
    main()
