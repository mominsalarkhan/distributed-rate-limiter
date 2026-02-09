from locust import HttpUser, task, between
import random

class RateLimiterUser(HttpUser):
    wait_time = between(0.001, 0.01)  # Very fast requests
    
    def on_start(self):
        """Assign each user a unique ID"""
        self.user_id = f"user_{random.randint(1, 1000)}"
    
    @task(10)
    def test_api_endpoint(self):
        """Main API endpoint - weighted heavily"""
        self.client.get(f"/api/data?user_id={self.user_id}")
    
    @task(1)
    def test_stats_endpoint(self):
        """Stats endpoint - less frequent"""
        self.client.get(f"/stats/{self.user_id}")
    
    @task(1)
    def test_health_endpoint(self):
        """Health check"""
        self.client.get("/health")