/**
 * Sentiment analysis functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set up the analyze button
    const analyzeBtn = document.getElementById('analyze-btn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeSentiment);
    }
});

// Analyze sentiment of text
function analyzeSentiment() {
    const textArea = document.getElementById('sentiment-text');
    const analyzeLoader = document.getElementById('analyze-loader');
    const resultDiv = document.getElementById('result');
    
    if (!textArea || !analyzeLoader || !resultDiv) return;
    
    const text = textArea.value.trim();
    
    if (!text) {
        alert('Please enter some text to analyze.');
        return;
    }
    
    analyzeLoader.style.display = 'block';
    resultDiv.style.display = 'none';
    
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            analyzeLoader.style.display = 'none';
            resultDiv.style.display = 'block';
            
            if (data.result) {
                const sentiment = data.result.sentiment;
                const score = data.result.score;
                
                let sentimentColor = '';
                if (sentiment === 'positive') {
                    sentimentColor = '#28a745';
                } else if (sentiment === 'negative') {
                    sentimentColor = '#dc3545';
                } else {
                    sentimentColor = '#ffc107';
                }
                
                resultDiv.innerHTML = `
                    <h3>Sentiment Analysis Result</h3>
                    <p>Sentiment: <strong style="color: ${sentimentColor}">${sentiment}</strong></p>
                    <p>Score: <strong>${score}</strong></p>
                    <p><small>Analyzed at: ${new Date().toLocaleString()}</small></p>
                `;
            } else {
                resultDiv.innerHTML = '<p>Error analyzing sentiment.</p>';
            }
        })
        .catch(error => {
            analyzeLoader.style.display = 'none';
            console.error('Error analyzing sentiment:', error);
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '<p>Error analyzing sentiment. Please try again later.</p>';
        });
} 