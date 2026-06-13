// App state
let activeSessionId = null;
let activeWidgets = 0;

const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const btnSend = document.getElementById('btn-send');
const sandboxContent = document.getElementById('sandbox-content');
const emptyState = document.getElementById('empty-state');
const widgetBadge = document.getElementById('widget-badge');
const sessionsListContainer = document.getElementById('sessions-list');
const btnNewChat = document.getElementById('btn-new-chat');

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

// Session Management REST Calls
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        if (!response.ok) throw new Error("Failed to list sessions");
        const sessions = await response.json();
        
        sessionsListContainer.innerHTML = '';
        if (sessions.length === 0) {
            sessionsListContainer.innerHTML = '<div class="session-loading">No conversations yet</div>';
            await createNewSession();
            return;
        }
        
        sessions.forEach(s => {
            const item = document.createElement('div');
            item.className = `session-item ${s.id === activeSessionId ? 'active' : ''}`;
            item.dataset.id = s.id;
            
            const details = document.createElement('div');
            details.className = 'session-details';
            details.onclick = () => selectSession(s.id);
            
            const name = document.createElement('span');
            name.className = 'session-name';
            name.textContent = `Session: ${s.id.substring(0, 8)}`;
            
            const time = document.createElement('span');
            time.className = 'session-time';
            if (s.create_time) {
                const date = new Date(s.create_time);
                time.textContent = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + " " + date.toLocaleDateString();
            } else {
                time.textContent = "unknown";
            }
            
            details.appendChild(name);
            details.appendChild(time);
            
            const btnDelete = document.createElement('button');
            btnDelete.className = 'btn-delete-session';
            btnDelete.innerHTML = '🗑️';
            btnDelete.onclick = (e) => {
                e.stopPropagation();
                deleteSession(s.id);
            };
            
            item.appendChild(details);
            item.appendChild(btnDelete);
            sessionsListContainer.appendChild(item);
        });
        
        if (!activeSessionId && sessions.length > 0) {
            selectSession(sessions[0].id);
        }
    } catch (err) {
        console.error("Load sessions error:", err);
        sessionsListContainer.innerHTML = '<div class="session-loading">Error loading conversations</div>';
    }
}

async function createNewSession() {
    try {
        const response = await fetch('/api/sessions', { method: 'POST' });
        if (!response.ok) throw new Error("Failed to create new session");
        const data = await response.json();
        activeSessionId = data.id;
        
        await loadSessions();
        selectSession(data.id);
    } catch (err) {
        console.error("Create session error:", err);
    }
}

async function deleteSession(id) {
    try {
        const response = await fetch(`/api/sessions/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error("Failed to delete session");
        
        if (activeSessionId === id) {
            activeSessionId = null;
        }
        await loadSessions();
    } catch (err) {
        console.error("Delete session error:", err);
    }
}

async function selectSession(id) {
    activeSessionId = id;
    document.getElementById('session-display').textContent = `Session ID: ${id.substring(0, 8)}`;
    
    // Highlight active sidebar item
    const items = document.querySelectorAll('.session-item');
    items.forEach(item => {
        if (item.dataset.id === id) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Clear chat panes & sandboxes
    chatMessages.innerHTML = '';
    sandboxContent.innerHTML = '';
    activeWidgets = 0;
    widgetBadge.textContent = '0 Active Widgets';
    if (emptyState) {
        emptyState.style.display = 'flex';
    }
    
    // Show default initial welcome
    const welcome = document.createElement('div');
    welcome.className = 'message system';
    welcome.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="content">
            Welcome to the Circana Pilot multi-agent orchestrator. I can help coordinate your pricing analysis, cohort sizing, and campaign activations. Try asking:
            <div class="suggestions">
                <button onclick="suggest('Identify pricing opportunities with shopper attrition in the Soft Drinks category.')">🔍 Identify soft drink attrition opportunities</button>
            </div>
        </div>
    `;
    chatMessages.appendChild(welcome);
    
    try {
        const response = await fetch(`/api/sessions/${id}`);
        if (!response.ok) throw new Error("Failed to load history");
        const history = await response.json();
        
        if (history.length > 0) {
            chatMessages.innerHTML = ''; // wipe welcome message
            history.forEach(item => {
                // If it is a tech/action log like "Clicked action: ...", we can render it as system status or skip
                // Let's render as chat messages
                const role = item.role === 'model' || item.role === 'assistant' ? 'agent' : 'user';
                appendMessage(role, item.text);
                
                if (item.widgets && item.widgets.length > 0) {
                    item.widgets.forEach(renderA2UIWidget);
                }
            });
        }
    } catch (err) {
        console.error("Load history error:", err);
        appendMessage('system', `Error loading session history: ${err.message}`);
    }
}

// User text query input submission
async function submitUserMessage(message) {
    if (!message.trim() || !activeSessionId) return;
    
    appendMessage('user', message);
    userInput.value = '';
    
    // Disable inputs
    userInput.disabled = true;
    btnSend.disabled = true;
    setIndicator('supervisor');
    
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
            body: JSON.stringify({ message: message, session_id: activeSessionId })
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
    if (!activeSessionId) return;
    
    let turnDescription = `User Action: ${action.actionId}`;
    let userPromptText = "";
    
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
    
    userInput.disabled = true;
    btnSend.disabled = true;
    
    try {
        const response = await fetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action, session_id: activeSessionId })
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

// Listen for iframe callbacks
window.addEventListener('message', (event) => {
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

btnNewChat.addEventListener('click', createNewSession);

// Suggestions shortcut
window.suggest = function(text) {
    userInput.value = text;
    submitUserMessage(text);
};

// Initial Load
loadSessions();
