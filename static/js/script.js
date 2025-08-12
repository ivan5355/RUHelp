const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const loading = document.getElementById('loading');

function askExample(query) {
    chatInput.value = query;
    chatForm.dispatchEvent(new Event('submit'));
}

function addMessage(content, isUser = false, sources = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    
    // Format the message content
    let formattedContent = formatMessage(content);
    // Inline citation linkifier disabled per request; using bottom sources list instead
    
    // Add sources directly to the response if they exist
    if (!isUser && sources && sources.length > 0) {
        formattedContent += '<br><br><strong>Sources:</strong><ul>';
        sources.forEach(source => {
            formattedContent += `<li><a href="${source.link}" target="_blank">${source.title}</a></li>`;
        });
        formattedContent += '</ul>';
    }
    
    bubbleDiv.innerHTML = formattedContent;
    messageDiv.appendChild(bubbleDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(text) {

    // Basic formatting for better readability
    return text
        
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        
        .replace(/\n/g, '<br>')
        
        .replace(/(\d{2}:\d{3}:\d{3})/g, '<strong>$1</strong>'); 
}

// show the loading spinners
function showLoading() {
    loading.style.display = 'block';
    sendButton.disabled = true;
}

// hide the loading spinners
function hideLoading() {
    loading.style.display = 'none';
    sendButton.disabled = false;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const query = chatInput.value.trim();
    if (!query) return;
    
    addMessage(query, true);
    chatInput.value = '';
    showLoading();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.sources && data.sources.length > 0) {
                
            } else {
                
            }
            addMessage(data.response, false, data.sources || []);
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', false);
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, I encountered a connection error. Please try again.', false);
    } finally {
        hideLoading();
        chatInput.focus();
    }
});

// Focus on input when page loads
chatInput.focus(); 