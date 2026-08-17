#!/usr/bin/env python3
import os
import sys

def check_maven_test_results():
    """Simple helper script to check if Maven test reports exist and print summary."""
    report_dir = "ledger-writer/target/surefire-reports"
    if not os.path.exists(report_dir):
        print("⚠️ No test reports found. Please run 'mvn test' first.")
        return

    print("🔍 Analyzing local test results...")
    files = [f for f in os.listdir(report_dir) if f.endswith(".txt")]
    for file in files:
        filepath = os.path.join(report_dir, file)
        with open(filepath, "r") as f:
            lines = f.readlines()
            for line in lines:
                if "Tests run:" in line:
                    print(f"📋 {file}: {line.strip()}")

if __name__ == "__main__":
    check_maven_test_results()
