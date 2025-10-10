// API Configuration
const API_BASE_URL = 'http://localhost:5001/api';

// State management
let currentUser = null;
let authToken = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    // Check for saved login
    const savedToken = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('currentUser');
    
    if (savedToken && savedUser) {
        authToken = savedToken;
        currentUser = JSON.parse(savedUser);
        updateAuthUI();
    }
});

// Authentication functions
async function login(event) {
    event.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            
            // Save to localStorage
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            updateAuthUI();
            closeModal('loginModal');
            showSuccess('Login successful!');
        } else {
            showError('loginError', data.error || 'Login failed');
        }
    } catch (error) {
        showError('loginError', 'Network error. Please try again.');
    }
}

async function register(event) {
    event.preventDefault();
    
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const phone = document.getElementById('registerPhone').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, phone, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            
            // Save to localStorage
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            updateAuthUI();
            closeModal('registerModal');
            showSuccess('Registration successful!');
        } else {
            showError('registerError', data.error || 'Registration failed');
        }
    } catch (error) {
        showError('registerError', 'Network error. Please try again.');
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    updateAuthUI();
    showSuccess('Logged out successfully!');
}

function updateAuthUI() {
    const authButtons = document.getElementById('authButtons');
    const userInfo = document.getElementById('userInfo');
    const userName = document.getElementById('userName');
    
    if (currentUser) {
        authButtons.classList.add('hidden');
        userInfo.classList.remove('hidden');
        userName.textContent = `Welcome, ${currentUser.name}`;
    } else {
        authButtons.classList.remove('hidden');
        userInfo.classList.add('hidden');
    }
}

// Modal functions
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    clearErrors();
}

function openLoginModal() {
    openModal('loginModal');
}

function openRegisterModal() {
    openModal('registerModal');
}

function openLostItemModal() {
    if (!authToken) {
        alert('Please login first to report a lost item.');
        openLoginModal();
        return;
    }
    openModal('lostItemModal');
}

function openFoundItemModal() {
    if (!authToken) {
        alert('Please login first to report a found item.');
        openLoginModal();
        return;
    }
    openModal('foundItemModal');
}

// Close modals when clicking outside
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Item reporting functions
async function reportLostItem(event) {
    event.preventDefault();
    
    if (!authToken) {
        alert('Please login first.');
        return;
    }
    
    const formData = new FormData();
    formData.append('title', document.getElementById('lostTitle').value);
    formData.append('description', document.getElementById('lostDescription').value);
    formData.append('category', document.getElementById('lostCategory').value);
    formData.append('color', document.getElementById('lostColor').value || '');
    formData.append('brand', document.getElementById('lostBrand').value || '');
    formData.append('lost_location', document.getElementById('lostLocation').value);
    formData.append('lost_date', document.getElementById('lostDate').value);
    formData.append('reward_amount', document.getElementById('lostReward').value || '0');
    const imageInput = document.getElementById('lostImage');
    if (imageInput && imageInput.files && imageInput.files[0]) {
        formData.append('image', imageInput.files[0]);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/lost-items`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            closeModal('lostItemModal');
            showSuccess(`Lost item reported successfully! Found ${data.potential_matches} potential matches.`);
            // Reset form
            document.querySelector('#lostItemModal form').reset();
        } else {
            showError('lostItemError', data.error || 'Failed to report lost item');
        }
    } catch (error) {
        showError('lostItemError', 'Network error. Please try again.');
    }
}

async function reportFoundItem(event) {
    event.preventDefault();
    
    if (!authToken) {
        alert('Please login first.');
        return;
    }
    
    const formData = new FormData();
    formData.append('title', document.getElementById('foundTitle').value);
    formData.append('description', document.getElementById('foundDescription').value);
    formData.append('category', document.getElementById('foundCategory').value);
    formData.append('color', document.getElementById('foundColor').value || '');
    formData.append('brand', document.getElementById('foundBrand').value || '');
    formData.append('found_location', document.getElementById('foundLocation').value);
    formData.append('found_date', document.getElementById('foundDate').value);
    formData.append('condition', document.getElementById('foundCondition').value);
    const imageInput = document.getElementById('foundImage');
    if (imageInput && imageInput.files && imageInput.files[0]) {
        formData.append('image', imageInput.files[0]);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/found-items`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            closeModal('foundItemModal');
            showSuccess(`Found item reported successfully! Found ${data.potential_matches} potential matches.`);
            // Reset form
            document.querySelector('#foundItemModal form').reset();
        } else {
            showError('foundItemError', data.error || 'Failed to report found item');
        }
    } catch (error) {
        showError('foundItemError', 'Network error. Please try again.');
    }
}

