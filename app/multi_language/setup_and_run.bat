@echo off
echo Shop Sentiment - Multi-Language Continuous Improvement Pipeline
echo ==============================================================
echo.

REM Change to the project root directory
cd ..\..\

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in the PATH
    echo Please install Python 3.8 or later and try again
    goto :eof
)

REM Check if required packages are installed
python -c "import numpy, pandas, schedule" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing required packages...
    pip install numpy pandas schedule
)

echo Setting up continuous improvement pipeline...
python app/multi_language/setup_continuous_improvement.py
if %errorlevel% neq 0 (
    echo Error: Failed to set up the continuous improvement pipeline
    goto :eof
)

echo.
echo Running a test of the pipeline...
python app/multi_language/pipeline/test_pipeline.py
if %errorlevel% neq 0 (
    echo Error: Pipeline test failed
    goto :eof
)

echo.
echo Setup completed successfully!
echo.
echo To run the pipeline manually:
echo   python app/multi_language/run_improvement_pipeline.py
echo.
echo To schedule the pipeline as a Windows task:
echo   schtasks /create /tn "ShopSentiment_MultiLanguage_Pipeline" /tr "python %cd%\app\multi_language\run_improvement_pipeline.py" /sc WEEKLY /d MON /st 00:00
echo.

REM Prompt the user to schedule the task
set /p schedule_task=Do you want to schedule the pipeline to run weekly (Y/N)? 
if /i "%schedule_task%"=="Y" (
    echo Scheduling weekly pipeline execution...
    schtasks /create /tn "ShopSentiment_MultiLanguage_Pipeline" /tr "python %cd%\app\multi_language\run_improvement_pipeline.py" /sc WEEKLY /d MON /st 00:00
    if %errorlevel% neq 0 (
        echo Failed to schedule the task. You may need administrator privileges.
    ) else (
        echo Task scheduled successfully!
    )
)

echo.
pause 