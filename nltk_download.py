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
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Direct import of downloader to avoid interactive prompts
from nltk.downloader import download

# Download NLTK data using the download function directly
packages = ['vader_lexicon', 'punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
for package in packages:
    logger.info(f"Downloading {package}...")
    try:
        download(package, download_dir=nltk_data_dir, quiet=True)
        logger.info(f"Successfully downloaded {package}")
    except Exception as e:
        logger.error(f"Failed to download {package}: {e}")

logger.info("NLTK download process completed") 