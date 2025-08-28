#!/usr/bin/env python3
"""
Setup script for EWS Git hooks and pre-commit framework.

This script installs and configures:
1. Pre-commit framework for automated code quality checks
2. Custom git hooks for testing and validation
3. Required dependencies for hook functionality

Author: Rank Rocket Co (C) Copyright 2025 - All Rights Reserved
Created: 2025-08-28
"""

import subprocess
import sys
import os
from pathlib import Path


def print_banner():
    """Print setup banner."""
    print("=" * 60)
    print("EWS Git Hooks & Pre-commit Setup")
    print("   Ethical Web Scraper Development Tools")
    print("=" * 60)


def check_python():
    """Check Python version and environment."""
    print("\nChecking Python Environment...")
    
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ required")
        sys.exit(1)
    
    print(f"OK: Python {sys.version.split()[0]} - OK")
    return True


def check_git():
    """Check if we're in a Git repository."""
    print("\n📋 Checking Git Repository...")
    
    if not Path('.git').exists():
        print("❌ Not in a Git repository")
        sys.exit(1)
    
    print("✅ Git repository detected")
    return True


def install_pre_commit():
    """Install pre-commit framework."""
    print("\n📦 Installing pre-commit framework...")
    
    try:
        # Check if pre-commit is already installed
        result = subprocess.run(['pre-commit', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ pre-commit already installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    # Install pre-commit
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pre-commit'], 
                      check=True, capture_output=True)
        print("✅ pre-commit framework installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install pre-commit: {e}")
        return False


def install_optional_tools():
    """Install optional but recommended tools."""
    print("\n🔧 Installing optional development tools...")
    
    optional_tools = [
        ('black', 'Code formatting'),
        ('isort', 'Import sorting'), 
        ('bandit', 'Security scanning'),
        ('pyyaml', 'YAML parsing for config validation')
    ]
    
    installed = []
    for tool, description in optional_tools:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', tool],
                          check=True, capture_output=True)
            installed.append(f"✅ {tool} - {description}")
        except subprocess.CalledProcessError:
            installed.append(f"⚠️  {tool} - Failed to install (optional)")
    
    for result in installed:
        print(f"  {result}")


def setup_pre_commit_hooks():
    """Set up pre-commit hooks."""
    print("\n⚙️  Setting up pre-commit hooks...")
    
    if not Path('.pre-commit-config.yaml').exists():
        print("❌ .pre-commit-config.yaml not found")
        return False
    
    try:
        # Install the git hook scripts
        subprocess.run(['pre-commit', 'install'], check=True, capture_output=True)
        print("✅ Pre-commit hooks installed in .git/hooks/")
        
        # Install commit-msg hook for conventional commits
        subprocess.run(['pre-commit', 'install', '--hook-type', 'commit-msg'], 
                      check=True, capture_output=True)
        print("✅ Commit message hooks installed")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install pre-commit hooks: {e}")
        return False


def validate_setup():
    """Validate the setup by running a quick test."""
    print("\n🧪 Validating setup...")
    
    try:
        # Test import validation
        print("  Testing core module imports...")
        modules = ['scraper', 'exporter', 'image_manager', 'validators', 
                  'rate_limiting', 'image_processing', 'exporters']
        
        failed = []
        for module in modules:
            try:
                __import__(module)
            except Exception as e:
                failed.append(f"{module}: {e}")
        
        if failed:
            print(f"⚠️  Some imports failed: {failed}")
            print("   This is expected if tests need updates after refactoring")
        else:
            print("✅ All core modules import successfully")
        
        # Test pre-commit dry run on a single hook
        print("  Testing pre-commit configuration...")
        result = subprocess.run(['pre-commit', 'run', '--all-files', 'trailing-whitespace'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode in [0, 1]:  # 0 = passed, 1 = failed but hook ran
            print("✅ Pre-commit configuration valid")
        else:
            print(f"⚠️  Pre-commit test had issues: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Validation completed with warnings: {e}")
        return True


def print_usage_info():
    """Print usage information."""
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print("\n📖 Usage Information:")
    print("\n🔄 Pre-commit will now run automatically on every commit")
    print("   - Import validation")
    print("   - Quick unit tests") 
    print("   - Code quality checks")
    print("   - Security scanning")
    print("   - Configuration validation")
    
    print("\n⚡ Manual Commands:")
    print("   pre-commit run --all-files    # Run on all files")
    print("   pre-commit run <hook-name>    # Run specific hook")
    print("   pre-commit autoupdate         # Update hook versions")
    
    print("\n🔧 Skip hooks (use sparingly):")
    print("   git commit --no-verify        # Skip all pre-commit hooks")
    print("   SKIP=hook-name git commit     # Skip specific hook")
    
    print("\n📝 Configuration files:")
    print("   .pre-commit-config.yaml       # Pre-commit configuration")
    print("   .git/hooks/pre-commit         # Custom git hook")
    
    print("\n⚠️  Note: Some tests may fail after architecture refactoring")
    print("   This is expected and will be addressed in Sprint 1.4")


def main():
    """Main setup function."""
    print_banner()
    
    # Check prerequisites
    check_python()
    check_git()
    
    # Install components
    if not install_pre_commit():
        print("❌ Setup failed - could not install pre-commit")
        sys.exit(1)
    
    install_optional_tools()
    
    # Setup hooks
    if not setup_pre_commit_hooks():
        print("❌ Setup failed - could not install hooks")
        sys.exit(1)
    
    # Validate
    validate_setup()
    
    # Print usage info
    print_usage_info()
    
    print("\n✅ Git hooks setup complete!")


if __name__ == "__main__":
    main()