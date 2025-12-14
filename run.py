#!/usr/bin/env python3
import subprocess
import sys
import os


def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'streamlit', 'pandas', 'plotly', 'mysql.connector',
        'python-dotenv', 'requests', 'openai'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            if package == 'mysql.connector':
                __import__('mysql.connector')
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)

    return missing_packages


def main():
    print("🚀 ERP AI Chatbot - Startup Check")
    print("=" * 40)

    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("Please install with: pip install -r requirements.txt")
        sys.exit(1)

    print("✅ All dependencies installed")

    # Check environment file
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found")
        print("Please create .env file with your configuration")
    else:
        print("✅ Environment file found")

    # Start the application
    print("\n🎯 Starting ERP AI Chatbot...")
    print("📱 Open your browser to: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the application\n")

    try:
        os.system("streamlit run app.py")
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")


if __name__ == "__main__":
    main()