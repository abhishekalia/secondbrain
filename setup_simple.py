#!/usr/bin/env python3
import subprocess
import time
import sys

print("🧠 Digital Consciousness - Simple Setup")
print("=" * 40)

# Install required packages
print("📦 Installing packages...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "streamlit", "requests"])

# Check/Install Ollama
print("🤖 Setting up Ollama...")
subprocess.run("brew install ollama", shell=True, capture_output=True)

# Start Ollama
print("🚀 Starting Ollama...")
subprocess.run("pkill ollama", shell=True, capture_output=True)
subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

# Download Qwen
print("📥 Downloading Qwen 2.5 7B (this takes 5-10 minutes)...")
subprocess.run("ollama pull qwen2.5:7b", shell=True)

print("✅ Setup complete!")
print("\nRun: python3 create_app.py")
