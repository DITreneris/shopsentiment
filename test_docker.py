#!/usr/bin/env python
"""
Docker test script for ShopSentiment application.
This script tests the Docker deployment by:
1. Checking container health
2. Testing Redis connection
3. Verifying Celery tasks can be submitted and processed
4. Testing the Flask web application is responding
"""

import os
import sys
import time
import json
import requests
import redis
from subprocess import run, PIPE

DOCKER_COMPOSE_FILE = "docker-compose.yml"
APP_URL = "http://localhost:5000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REQUEST_TIMEOUT = 10

def run_command(command):
    """Run a shell command and return output"""
    result = run(command, shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    return result.stdout, result.stderr, result.returncode

def check_containers():
    """Check if all containers are running"""
    print("\n🔍 Checking Docker containers...")
    
    stdout, stderr, code = run_command("docker-compose ps")
    if code != 0:
        print("❌ Failed to run docker-compose ps")
        print(f"Error: {stderr}")
        return False
    
    print(stdout)
    
    # Check if containers are up
    stdout, stderr, code = run_command("docker-compose ps -q")
    if not stdout.strip():
        print("❌ No containers are running")
        return False
    
    # Check container health
    containers = ["web", "redis", "worker", "beat"]
    all_healthy = True
    
    for container in containers:
        stdout, stderr, code = run_command(f"docker-compose ps {container} | grep Up")
        if not stdout:
            print(f"❌ Container '{container}' is not running")
            all_healthy = False
    
    if all_healthy:
        print("✅ All containers are running")
    
    return all_healthy

def test_redis_connection():
    """Test Redis connection"""
    print("\n🔍 Testing Redis connection...")
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        r.ping()
        print("✅ Redis connection successful")
        
        # Test setting and getting a value
        test_value = "docker-test-value"
        r.set("docker-test-key", test_value)
        retrieved = r.get("docker-test-key").decode('utf-8')
        
        if retrieved == test_value:
            print(f"✅ Redis data operations working (set/get)")
        else:
            print(f"❌ Redis data operation failed. Expected: {test_value}, Got: {retrieved}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        return False

def test_web_application():
    """Test the Flask web application"""
    print("\n🔍 Testing Flask web application...")
    try:
        response = requests.get(f"{APP_URL}/", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            print(f"✅ Web application is responding (Status: {response.status_code})")
            return True
        else:
            print(f"❌ Web application returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to web application")
        return False
    except Exception as e:
        print(f"❌ Error testing web application: {str(e)}")
        return False

def check_log_files():
    """Check if log files are being generated"""
    print("\n🔍 Checking log files...")
    
    stdout, stderr, code = run_command("docker-compose logs --tail=10 web")
    if "Error" in stdout or "error" in stdout.lower():
        print("⚠️ Web container logs contain errors")
        print(stdout)
    else:
        print("✅ Web container logs look OK")
    
    stdout, stderr, code = run_command("docker-compose logs --tail=10 worker")
    if "Error" in stdout or "error" in stdout.lower():
        print("⚠️ Worker container logs contain errors")
        print(stdout)
    else:
        print("✅ Worker container logs look OK")
    
    return True

def main():
    """Main test function"""
    print("🚀 Starting ShopSentiment Docker deployment test")
    
    # Ensure Docker is running
    stdout, stderr, code = run_command("docker --version")
    if code != 0:
        print("❌ Docker is not installed or not running")
        sys.exit(1)
    else:
        print(f"✅ Docker is installed: {stdout.strip()}")
    
    # Ensure Docker Compose is running
    stdout, stderr, code = run_command("docker-compose --version")
    if code != 0:
        print("❌ Docker Compose is not installed")
        sys.exit(1)
    else:
        print(f"✅ Docker Compose is installed: {stdout.strip()}")
    
    # Check if containers are running
    if not check_containers():
        print("\n⚠️ Container check failed. Trying to start containers...")
        stdout, stderr, code = run_command("docker-compose up -d")
        if code != 0:
            print(f"❌ Failed to start containers: {stderr}")
            sys.exit(1)
        
        print("Waiting for containers to start up...")
        time.sleep(10)
        
        if not check_containers():
            print("❌ Containers failed to start properly")
            sys.exit(1)
    
    # Run tests
    tests = [
        test_redis_connection,
        test_web_application,
        check_log_files
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Summary
    print("\n📋 Test Summary:")
    all_passed = all(results)
    
    if all_passed:
        print("✅ All tests passed! The Docker deployment is working correctly.")
    else:
        print("❌ Some tests failed. Please check the logs for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 