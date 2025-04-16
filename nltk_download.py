#!/usr/bin/env python
import os
import sys
import ssl
import nltk
import logging

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

# Set NLTK data path
nltk.data.path.append(nltk_data_dir)

# Workaround for SSL certificate verification issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
    ssl._create_default_https_context = _create_unverified_https_context
    logger.info("Set up unverified HTTPS context for NLTK downloads")
except AttributeError:
    logger.info("Unable to set up unverified HTTPS context")

# Download NLTK data DIRECTLY without using the downloader module
# We need this for Heroku as it doesn't handle interactive inputs well
packages = [
    ('vader_lexicon', 'sentiment/vader_lexicon.zip'),
    ('punkt', 'tokenizers/punkt.zip'),
    ('stopwords', 'corpora/stopwords.zip'),
    ('wordnet', 'corpora/wordnet.zip'),
    ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger.zip')
]

# NLTK download URLs
NLTK_DOWNLOAD_BASE = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/"

import urllib.request
import zipfile
import io

for package_name, package_url_path in packages:
    logger.info(f"Downloading {package_name}...")
    try:
        # Create target directory structure
        target_dir = os.path.join(nltk_data_dir, os.path.dirname(package_url_path))
        os.makedirs(target_dir, exist_ok=True)
        
        # Download the package
        url = NLTK_DOWNLOAD_BASE + package_url_path
        with urllib.request.urlopen(url) as response:
            # Extract the zip file
            zip_data = io.BytesIO(response.read())
            with zipfile.ZipFile(zip_data) as zip_file:
                zip_file.extractall(path=target_dir)
        
        logger.info(f"Successfully downloaded and extracted {package_name}")
    except Exception as e:
        logger.error(f"Failed to download {package_name}: {e}")

logger.info("NLTK download process completed") 