#!/usr/bin/env python3
"""
Tableau LangChain Setup Script

Validates environment and installs dependencies for Tableau LangChain integration.
"""

import os
import sys
import subprocess

# Required environment variables
REQUIRED_VARS = [
    "TABLEAU_DOMAIN",
    "TABLEAU_SITE",
    "TABLEAU_JWT_CLIENT_ID",
    "TABLEAU_JWT_SECRET_ID",
    "TABLEAU_JWT_SECRET",
    "TABLEAU_USER",
]

OPTIONAL_VARS = [
    "TABLEAU_API_VERSION",  # Default: 3.22
    "TABLEAU_DATASOURCE_LUID",  # Can be provided per-query
]

def check_environment():
    """Check required environment variables."""
    missing = []
    for var in REQUIRED_VARS:
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        print("BLOCKED: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        return False

    print("Environment validated:")
    for var in REQUIRED_VARS:
        value = os.environ.get(var, "")
        masked = value[:4] + "..." if len(value) > 8 else "***"
        print(f"  {var}: {masked}")

    return True


def install_dependencies():
    """Install required Python packages."""
    packages = [
        "langchain-tableau>=0.4.0",
        "langchain>=0.2.0",
        "langgraph>=0.2.0",
        "langchain-openai>=0.1.0",  # For OpenAI LLMs
        "langchain-anthropic>=0.1.0",  # For Claude LLMs
    ]

    print("\nInstalling dependencies...")
    for pkg in packages:
        print(f"  Installing {pkg}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"    WARNING: Failed to install {pkg}")
            print(f"    {result.stderr}")

    print("Dependencies installed.")


def verify_installation():
    """Verify the installation works."""
    try:
        from langchain_tableau.tools import initialize_simple_datasource_qa
        print("\nVerification: langchain_tableau imported successfully")
        return True
    except ImportError as e:
        print(f"\nVerification FAILED: {e}")
        return False


def main():
    print("=" * 60)
    print("Tableau LangChain Setup")
    print("=" * 60)

    # Step 1: Check environment
    print("\n[1/3] Checking environment...")
    if not check_environment():
        print("\nSetup incomplete. Set missing variables and re-run.")
        sys.exit(1)

    # Step 2: Install dependencies
    print("\n[2/3] Installing dependencies...")
    install_dependencies()

    # Step 3: Verify
    print("\n[3/3] Verifying installation...")
    if not verify_installation():
        print("\nSetup completed with warnings.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Setup complete! You can now use Tableau LangChain tools.")
    print("=" * 60)


if __name__ == "__main__":
    main()
