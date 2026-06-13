// App state
const sessionId = "session-" + Math.random().toString(36).substring(2, 10);
document.getElementById('session-display').textContent = `Session ID: ${sessionId}`;

const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const btnSend = document.getElementById('btn-send');
const sandboxContent = document.getElementById('sandbox-content');
const emptyState = document.getElementById('empty-state');
const widgetBadge = document.getElementById('widget-badge');

let activeWidgets = 0;

// Indicators
const indicators = {
    supervisor: document.getElementById('indicator-supervisor'),
    pricing: document.getElementById('indicator-pricing'),
    activate: document.getElementById('indicator-activate'),
    loyalty: document.getElementById('indicator-loyalty')
};

function setIndicator(activeName) {
    Object.keys(indicators).forEach(name => {
        if (name === activeName) {
            indicators[name].classList.add('active');
        } else {
            indicators[name].classList.remove('active');
        }
    });
}

function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar';
    avatarDiv.textContent = role === 'user' ? '👤' : '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    contentDiv.textContent = text;
    
    msgDiv.appendChild(avatarDiv);
    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function renderA2UIWidget(widget) {
    if (emptyState) {
        emptyState.style.display = 'none';
    }
    
    // Find the WebFrameSrcdoc components
    let htmlContent = "";
    let surfaceId = widget.surfaceId || "A2UI Widget";
    
    // Traversal function to find htmlContent recursively
    function findHtmlContent(node) {
        if (!node || typeof node !== 'object') return;
        if (node.WebFrameSrcdoc && node.WebFrameSrcdoc.htmlContent && node.WebFrameSrcdoc.htmlContent.literalString) {
            htmlContent = node.WebFrameSrcdoc.htmlContent.literalString;
            return;
        }
        for (let key in node) {
            if (node.hasOwnProperty(key)) {
                const val = node[key];
                if (Array.isArray(val)) {
                    val.forEach(findHtmlContent);
                } else if (typeof val === 'object') {
                    findHtmlContent(val);
                }
            }
        }
    }
    
    findHtmlContent(widget);
    
    if (!htmlContent) {
        console.warn("No htmlContent found in widget data:", widget);
        return;
    }
    
    activeWidgets++;
    widgetBadge.textContent = `${activeWidgets} Active Widget${activeWidgets > 1 ? 's' : ''}`;
    
    const card = document.createElement('div');
    card.className = 'widget-card';
    
    const header = document.createElement('div');
    header.className = 'widget-card-header';
    
    const title = document.createElement('span');
    title.className = 'widget-title';
    title.textContent = surfaceId.replace(/-/g, ' ').toUpperCase();
    
    const badge = document.createElement('span');
    badge.className = 'widget-badge';
    badge.textContent = 'interactive';
    
    header.appendChild(title);
    header.appendChild(badge);
    
    const iframeContainer = document.createElement('div');
    iframeContainer.className = 'iframe-container';
    
    const iframe = document.createElement('iframe');
    iframe.srcdoc = htmlContent;
    
    iframeContainer.appendChild(iframe);
    card.appendChild(header);
    card.appendChild(iframeContainer);
    
    // Append to top of sandbox list
    sandboxContent.insertBefore(card, sandboxContent.firstChild);
}

// User text query input submission
async function submitUserMessage(message) {
    if (!message.trim()) return;
    
    appendMessage('user', message);
    userInput.value = '';
    
    // Disable inputs
    userInput.disabled = true;
    btnSend.disabled = true;
    setIndicator('supervisor');
    
    // Guess sub-agent route to light up indicators during latency!
    const msgLower = message.toLowerCase();
    if (msgLower.includes('pricing') || msgLower.includes('attrition') || msgLower.includes('soft drinks')) {
        setIndicator('pricing');
    } else if (msgLower.includes('loyalty') || msgLower.includes('campaign') || msgLower.includes('discount')) {
        setIndicator('loyalty');
    }
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, session_id: sessionId })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned HTTP ${response.status}`);
        }
        
        const data = await response.json();
        setIndicator('supervisor');
        
        if (data.text) {
            appendMessage('agent', data.text);
        }
        if (data.widgets && data.widgets.length > 0) {
            data.widgets.forEach(renderA2UIWidget);
        }
    } catch (err) {
        console.error("Chat Error:", err);
        appendMessage('system', `Error sending message: ${err.message}`);
        setIndicator('supervisor');
    } finally {
        userInput.disabled = false;
        btnSend.disabled = false;
        userInput.focus();
    }
}

// Interactive callback payload submission
async function submitInteractiveAction(action) {
    let turnDescription = `User Action: ${action.actionId}`;
    let userPromptText = "";
    
    // Translate action payloads into a user-friendly conversational bubble
    if (action.actionId === 'product_selected') {
        userPromptText = `Selected product: "${action.payload.product}". Sizing the cohort...`;
        setIndicator('activate');
    } else if (action.actionId === 'btn_activate') {
        const partners = action.payload.partners ? action.payload.partners.join(', ') : 'None';
        userPromptText = `Exporting cohort segment to: ${partners}`;
        setIndicator('activate');
    } else if (action.actionId === 'btn_launch_campaign') {
        userPromptText = `Launching personalized campaign for ${action.payload.product} (${action.payload.discount_pct}% discount, ${action.payload.points_mult}x multiplier)`;
        setIndicator('loyalty');
    } else {
        userPromptText = `Initiating A2UI callback action: ${action.actionId}`;
    }
    
    appendMessage('user', userPromptText);
    
    // Disable inputs
    userInput.disabled = true;
    btnSend.disabled = true;
    
    try {
        const response = await fetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action, session_id: sessionId })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned HTTP ${response.status}`);
        }
        
        const data = await response.json();
        setIndicator('supervisor');
        
        if (data.text) {
            appendMessage('agent', data.text);
        }
        if (data.widgets && data.widgets.length > 0) {
            data.widgets.forEach(renderA2UIWidget);
        }
    } catch (err) {
        console.error("Action Callback Error:", err);
        appendMessage('system', `Error executing callback action: ${err.message}`);
        setIndicator('supervisor');
    } finally {
        userInput.disabled = false;
        btnSend.disabled = false;
    }
}

// Listen for messages from within the rendered iFrames
window.addEventListener('message', (event) => {
    // Only accept messages that are of USER_ACTION type
    if (event.data && event.data.type === 'USER_ACTION') {
        console.log("Captured USER_ACTION callback from widget:", event.data);
        submitInteractiveAction(event.data);
    }
});

// Input bindings
btnSend.addEventListener('click', () => submitUserMessage(userInput.value));
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        submitUserMessage(userInput.value);
    }
});

// Suggestions shortcut
window.suggest = function(text) {
    userInput.value = text;
    submitUserMessage(text);
};
