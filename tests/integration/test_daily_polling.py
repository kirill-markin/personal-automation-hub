#!/usr/bin/env python3
"""
Integration tests for Daily Polling System.

This script tests the calendar sync polling system by:
1. Testing health check and status monitoring
2. Testing manual sync operations with different parameters
3. Testing force run scheduler functionality
4. Testing API endpoints for accounts and sync flows
5. Testing calendar listing functionality

Usage:
    # As pytest integration test
    python -m pytest tests/integration/test_daily_polling.py -v -m integration
    
    # As standalone script
    python tests/integration/test_daily_polling.py
    python tests/integration/test_daily_polling.py --test-manual-sync
    python tests/integration/test_daily_polling.py --test-scheduler
"""

import os
import sys
import argparse
import logging
import time
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyPollingTestHelper:
    """Helper class for daily polling integration tests."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> str:
        """Get API key from environment variables."""
        api_key = os.getenv('WEBHOOK_API_KEY')
        if not api_key:
            raise ValueError("WEBHOOK_API_KEY environment variable not set")
        return api_key
    
    def make_request(self, method: str, endpoint: str, 
                    data: Optional[Dict[str, Any]] = None, 
                    params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {endpoint}: {e}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    logger.error(f"Response: {error_data}")
                except:
                    logger.error(f"Response: {e.response.text}")
            raise
    
    def wait_for_server(self, max_attempts: int = 10, delay: float = 1.0) -> bool:
        """Wait for the server to be available."""
        for attempt in range(max_attempts):
            try:
                result = self.make_request("GET", "/api/v1/webhooks/google-calendar/health")
                if result.get("status") == "healthy":
                    logger.info("Server is healthy and ready for testing")
                    return True
            except:
                logger.info(f"Server not ready, attempt {attempt + 1}/{max_attempts}")
                time.sleep(delay)
        
        logger.error("Server did not become available within timeout")
        return False


@pytest.mark.integration
def test_health_check_endpoint():
    """Test health check endpoint functionality."""
    helper = DailyPollingTestHelper()
    
    # Test health check endpoint
    result = helper.make_request("GET", "/api/v1/webhooks/google-calendar/health")
    
    # Verify response structure
    assert "status" in result, "Health check should include status"
    assert "services" in result, "Health check should include services"
    assert "scheduler_running" in result, "Health check should include scheduler status"
    assert "timestamp" in result, "Health check should include timestamp"
    
    # Verify all services are healthy
    assert result["status"] == "healthy", f"Service should be healthy, got: {result['status']}"
    assert result["scheduler_running"] is True, "Scheduler should be running"
    
    services = result["services"]
    required_services = ["config", "account_manager", "sync_engine", "webhook_handler", "polling_scheduler"]
    for service in required_services:
        assert service in services, f"Service {service} should be in health check"
        assert services[service] is True, f"Service {service} should be initialized"
    
    logger.info("Health check endpoint test passed successfully")


@pytest.mark.integration
def test_sync_status_endpoint():
    """Test sync status endpoint functionality."""
    helper = DailyPollingTestHelper()
    
    # Test sync status endpoint
    result = helper.make_request("GET", "/api/v1/webhooks/google-calendar/status")
    
    # Verify response structure
    assert "sync_engine" in result, "Status should include sync engine info"
    assert "scheduler" in result, "Status should include scheduler info"
    assert "monitored_calendars" in result, "Status should include monitored calendars"
    assert "timestamp" in result, "Status should include timestamp"
    
    # Verify sync engine stats
    sync_engine = result["sync_engine"]
    required_stats = ["events_processed", "busy_blocks_created", "busy_blocks_deleted", 
                     "errors", "accounts", "sync_flows", "last_updated"]
    for stat in required_stats:
        assert stat in sync_engine, f"Sync engine should include {stat}"
        assert isinstance(sync_engine[stat], (int, str)), f"{stat} should be int or str"
    
    # Verify scheduler info
    scheduler = result["scheduler"]
    required_scheduler_fields = ["is_running", "sync_interval_minutes", 
                               "next_run_time", "stats"]
    for field in required_scheduler_fields:
        assert field in scheduler, f"Scheduler should include {field}"
    
    assert scheduler["is_running"] is True, "Scheduler should be running"
    
    # Verify monitored calendars
    monitored_calendars = result["monitored_calendars"]
    assert isinstance(monitored_calendars, list), "Monitored calendars should be a list"
    assert len(monitored_calendars) > 0, "Should have at least one monitored calendar"  # type: ignore
    
    for calendar in monitored_calendars:  # type: ignore
        assert "calendar_id" in calendar, "Calendar should have calendar_id"
        assert "account_id" in calendar, "Calendar should have account_id"
        assert "account_email" in calendar, "Calendar should have account_email"
        assert "flow_name" in calendar, "Calendar should have flow_name"
    
    logger.info("Sync status endpoint test passed successfully")


@pytest.mark.integration
def test_accounts_endpoint():
    """Test accounts listing endpoint functionality."""
    helper = DailyPollingTestHelper()
    
    # Test accounts endpoint
    result = helper.make_request("GET", "/api/v1/webhooks/google-calendar/accounts")
    
    # Verify response structure
    assert "accounts" in result, "Response should include accounts"
    assert "total_accounts" in result, "Response should include total_accounts"
    assert "timestamp" in result, "Response should include timestamp"
    
    # Verify accounts data
    accounts = result["accounts"]
    assert isinstance(accounts, list), "Accounts should be a list"
    assert len(accounts) > 0, "Should have at least one account"  # type: ignore
    assert result["total_accounts"] == len(accounts), "Total accounts should match list length"  # type: ignore
    
    for account in accounts:  # type: ignore
        assert "account_id" in account, "Account should have account_id"
        assert "email" in account, "Account should have email"
        assert "connection_ok" in account, "Account should have connection_ok status"
        assert isinstance(account["account_id"], int), "Account ID should be an integer"
        assert isinstance(account["connection_ok"], bool), "Connected should be boolean"
    
    logger.info(f"Accounts endpoint test passed successfully - found {len(accounts)} accounts")  # type: ignore


@pytest.mark.integration
def test_sync_flows_endpoint():
    """Test sync flows listing endpoint functionality."""
    helper = DailyPollingTestHelper()
    
    # Test sync flows endpoint
    result = helper.make_request("GET", "/api/v1/webhooks/google-calendar/sync-flows")
    
    # Verify response structure
    assert "sync_flows" in result, "Response should include sync_flows"
    assert "total_flows" in result, "Response should include total_flows"
    
    # Verify sync flows data
    sync_flows = result["sync_flows"]
    assert isinstance(sync_flows, list), "Sync flows should be a list"
    assert len(sync_flows) > 0, "Should have at least one sync flow"  # type: ignore
    assert result["total_flows"] == len(sync_flows), "Total flows should match list length"  # type: ignore
    
    for flow in sync_flows:  # type: ignore
        required_fields = ["name", "source_account_id", "source_account_email",
                           "source_calendar_id", "target_account_id", "target_account_email",
                           "target_calendar_id", "start_offset", "end_offset"]
        for field in required_fields:
            assert field in flow, f"Sync flow should have {field}"
        
        assert isinstance(flow["source_account_id"], int), "Source account ID should be int"
        assert isinstance(flow["target_account_id"], int), "Target account ID should be int"
        assert isinstance(flow["start_offset"], int), "Start offset should be int"
        assert isinstance(flow["end_offset"], int), "End offset should be int"
    
    logger.info(f"Sync flows endpoint test passed successfully - found {len(sync_flows)} flows")  # type: ignore


@pytest.mark.integration
def test_calendar_listing_endpoint():
    """Test calendar listing endpoint for each account."""
    helper = DailyPollingTestHelper()
    
    # First get accounts
    accounts_result = helper.make_request("GET", "/api/v1/webhooks/google-calendar/accounts")
    accounts = accounts_result["accounts"]
    
    for account in accounts:
        account_id = account["account_id"]
        account_email = account["email"]
        
        # Test calendar listing for this account
        result = helper.make_request("GET", f"/api/v1/webhooks/google-calendar/accounts/{account_id}/calendars")
        
        # Verify response structure
        assert "account_id" in result, "Response should include account_id"
        assert "calendars" in result, "Response should include calendars"
        assert "total_calendars" in result, "Response should include total_calendars"
        
        assert result["account_id"] == account_id, "Account ID should match request"
        
        # Verify calendars data
        calendars = result["calendars"]
        assert isinstance(calendars, list), "Calendars should be a list"
        assert result["total_calendars"] == len(calendars), "Total calendars should match list length"  # type: ignore
        
        if len(calendars) > 0:  # type: ignore
            for calendar in calendars[:3]:  # Check first 3 calendars  # type: ignore
                assert "id" in calendar, "Calendar should have id"
                assert "summary" in calendar, "Calendar should have summary"
                assert "access_role" in calendar, "Calendar should have access_role"
        
        logger.info(f"Calendar listing test passed for account {account_id} ({account_email}) - found {len(calendars)} calendars")  # type: ignore


@pytest.mark.integration
def test_manual_sync_operations():
    """Test manual sync operations with different parameters."""
    helper = DailyPollingTestHelper()
    
    # Test with different parameters
    test_params = [
        {"days_back": 1, "days_forward": 7},
        {"days_back": 2, "days_forward": 14},
        {"days_back": 0, "days_forward": 3}
    ]
    
    for i, params in enumerate(test_params, 1):
        logger.info(f"Testing manual sync {i} - {params['days_back']} days back, {params['days_forward']} days forward")
        
        # Make manual sync request
        result = helper.make_request("POST", "/api/v1/webhooks/google-calendar/sync/manual", params=params)
        
        # Verify response structure
        assert "success" in result, "Response should include success"
        assert "message" in result, "Response should include message"
        assert "results" in result, "Response should include results"
        
        assert result["success"] is True, f"Manual sync should succeed, got: {result}"
        
        # Verify results structure
        sync_results = result["results"]
        required_fields = ["start_date", "end_date", "sync_type", "calendars_synced",
                          "total_events_found", "total_events_processed", "calendar_results"]
        for field in required_fields:
            assert field in sync_results, f"Sync results should include {field}"
        
        assert sync_results["sync_type"] == "manual", "Sync type should be manual"
        assert isinstance(sync_results["calendars_synced"], int), "Calendars synced should be int"
        assert isinstance(sync_results["total_events_found"], int), "Total events found should be int"
        assert isinstance(sync_results["total_events_processed"], int), "Total events processed should be int"
        assert isinstance(sync_results["calendar_results"], list), "Calendar results should be list"
        
        # Verify calendar results
        if len(sync_results["calendar_results"]) > 0:
            for calendar_result in sync_results["calendar_results"]:
                assert "calendar_id" in calendar_result, "Calendar result should have calendar_id"
                assert "account_id" in calendar_result, "Calendar result should have account_id"
                assert "events_found" in calendar_result, "Calendar result should have events_found"
                assert "events_processed" in calendar_result, "Calendar result should have events_processed"
                assert "results" in calendar_result, "Calendar result should have results"
        
        logger.info(f"Manual sync test {i} passed - synced {sync_results['calendars_synced']} calendars, "
                   f"found {sync_results['total_events_found']} events, "
                   f"processed {sync_results['total_events_processed']} events")
        
        # Small delay between tests
        time.sleep(1)


@pytest.mark.integration
def test_force_scheduler_run():
    """Test force run scheduler functionality."""
    helper = DailyPollingTestHelper()
    
    # Get initial scheduler stats
    initial_status = helper.make_request("GET", "/api/v1/webhooks/google-calendar/status")
    initial_runs = initial_status["scheduler"]["stats"]["total_runs"]
    
    # Force run scheduler
    result = helper.make_request("POST", "/api/v1/webhooks/google-calendar/scheduler/run-now")
    
    # Verify response
    assert "success" in result, "Response should include success"
    assert "message" in result, "Response should include message"
    assert result["success"] is True, f"Force run should succeed, got: {result}"
    
    # Wait for scheduler to run
    logger.info("Waiting 10 seconds for scheduler to complete...")
    time.sleep(10)
    
    # Check status after force run
    final_status = helper.make_request("GET", "/api/v1/webhooks/google-calendar/status")
    final_runs = final_status["scheduler"]["stats"]["total_runs"]
    
    # Verify scheduler ran
    assert final_runs > initial_runs, f"Scheduler should have run (initial: {initial_runs}, final: {final_runs})"
    
    # Verify scheduler stats
    scheduler_stats = final_status["scheduler"]["stats"]
    assert "last_run_time" in scheduler_stats, "Scheduler should have last_run_time"
    assert "last_run_success" in scheduler_stats, "Scheduler should have last_run_success"
    assert scheduler_stats["last_run_success"] is True, "Last run should be successful"
    
    logger.info(f"Force scheduler run test passed - total runs increased from {initial_runs} to {final_runs}")


@pytest.mark.integration
def test_complete_polling_workflow():
    """Test complete polling workflow from initialization to execution."""
    helper = DailyPollingTestHelper()
    
    # 1. Verify system is healthy
    health = helper.make_request("GET", "/api/v1/webhooks/google-calendar/health")
    assert health["status"] == "healthy", "System should be healthy for complete workflow test"
    
    # 2. Get initial system state
    initial_status = helper.make_request("GET", "/api/v1/webhooks/google-calendar/status")
    initial_events_processed = initial_status["sync_engine"]["events_processed"]
    
    # 3. Run manual sync to process some events
    manual_sync_result = helper.make_request("POST", "/api/v1/webhooks/google-calendar/sync/manual", 
                                           params={"days_back": 1, "days_forward": 7})
    assert manual_sync_result["success"] is True, "Manual sync should succeed"
    
    # 4. Verify events were processed
    post_sync_status = helper.make_request("GET", "/api/v1/webhooks/google-calendar/status")
    post_sync_events_processed = post_sync_status["sync_engine"]["events_processed"]
    
    assert post_sync_events_processed >= initial_events_processed, "Events should be processed during sync"
    
    # 5. Force run scheduler and verify it works
    scheduler_result = helper.make_request("POST", "/api/v1/webhooks/google-calendar/scheduler/run-now")
    assert scheduler_result["success"] is True, "Scheduler force run should succeed"
    
    # Wait for scheduler
    time.sleep(8)
    
    # 6. Verify final state
    final_status = helper.make_request("GET", "/api/v1/webhooks/google-calendar/status")
    final_events_processed = final_status["sync_engine"]["events_processed"]
    final_scheduler_runs = final_status["scheduler"]["stats"]["total_runs"]
    
    assert final_events_processed >= post_sync_events_processed, "Scheduler should process events"
    assert final_scheduler_runs > 0, "Scheduler should have run at least once"
    
    # 7. Verify accounts and sync flows are properly configured
    accounts = helper.make_request("GET", "/api/v1/webhooks/google-calendar/accounts")
    sync_flows = helper.make_request("GET", "/api/v1/webhooks/google-calendar/sync-flows")
    
    assert len(accounts["accounts"]) > 0, "Should have configured accounts"
    assert len(sync_flows["sync_flows"]) > 0, "Should have configured sync flows"
    
    logger.info(f"Complete polling workflow test passed - processed {final_events_processed} total events, "
               f"scheduler ran {final_scheduler_runs} times")


def main() -> None:
    """Run standalone test script."""
    parser = argparse.ArgumentParser(description="Test Daily Polling System")
    parser.add_argument("--test-manual-sync", action="store_true", 
                       help="Test only manual sync operations")
    parser.add_argument("--test-scheduler", action="store_true", 
                       help="Test only scheduler operations")
    parser.add_argument("--base-url", default="http://localhost:8000",
                       help="Base URL for API requests")
    
    args = parser.parse_args()
    
    # Initialize helper
    helper = DailyPollingTestHelper(args.base_url)
    
    try:
        # Wait for server to be ready
        if not helper.wait_for_server():
            logger.error("Server is not available")
            sys.exit(1)
        
        logger.info("🚀 Starting Daily Polling System Integration Tests")
        logger.info(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run specific tests based on arguments
        if args.test_manual_sync:
            logger.info("Running manual sync tests only...")
            test_manual_sync_operations()
        elif args.test_scheduler:
            logger.info("Running scheduler tests only...")
            test_force_scheduler_run()
        else:
            # Run all tests
            logger.info("Running all daily polling tests...")
            test_health_check_endpoint()
            test_sync_status_endpoint()
            test_accounts_endpoint()
            test_sync_flows_endpoint()
            test_calendar_listing_endpoint()
            test_manual_sync_operations()
            test_force_scheduler_run()
            test_complete_polling_workflow()
        
        logger.info("✅ All daily polling tests completed successfully!")
        logger.info(f"⏰ Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"❌ Daily polling tests failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 