/**
 * Product detail page functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Fetch and display sentiment data
    fetchSentimentData(PRODUCT_ID);
    
    // Fetch and display reviews
    fetchReviews(PRODUCT_ID);
});

function fetchSentimentData(productId) {
    fetch(`/api/products/${productId}/sentiment`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.sentiment) {
                const sentiment = data.sentiment;
                const scoreElement = document.getElementById('sentiment-score');
                
                if (scoreElement) {
                    scoreElement.textContent = sentiment.score.toFixed(2) + ' / 1.0';
                }
                
                setTimeout(() => {
                    // Update the bars with animation
                    updateSentimentBar('positive', sentiment.positive);
                    updateSentimentBar('neutral', sentiment.neutral);
                    updateSentimentBar('negative', sentiment.negative);
                }, 300);
            }
        })
        .catch(error => {
            console.error('Error fetching sentiment data:', error);
            const sentimentSummary = document.querySelector('.sentiment-summary');
            if (sentimentSummary) {
                showError('Error loading sentiment data. Please try again later.', sentimentSummary);
            }
        });
}

function updateSentimentBar(type, percentage) {
    const bar = document.getElementById(`${type}-bar`);
    const percentageElement = document.getElementById(`${type}-percentage`);
    
    if (bar) {
        bar.style.width = percentage + '%';
    }
    
    if (percentageElement) {
        percentageElement.textContent = percentage + '%';
    }
}

function fetchReviews(productId) {
    const reviewsContainer = document.getElementById('reviews-container');
    const reviewsLoader = document.getElementById('reviews-loader');
    
    if (!reviewsContainer || !reviewsLoader) return;
    
    reviewsLoader.style.display = 'block';
    
    fetch(`/api/products/${productId}/reviews`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            reviewsLoader.style.display = 'none';
            
            if (data.reviews && data.reviews.length > 0) {
                let reviewsHTML = '';
                
                data.reviews.forEach(review => {
                    // Generate star rating HTML
                    const ratingStars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
                    
                    reviewsHTML += `
                        <div class="review-card">
                            <div class="review-header">
                                <div class="review-author">${review.author}</div>
                                <div class="review-rating">${ratingStars}</div>
                            </div>
                            <div class="review-text">${review.text}</div>
                            <div class="review-meta">
                                <span class="review-date">${formatDate(review.date)}</span> | 
                                Sentiment: <span class="review-sentiment ${review.sentiment}">${review.sentiment}</span>
                            </div>
                        </div>
                    `;
                });
                
                reviewsContainer.innerHTML = reviewsHTML;
            } else {
                reviewsContainer.innerHTML = '<p>No reviews available for this product.</p>';
            }
        })
        .catch(error => {
            reviewsLoader.style.display = 'none';
            console.error('Error fetching reviews:', error);
            showError('Error loading reviews. Please try again later.', reviewsContainer);
        });
} 