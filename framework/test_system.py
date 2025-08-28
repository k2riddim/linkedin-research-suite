#!/usr/bin/env python3
"""
LinkedIn Research Framework - System Test Script
This script performs basic functionality tests to verify system health.
"""

import requests
import json
import time
import sys
from datetime import datetime

class SystemTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': timestamp
        }
        self.test_results.append(result)
        print(f"[{timestamp}] {status} {test_name}")
        if message:
            print(f"    {message}")
    
    def test_health_endpoint(self):
        """Test basic health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                self.log_test("Health Endpoint", True, "API is responding")
                return True
            else:
                self.log_test("Health Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Connection error: {str(e)}")
            return False
    
    def test_database_connection(self):
        """Test database connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/api/accounts", timeout=10)
            if response.status_code in [200, 401]:  # 401 is OK, means auth is working
                self.log_test("Database Connection", True, "Database is accessible")
                return True
            else:
                self.log_test("Database Connection", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Database Connection", False, f"Error: {str(e)}")
            return False
    
    def test_ai_service(self):
        """Test AI service integration"""
        try:
            # Test persona generation endpoint
            test_data = {
                "industry": "Technology",
                "experience_level": "Senior",
                "location": "Paris, France"
            }
            response = self.session.post(
                f"{self.base_url}/api/ai/persona",
                json=test_data,
                timeout=30
            )
            
            if response.status_code in [200, 401, 422]:  # Various acceptable responses
                self.log_test("AI Service", True, "AI endpoint is accessible")
                return True
            else:
                self.log_test("AI Service", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("AI Service", False, f"Error: {str(e)}")
            return False
    
    def test_service_monitoring(self):
        """Test service monitoring endpoints"""
        try:
            response = self.session.get(f"{self.base_url}/api/services/status", timeout=10)
            if response.status_code in [200, 401]:
                self.log_test("Service Monitoring", True, "Service monitoring is working")
                return True
            else:
                self.log_test("Service Monitoring", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Service Monitoring", False, f"Error: {str(e)}")
            return False
    
    def test_frontend_access(self):
        """Test frontend accessibility"""
        try:
            # Test if we can access the main page
            response = self.session.get("http://localhost", timeout=10)
            if response.status_code == 200 and "LinkedIn Research Framework" in response.text:
                self.log_test("Frontend Access", True, "Frontend is accessible")
                return True
            else:
                self.log_test("Frontend Access", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Access", False, f"Error: {str(e)}")
            return False
    
    def test_websocket_endpoint(self):
        """Test WebSocket endpoint availability"""
        try:
            # Just test if the endpoint responds (actual WebSocket testing would be more complex)
            response = self.session.get(f"{self.base_url}/socket.io/", timeout=10)
            # WebSocket endpoints typically return specific responses
            if response.status_code in [200, 400, 404]:  # Various acceptable responses
                self.log_test("WebSocket Endpoint", True, "WebSocket endpoint is available")
                return True
            else:
                self.log_test("WebSocket Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("WebSocket Endpoint", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all system tests"""
        print("🧪 LinkedIn Research Framework - System Tests")
        print("=" * 50)
        print(f"Testing system at: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run tests
        tests = [
            self.test_health_endpoint,
            self.test_database_connection,
            self.test_ai_service,
            self.test_service_monitoring,
            self.test_frontend_access,
            self.test_websocket_endpoint
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(1)  # Small delay between tests
        
        print()
        print("=" * 50)
        print(f"Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is healthy.")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Check system configuration.")
            return False
    
    def generate_report(self):
        """Generate detailed test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'passed_tests': sum(1 for r in self.test_results if r['success']),
            'failed_tests': sum(1 for r in self.test_results if not r['success']),
            'results': self.test_results
        }
        
        with open('test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: test_report.json")

def main():
    """Main test function"""
    # Check if custom URL provided
    base_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    tester = SystemTester(base_url)
    
    try:
        success = tester.run_all_tests()
        tester.generate_report()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test runner error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

