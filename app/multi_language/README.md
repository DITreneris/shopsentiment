# Multi-Language Support and Continuous Improvement Pipeline

This module implements multi-language sentiment analysis support for the Shop Sentiment platform, including a continuous improvement pipeline that automatically monitors and enhances model performance across different languages.

## Directory Structure

```
app/multi_language/
├── evaluation/             # Evaluation metrics and tools
│   ├── metrics/            # Metrics for each language
│   └── accuracy_measurement.py  # Code for measuring model accuracy
├── pipeline/               # Continuous improvement pipeline 
│   ├── continuous_improvement.py # Main pipeline implementation
│   ├── test_pipeline.py    # Test script for the pipeline
│   └── standalone_test.py  # Standalone test that doesn't require app imports
├── models/                 # Language-specific models
│   ├── en/                 # English model
│   ├── fr/                 # French model
│   ├── de/                 # German model
│   ├── es/                 # Spanish model
│   └── it/                 # Italian model
├── lexicons/               # Language-specific sentiment lexicons
├── setup_continuous_improvement.py  # Setup script for the pipeline
├── run_improvement_pipeline.py      # Script to run the pipeline
├── setup_and_run.bat       # Windows batch file to set up and run the pipeline
└── setup_and_run.sh        # Unix/Linux/Mac shell script to set up and run the pipeline
```

## Supported Languages

- English (en)
- French (fr)
- German (de)
- Spanish (es)
- Italian (it)

## Getting Started

### Windows

```
cd app/multi_language
setup_and_run.bat
```

### Unix/Linux/Mac

```
cd app/multi_language
chmod +x setup_and_run.sh
./setup_and_run.sh
```

## Manual Setup and Execution

1. Set up the continuous improvement pipeline:
   ```
   python app/multi_language/setup_continuous_improvement.py
   ```

2. Test the pipeline:
   ```
   python app/multi_language/pipeline/standalone_test.py
   ```

3. Run the pipeline:
   ```
   python app/multi_language/run_improvement_pipeline.py [--mode {full|collect|report}]
   ```

## Scheduling the Pipeline

The pipeline can be scheduled to run automatically:

### Windows

```
schtasks /create /tn "ShopSentiment_MultiLanguage_Pipeline" /tr "python %cd%\app\multi_language\run_improvement_pipeline.py" /sc WEEKLY /d MON /st 00:00
```

### Unix/Linux/Mac (cron)

```
0 0 * * 1 cd /path/to/project && python app/multi_language/run_improvement_pipeline.py
```

## Pipeline Features

- **Metrics Collection**: Collects performance metrics for all supported languages
- **Underperforming Language Detection**: Identifies languages that need improvement based on thresholds
- **Recommendation Generation**: Suggests improvements for underperforming languages
- **Model Retraining**: Automatically triggers retraining for underperforming models
- **Lexicon Updates**: Updates sentiment lexicons based on performance data
- **Performance Reporting**: Generates comprehensive reports with cross-language comparisons

## Performance Thresholds

Current performance thresholds:
- Accuracy: 0.85
- F1 Score: 0.80
- Precision: 0.80
- Recall: 0.75

## Adding a New Language

To add support for a new language:

1. Update the `SUPPORTED_LANGUAGES` and `LANGUAGE_NAMES` constants in:
   - `app/multi_language/pipeline/continuous_improvement.py`
   - `app/multi_language/setup_continuous_improvement.py`

2. Run the setup script again to create the necessary directory and files:
   ```
   python app/multi_language/setup_continuous_improvement.py
   ```

3. Add language-specific preprocessing in the sentiment analysis models

4. Create a language-specific lexicon with sentiment terms 