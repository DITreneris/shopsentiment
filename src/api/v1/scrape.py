from flask import Blueprint, request, jsonify
from celery.result import AsyncResult
import logging

# Assuming your Celery task is defined in src.tasks.scraper_tasks
from src.tasks.scraper_tasks import scrape_amazon
# Assuming you have a DAL for products
from src.database.product_dal import ProductDAL

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
scrape_bp = Blueprint('scrape_api', __name__, url_prefix='/api/v1/scrape')

@scrape_bp.route('', methods=['POST'])
async def trigger_scrape():
    """
    Triggers the Amazon scraping task for a given ASIN or product URL.
    Expects JSON body: {\"url\": \"<amazon_product_url>\"} or {\"asin\": \"<product_asin>\"}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    product_url = data.get('url')
    asin = data.get('asin')

    if not product_url and not asin:
        return jsonify({"error": "Missing 'url' or 'asin' in request body"}), 400

    # TODO: Extract ASIN from URL if only URL is provided
    if product_url and not asin:
        # Basic extraction, improve as needed
        try:
            # Look for /dp/<ASIN> or /gp/product/<ASIN>
            if '/dp/' in product_url:
                asin = product_url.split('/dp/')[1].split('/')[0].split('?')[0]
            elif '/gp/product/' in product_url:
                 asin = product_url.split('/gp/product/')[1].split('/')[0].split('?')[0]
            else:
                raise ValueError("Could not extract ASIN from URL")
        except Exception as e:
             logger.error(f"Failed to extract ASIN from URL {product_url}: {e}")
             return jsonify({"error": f"Could not extract ASIN from URL: {product_url}"}), 400

    if not asin: # Should not happen if logic above is correct, but double check
        return jsonify({"error": "Failed to determine ASIN"}), 400

    logger.info(f"Received scrape request for ASIN: {asin}")

    try:
        # Optional: Check if product exists, create basic entry if not (using DAL)
        # product_dal = ProductDAL()
        # product = await product_dal.get_product_by_asin(asin)
        # if not product:
        #     logger.info(f"Product {asin} not in DB. Consider adding basic entry.")
        #     # Add basic product entry here if desired before scraping
        # else:
        #     logger.info(f"Product {asin} found in DB.")

        # Trigger Celery task
        # Pass ASIN and potentially the existing DB ID if found
        task = scrape_amazon.delay(product_asin=asin, product_url=product_url)
        logger.info(f"Dispatched Celery task {task.id} for ASIN {asin}")

        return jsonify({
            "message": "Scraping task started",
            "task_id": task.id,
            "asin": asin
        }), 202 # Accepted

    except Exception as e:
        logger.exception(f"Error triggering scrape task for ASIN {asin}: {e}")
        return jsonify({"error": "Failed to start scraping task"}), 500

@scrape_bp.route('/status/<task_id>', methods=['GET'])
def get_scrape_status(task_id):
    """
    Checks the status of a previously started scraping task.
    """
    try:
        task_result = AsyncResult(task_id, app=scrape_amazon.app) # Need Celery app instance

        status = task_result.state
        result = task_result.result

        response = {
            'task_id': task_id,
            'status': status,
        }
        if status == 'PENDING':
             response['info'] = 'Task is waiting to be executed or unknown.'
        elif status == 'PROGRESS':
             response['info'] = result # Meta data is stored in result during PROGRESS
        elif status == 'SUCCESS':
             response['result'] = result # Final result is stored here
        elif status == 'FAILURE':
             # Result might be the exception raised
             response['error'] = str(result) if result else 'Task failed without error details.'

        return jsonify(response), 200

    except Exception as e:
        logger.exception(f"Error checking status for task {task_id}: {e}")
        return jsonify({"error": "Failed to get task status"}), 500

# You might need to register this blueprint in your main app factory (e.g., src/app_factory.py)
# Example registration:
# from .api.v1.scrape import scrape_bp
# app.register_blueprint(scrape_bp) 