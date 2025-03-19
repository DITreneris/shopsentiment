import sys
import os

with open('scrapy_test_output.txt', 'w') as f:
    f.write(f"Python executable: {sys.executable}\n")
    
    try:
        import scrapy
        f.write(f"Scrapy imported successfully, version: {scrapy.__version__}\n")
    except ImportError as e:
        f.write(f"Error importing Scrapy: {e}\n")
        
    try:
        from scrapy.crawler import CrawlerProcess
        f.write("CrawlerProcess imported successfully\n")
    except ImportError as e:
        f.write(f"Error importing CrawlerProcess: {e}\n")

    f.write("Script completed successfully\n") 