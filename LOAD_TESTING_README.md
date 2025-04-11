# Shop Sentiment Load Testing Guide

This document provides instructions for setting up and running load tests against the Shop Sentiment application using Locust.

## Prerequisites

- Python 3.7+ installed
- Access to Shop Sentiment application (local or remote instance)
- MongoDB with test data generated (using generate_test_data.py)

## Installation

1. Install Locust and dependencies:
   ```
   python -m pip install locust faker
   ```

2. Ensure application is running before starting load tests.

## Configuration

The load testing setup includes:

- `locustfile.py`: Defines user behaviors and test scenarios
- `locust.conf`: Contains test configuration parameters

### User Types

Two user types are defined:

1. **ShopSentimentUser**: Simulates regular website users browsing the site, viewing dashboards, and analyzing products.
2. **APIUser**: Simulates API clients making direct calls to backend endpoints with higher frequency.

### Test Scenarios

The test configuration includes:

- Homepage visits
- Dashboard views
- API calls for reviews
- Product analysis requests
- Review filtering
- Data export operations

## Running the Tests

### Web UI Mode

1. Start Locust with the web interface:
   ```
   locust
   ```

2. Open a browser and navigate to http://localhost:8089

3. Enter the host URL (e.g., http://localhost:5000) and desired number of users.

4. Click "Start swarming" to begin the test.

### Headless Mode

For automated testing, run Locust in headless mode:

```
locust --headless --users 100 --spawn-rate 10 --run-time 5m --host http://localhost:5000
```

Or use the configuration file:

```
locust --config=locust.conf
```

## Interpreting Results

Locust provides several metrics:

- **Response Time**: Average, median, min, max response times
- **Requests Per Second (RPS)**: How many requests the system handles
- **Failure Rate**: Percentage of failed requests
- **User Count**: Number of active virtual users

### Success Criteria

- Response time should stay under 200ms for 95% of requests
- No more than 1% error rate
- System should handle at least 50 requests/second

## Generating Reports

Run with the `--csv` option to generate CSV reports:

```
locust --csv=results
```

This will create:
- `results_stats.csv`: Overall statistics
- `results_failures.csv`: Failed requests
- `results_history.csv`: Time-series data

## Troubleshooting

- If tests fail immediately, check that the app is running and accessible
- If you see authentication errors, update the login credentials in locustfile.py
- For MongoDB connection issues, ensure your database is running and properly configured

## Customizing Tests

Modify `locustfile.py` to:
- Add new user behaviors
- Change task weights (frequency)
- Adjust wait times between tasks
- Add authentication if needed

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [MongoDB Performance Best Practices](https://www.mongodb.com/docs/manual/core/query-optimization/)
- [Flask Performance Tuning](https://flask.palletsprojects.com/en/2.0.x/deploying/) 