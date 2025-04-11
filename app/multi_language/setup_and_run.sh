#!/bin/bash

echo "Shop Sentiment - Multi-Language Continuous Improvement Pipeline"
echo "=============================================================="
echo ""

# Change to the project root directory
cd $(dirname "$0")/../..

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed"
    echo "Please install Python 3.8 or later and try again"
    exit 1
fi

# Check if required packages are installed
if ! python3 -c "import numpy, pandas, schedule" &> /dev/null; then
    echo "Installing required packages..."
    pip3 install numpy pandas schedule
fi

echo "Setting up continuous improvement pipeline..."
python3 app/multi_language/setup_continuous_improvement.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to set up the continuous improvement pipeline"
    exit 1
fi

echo ""
echo "Running a test of the pipeline..."
python3 app/multi_language/pipeline/test_pipeline.py
if [ $? -ne 0 ]; then
    echo "Error: Pipeline test failed"
    exit 1
fi

echo ""
echo "Setup completed successfully!"
echo ""
echo "To run the pipeline manually:"
echo "  python3 app/multi_language/run_improvement_pipeline.py"
echo ""
echo "To schedule the pipeline as a cron job:"
echo "  Add the following line to crontab (crontab -e):"
echo "  0 0 * * 1 cd $(pwd) && python3 app/multi_language/run_improvement_pipeline.py"
echo ""

# Prompt the user to schedule a cron job
read -p "Do you want to schedule the pipeline to run weekly (Y/N)? " schedule_job
if [[ "$schedule_job" =~ ^[Yy]$ ]]; then
    echo "Scheduling weekly pipeline execution..."
    
    # Create a temporary file with the existing crontab contents
    crontab -l > temp_crontab 2>/dev/null
    
    # Add our cron job
    echo "# Shop Sentiment Multi-Language Pipeline - runs every Monday at midnight" >> temp_crontab
    echo "0 0 * * 1 cd $(pwd) && python3 app/multi_language/run_improvement_pipeline.py" >> temp_crontab
    
    # Install the new crontab
    crontab temp_crontab
    if [ $? -ne 0 ]; then
        echo "Failed to schedule the cron job."
    else
        echo "Cron job scheduled successfully!"
    fi
    
    # Remove the temporary file
    rm temp_crontab
fi

echo "" 