#!/usr/bin/env python
import os
import sys
import ssl
import nltk
import logging
import urllib.request
import zipfile
import io
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("nltk_download")

# Create a directory for NLTK data
nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nltk_data')
os.makedirs(nltk_data_dir, exist_ok=True)

# Add the NLTK data directory to the NLTK path
nltk.data.path.append(nltk_data_dir)

# Set environment variable for NLTK data path (used by child processes)
os.environ['NLTK_DATA'] = nltk_data_dir
logger.info(f"Set NLTK_DATA environment variable to {nltk_data_dir}")

# Workaround for SSL certificate verification issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
    ssl._create_default_https_context = _create_unverified_https_context
    logger.info("Set up unverified HTTPS context for NLTK downloads")
except AttributeError:
    logger.info("Unable to set up unverified HTTPS context")

# NLTK download URLs and paths
NLTK_DOWNLOAD_BASE = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/"
packages = [
    ('vader_lexicon', 'sentiment/vader_lexicon.zip'),
    ('punkt', 'tokenizers/punkt.zip'),
    ('stopwords', 'corpora/stopwords.zip'),
    ('wordnet', 'corpora/wordnet.zip'),
    ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger.zip')
]

# Download each package directly (no interactive prompts)
for package_name, package_url_path in packages:
    logger.info(f"Downloading {package_name}...")
    
    # Check if already downloaded
    target_dir = os.path.join(nltk_data_dir, os.path.dirname(package_url_path))
    package_dir = os.path.join(target_dir, package_name)
    if os.path.exists(package_dir):
        logger.info(f"Package {package_name} already exists at {package_dir}")
        continue
    
    # Create target directory structure
    os.makedirs(target_dir, exist_ok=True)
    
    # Maximum retry attempts
    max_retries = 3
    retry_count = 0
    success = False
    
    while retry_count < max_retries and not success:
        try:
            # Download the package
            url = NLTK_DOWNLOAD_BASE + package_url_path
            logger.info(f"Downloading from {url}")
            
            with urllib.request.urlopen(url, timeout=30) as response:
                # Extract the zip file
                zip_data = io.BytesIO(response.read())
                with zipfile.ZipFile(zip_data) as zip_file:
                    zip_file.extractall(path=target_dir)
            
            logger.info(f"Successfully downloaded and extracted {package_name}")
            success = True
        except Exception as e:
            retry_count += 1
            logger.error(f"Attempt {retry_count}/{max_retries} failed for {package_name}: {e}")
            if retry_count < max_retries:
                logger.info(f"Retrying in 5 seconds...")
                time.sleep(5)
            else:
                logger.error(f"Failed to download {package_name} after {max_retries} attempts")

# Verify NLTK data is available
missing_packages = []
for package_name, package_url_path in packages:
    target_dir = os.path.join(nltk_data_dir, os.path.dirname(package_url_path))
    package_dir = os.path.join(target_dir, package_name)
    if not os.path.exists(package_dir):
        missing_packages.append(package_name)

if missing_packages:
    logger.warning(f"The following packages could not be downloaded: {', '.join(missing_packages)}")
    logger.warning("Application may have limited functionality")
else:
    logger.info("All NLTK packages successfully downloaded")

logger.info("NLTK download process completed") 