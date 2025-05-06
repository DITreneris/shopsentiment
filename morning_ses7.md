# Plan for ShopSentiment Scraping Integration & Fixes (Morning Session 7 - Revised)

## Objective
Integrate and fix the **existing** review scraping functionality (found in the `app` directory) into the main application structure (`src`) to fulfill the core requirement of collecting product reviews from external e-commerce platforms (Amazon.com) as described in the `README.md`.

## Current Status
- Backend services (DB, Cache, API framework) are stable on Heroku (v63).
- API endpoints (`/api/v1/products`, `/api/v1/sentiment/analyze`) are functional for manually added data.
- **Scraping Code Found:** Existing code for scraping Amazon reviews (`app/scrapers/amazon_scraper.py`), using a resilient utility (`app/utils/resilient_scraper.py`), and intended to run via Celery tasks (`app/tasks.py`) has been located. This code is currently **not integrated** with the primary `src` application structure.

## Revised Implementation Plan (Focus: Integration & Fixes)

**(Previous plan based on building from scratch is now obsolete)**

1.  **Step 1: Consolidate Code Structure (Immediate Priority)**
    - **Action 1.1:** Move relevant scraping/utility/task files from `app/` directory to the `src/` directory structure.
        - *Suggestion:* `app/scrapers/` -> `src/scraper/`, `app/utils/resilient_scraper.py` -> `src/utils/`, `app/tasks.py` -> `src/tasks.py`.
    - **Action 1.2:** Update all import statements within the moved files and any files that might use them (e.g., tasks file importing scraper) to reflect the new `src` locations.

2.  **Step 2: Update Dependencies & Configure Celery**
    - **Action 2.1:** Ensure necessary scraping and task queue dependencies are in `requirements.txt` (`requests`, `beautifulsoup4`, `fake_useragent`, `tenacity`, `celery`, `redis`).
    - **Action 2.2:** Configure Celery broker/backend URLs in `.env` and Heroku config vars (using existing Heroku Redis is recommended).
    - **Action 2.3:** Add Celery worker process to `Procfile` (e.g., `worker: celery -A src.tasks worker --loglevel=info`).

3.  **Step 3: Refactor Scraper & Task Logic**
    - **Action 3.1:** Verify and **Update Amazon CSS Selectors** in `src/scraper/amazon_scraper.py`. This is critical as Amazon's structure changes often.
    - **Action 3.2:** Modify scraper/task logic to use the correct **MongoDB DAL** (`src/database/product_dal.py`) for saving products and reviews. Ensure data format compatibility with `src.models`.
    - **Action 3.3:** Remove redundant sentiment analysis from the scraper; rely on the main application's `SentimentService`.
    - **Action 3.4:** Update Celery task (`src/tasks.py`) to use corrected imports and DAL interactions.

4.  **Step 4: Implement Trigger API Endpoint**
    - **Action 4.1:** Create a new API route file (e.g., `src/api/v1/scrape.py`) with a blueprint.
    - **Action 4.2:** Define the `POST /api/v1/scrape` endpoint accepting an Amazon product URL or ASIN.
    - **Action 4.3:** Implement logic for the endpoint to:
        - Check if the product exists in the DB (using `ProductDAL`). Create a basic product entry if not.
        - Trigger the `scrape_amazon.delay(asin=..., db_id=...)` Celery task, passing necessary identifiers.
        - Return a response indicating the task has started (e.g., task ID).
    - **Action 4.4:** Register the new scrape blueprint in `src/api/v1/__init__.py`.

5.  **Step 5: Local Testing & Debugging**
    - **Action 5.1:** Run Flask app, Redis, and Celery worker locally.
    - **Action 5.2:** Test the `/api/v1/scrape` endpoint with various Amazon product URLs/ASINs.
    - **Action 5.3:** Monitor logs (Flask, Celery worker, scraper) for errors.
    - **Action 5.4:** Debug CSS selectors, database integration, and task execution.
    - **Action 5.5:** Verify scraped data appears correctly in the database via `/api/v1/products`.

6.  **Step 6: Deploy & Test on Heroku**
    - **Action 6.1:** Commit all consolidated and refactored code.
    - **Action 6.2:** Ensure all dependencies and environment variables (including Celery) are set on Heroku.
    - **Action 6.3:** Deploy the application.
    - **Action 6.4:** Scale up the Heroku worker dyno (`heroku ps:scale worker=1`).
    - **Action 6.5:** Test the `/api/v1/scrape` endpoint on the live application.
    - **Action 6.6:** Monitor Heroku logs and verify data persistence.

---

**Next Immediate Actions:** Focus on **Step 1** - Consolidating the code structure by moving files from `app/` to `src/` and fixing imports.