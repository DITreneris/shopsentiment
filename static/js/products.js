/**
 * Products JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Fetch products when page loads
    fetchProducts();
});

// Fetch products from the API
function fetchProducts() {
    const productsContainer = document.getElementById('products-container');
    const productsLoader = document.getElementById('products-loader');
    
    if (!productsContainer || !productsLoader) return;
    
    productsLoader.style.display = 'block';
    
    fetch('/api/products')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            productsLoader.style.display = 'none';
            
            if (data.products && data.products.length > 0) {
                let productsHTML = '';
                
                data.products.forEach(product => {
                    productsHTML += `
                        <div class="product-card ${product.sentiment}">
                            <a href="/product/${product.id}">
                                <h3>${product.name} <span class="badge ${product.sentiment}">${product.sentiment}</span></h3>
                                <p>ID: ${product.id}</p>
                                <p>Reviews: ${product.reviews_count}</p>
                                <p>${product.description.substring(0, 100)}...</p>
                                <div class="view-details">View Details →</div>
                            </a>
                        </div>
                    `;
                });
                
                productsContainer.innerHTML = productsHTML;
            } else {
                productsContainer.innerHTML = '<p>No products found.</p>';
            }
        })
        .catch(error => {
            productsLoader.style.display = 'none';
            console.error('Error fetching products:', error);
            showError('Error loading products. Please try again later.', productsContainer);
        });
} 