// Search functions
async function searchItems(event) {
    event.preventDefault();
    
    const query = document.getElementById('searchQuery').value;
    const type = document.getElementById('searchType').value;
    
    if (!query.trim()) {
        alert('Please enter a search query.');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/search?query=${encodeURIComponent(query)}&type=${type}&limit=20`);
        const data = await response.json();
        
        if (response.ok) {
            displaySearchResults(data.results);
        } else {
            showError('searchError', data.error || 'Search failed');
        }
    } catch (error) {
        showError('searchError', 'Network error. Please try again.');
    }
}

function displaySearchResults(results) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = '<p>No items found matching your search.</p>';
        return;
    }
    
    let html = `<h3>Search Results (${results.length} items found)</h3>`;
    
    results.forEach(item => {
        const itemType = item.type === 'lost' ? '📢 Lost Item' : '🎯 Found Item';
        const itemTypeClass = item.type === 'lost' ? 'lost-item' : 'found-item';
        const similarityPercent = Math.round(item.similarity * 100);
        
        const actions = item.type === 'found' ? `<div class="item-actions"><button class="btn btn-primary" onclick="openClaimModal(${item.id})">Claim this item</button></div>` : '';
        
        html += `
            <div class="item-card ${itemTypeClass}">
                <h4>${itemType}: ${item.title}</h4>
                <p><strong>Description:</strong> ${item.description}</p>
                <div class="item-meta">
                    <span><strong>Category:</strong> ${item.category}</span>
                    ${item.color ? `| <strong>Color:</strong> ${item.color}` : ''}
                    ${item.brand ? `| <strong>Brand:</strong> ${item.brand}` : ''}
                </div>
                <div class="item-meta">
                    <span><strong>Location:</strong> ${item.type === 'lost' ? item.lost_location : item.found_location}</span>
                    | <span><strong>Date:</strong> ${item.type === 'lost' ? item.lost_date : item.found_date}</span>
                    ${item.type === 'found' ? `| <strong>Condition:</strong> ${item.condition}` : ''}
                    ${item.type === 'lost' && item.reward_amount > 0 ? `| <strong>Reward:</strong> $${item.reward_amount}` : ''}
                </div>
                <div class="similarity-score">Match: ${similarityPercent}%</div>
                ${actions}
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
}

// Claim flow state
let claimContext = {
    targetFoundItemId: null,
    claimId: null,
    selectedOptionId: null,
};

function openClaimModal(foundItemId) {
    if (!authToken) {
        alert('Please login first to claim an item.');
        openLoginModal();
        return;
    }
    claimContext = { targetFoundItemId: foundItemId, claimId: null, selectedOptionId: null };
    document.getElementById('claimDescription').value = '';
    document.getElementById('claimInitError').innerHTML = '';
    document.getElementById('claimVerifyError').innerHTML = '';
    document.getElementById('claimStepDescribe').classList.remove('hidden');
    document.getElementById('claimStepChallenge').classList.add('hidden');
    openModal('claimModal');
}

async function initiateClaim() {
    const desc = document.getElementById('claimDescription').value;
    try {
        const response = await fetch(`${API_BASE_URL}/claims/initiate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                target_type: 'found',
                target_item_id: claimContext.targetFoundItemId,
                claimant_description: desc
            })
        });
        const data = await response.json();
        if (!response.ok) {
            showError('claimInitError', data.error || 'Failed to initiate claim');
            return;
        }
        claimContext.claimId = data.claim.id;
        renderClaimChallenge(data.claim);
    } catch (e) {
        showError('claimInitError', 'Network error. Please try again.');
    }
}

function renderClaimChallenge(claim) {
    document.getElementById('claimStepDescribe').classList.add('hidden');
    document.getElementById('claimStepChallenge').classList.remove('hidden');
    document.getElementById('claimQuestionText').textContent = claim.question_text;
    const container = document.getElementById('claimOptions');
    container.innerHTML = '';
    claim.options.forEach((opt, idx) => {
        const wrapper = document.createElement('div');
        wrapper.style.border = '1px solid #ddd';
        wrapper.style.borderRadius = '6px';
        wrapper.style.padding = '6px';
        wrapper.style.textAlign = 'center';
        wrapper.innerHTML = `
            <img src="${opt.image_url}" alt="${opt.label}" style="width:100%;height:120px;object-fit:cover;border-radius:4px;" />
            <div style="margin-top:6px;">
                <input type="radio" name="claimOption" id="claimOpt_${opt.id}" value="${opt.id}" />
                <label for="claimOpt_${opt.id}">${opt.label}</label>
            </div>
        `;
        container.appendChild(wrapper);
    });
    container.addEventListener('change', (e) => {
        if (e.target && e.target.name === 'claimOption') {
            claimContext.selectedOptionId = e.target.value;
        }
    });
}

async function verifyClaim() {
    if (!claimContext.claimId || !claimContext.selectedOptionId) {
        showError('claimVerifyError', 'Please select an option.');
        return;
    }
    try {
        const response = await fetch(`${API_BASE_URL}/claims/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                claim_id: claimContext.claimId,
                selected_option_id: claimContext.selectedOptionId
            })
        });
        const data = await response.json();
        if (!response.ok) {
            showError('claimVerifyError', data.error || 'Verification failed');
            return;
        }
        if (data.result === 'correct') {
            showSuccess('Verification passed! We have recorded your claim.');
            closeModal('claimModal');
        } else {
            showError('claimVerifyError', 'That was not correct. Please try again or provide a better description.');
        }
    } catch (e) {
        showError('claimVerifyError', 'Network error. Please try again.');
    }
}

// Utility functions
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="error">${message}</div>`;
}

function showSuccess(message) {
    // Create a temporary success message
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.textContent = message;
    successDiv.style.position = 'fixed';
    successDiv.style.top = '20px';
    successDiv.style.right = '20px';
    successDiv.style.zIndex = '9999';
    successDiv.style.maxWidth = '300px';
    
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        document.body.removeChild(successDiv);
    }, 5000);
}

function clearErrors() {
    const errorElements = ['loginError', 'registerError', 'lostItemError', 'foundItemError'];
    errorElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.innerHTML = '';
        }
    });
}

// Set default date to today
function setDefaultDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('lostDate').value = today;
    document.getElementById('foundDate').value = today;
}

// Set default dates when modals open
document.addEventListener('DOMContentLoaded', function() {
    setDefaultDate();
});