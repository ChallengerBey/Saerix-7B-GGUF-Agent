/**
 * Saerix - Web UI Frontend
 * WebSocket tabanlı agent chat
 */

class AgentChat {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.isStreaming = false;
        this.showTools = true;
        this.messageBuffer = '';
        this.currentToolCalls = [];
        this.autoScroll = true;
        
        this.initElements();
        this.bindEvents();
        this.loadFileTree();
        this.connect();
    }

    initElements() {
        this.elements = {
            messages: document.getElementById('messages'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            toolPanel: document.getElementById('toolPanel'),
            toolList: document.getElementById('toolList'),
            closeToolPanel: document.getElementById('closeToolPanel'),
            sidebar: document.getElementById('sidebar'),
            toggleSidebar: document.getElementById('toggleSidebar'),
            openSidebar: document.getElementById('openSidebar'),
            fileTree: document.getElementById('fileTree'),
            newChat: document.getElementById('newChat'),
            settingsBtn: document.getElementById('settingsBtn'),
            settingsModal: document.getElementById('settingsModal'),
            closeSettings: document.getElementById('closeSettings'),
            showToolsToggle: document.getElementById('showToolsToggle'),
            tempSlider: document.getElementById('tempSlider'),
            tempValue: document.getElementById('tempValue'),
            streamToggle: document.getElementById('streamToggle'),
        };
    }

    bindEvents() {
        // Send message
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.elements.messageInput.addEventListener('input', () => {
            const ta = this.elements.messageInput;
            ta.style.height = 'auto';
            ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
        });

        // Tool panel
        this.elements.closeToolPanel.addEventListener('click', () => this.toggleToolPanel(false));

        // Sidebar
        this.elements.toggleSidebar.addEventListener('click', () => this.toggleSidebar(false));
        this.elements.openSidebar.addEventListener('click', () => this.toggleSidebar(true));

        // New chat
        this.elements.newChat.addEventListener('click', () => this.newChat());

        // Settings
        this.elements.settingsBtn.addEventListener('click', () => this.openSettings());
        this.elements.closeSettings.addEventListener('click', () => this.closeSettings());
        this.elements.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.elements.settingsModal) this.closeSettings();
        });
        this.elements.showToolsToggle.addEventListener('change', (e) => {
            this.showTools = e.target.checked;
            if (!this.showTools) this.toggleToolPanel(false);
        });
        this.elements.tempSlider.addEventListener('input', (e) => {
            this.elements.tempValue.textContent = parseFloat(e.target.value).toFixed(1);
        });

        // Example buttons
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.elements.messageInput.value = btn.dataset.msg;
                this.elements.messageInput.dispatchEvent(new Event('input'));
                this.sendMessage();
            });
        });

        // Close sidebar on mobile when clicking main
        document.querySelector('.main').addEventListener('click', () => {
            if (window.innerWidth <= 768) this.toggleSidebar(false);
        });

        // Scroll detection for auto-scroll
        this.elements.messages.addEventListener('scroll', () => {
            const { scrollTop, scrollHeight, clientHeight } = this.elements.messages;
            this.autoScroll = scrollHeight - scrollTop - clientHeight < 50;
        });
    }

    async connect() {
        // Create new session via REST first
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: '__init__', session_id: null })
            });
            const data = await res.json();
            this.sessionId = data.session_id;
            console.log('[Chat] Session created:', this.sessionId);
        } catch (e) {
            console.error('[Chat] Session create failed:', e);
            this.sessionId = 'local-' + Date.now();
        }

        // Connect WebSocket
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${location.host}/ws/chat/${this.sessionId}`);
        
        this.ws.onopen = () => {
            console.log('[WS] Connected');
            this.setInputDisabled(false);
        };

        this.ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            this.handleWSMessage(msg);
        };

        this.ws.onclose = () => {
            console.log('[WS] Disconnected, reconnecting...');
            this.setInputDisabled(true);
            setTimeout(() => this.connect(), 2000);
        };

        this.ws.onerror = (err) => {
            console.error('[WS] Error:', err);
        };
    }

    handleWSMessage(msg) {
        switch (msg.type) {
            case 'token':
                this.appendToken(msg.content);
                break;
            case 'tool_call':
                this.addToolCall(msg.tool, msg.args);
                break;
            case 'tool_result':
                this.updateToolResult(msg.tool, msg.content);
                break;
            case 'done':
                this.finishStreaming(msg.response, msg.tool_calls);
                break;
            case 'error':
                this.showError(msg.message);
                this.finishStreaming('');
                break;
        }
    }

    sendMessage() {
        const text = this.elements.messageInput.value.trim();
        if (!text || this.isStreaming) return;

        this.elements.messageInput.value = '';
        this.elements.messageInput.style.height = 'auto';
        this.setInputDisabled(true);
        this.isStreaming = true;
        this.messageBuffer = '';
        this.currentToolCalls = [];

        // Remove welcome screen
        this.hideWelcome();

        // Add user message
        this.addMessage('user', text);

        // Show tool panel if enabled
        if (this.showTools) this.toggleToolPanel(true);

        // Send via WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'message', content: text }));
        } else {
            // Fallback to REST
            this.sendMessageREST(text);
        }
    }

    async sendMessageREST(text) {
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, session_id: this.sessionId })
            });
            const data = await res.json();
            this.finishStreaming(data.response, data.tool_calls);
        } catch (e) {
            this.showError('İstek başarısız: ' + e.message);
            this.finishStreaming('');
        }
    }

    addMessage(role, content) {
        const welcome = this.elements.messages.querySelector('.welcome');
        if (welcome) welcome.remove();

        const div = document.createElement('div');
        div.className = `message ${role}`;
        
        const avatar = role === 'user' ? '👤' : (role === 'tool' ? '🔧' : '🤖');
        const name = role === 'user' ? 'Sen' : (role === 'tool' ? 'Tool' : 'Agent');
        
        div.innerHTML = `
            <div class="avatar ${role}">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="name">${name}</span>
                </div>
                <div class="message-body">${this.escapeHtml(content)}</div>
            </div>
        `;

        this.elements.messages.appendChild(div);
        this.scrollToBottom();
        return div.querySelector('.message-body');
    }

    appendToken(token) {
        this.messageBuffer += token;
        
        // Find or create assistant message
        let lastMsg = this.elements.messages.lastElementChild;
        if (!lastMsg || !lastMsg.classList.contains('message') || !lastMsg.classList.contains('assistant')) {
            lastMsg = this.addMessage('assistant', '');
            lastMsg = lastMsg.parentElement;
        }
        
        const body = lastMsg.querySelector('.message-body');
        if (body) {
            body.textContent = this.messageBuffer;
            if (this.autoScroll) this.scrollToBottom();
        }
    }

    addToolCall(name, args) {
        if (!this.showTools) return;
        
        const id = `tool-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;
        const div = document.createElement('div');
        div.className = 'tool-item';
        div.id = id;
        div.innerHTML = `
            <div class="tool-item-header">
                <span class="tool-name">${this.escapeHtml(name)}</span>
                <span class="tool-status">⏳ Çalışıyor...</span>
            </div>
            <div class="tool-args">${this.escapeHtml(JSON.stringify(args, null, 2))}</div>
        `;
        this.elements.toolList.appendChild(div);
        this.elements.toolList.scrollTop = this.elements.toolList.scrollHeight;
    }

    updateToolResult(toolName, result) {
        if (!this.showTools) return;
        
        const items = this.elements.toolList.querySelectorAll('.tool-item');
        const item = Array.from(items).find(el => 
            el.querySelector('.tool-name').textContent === toolName && 
            el.querySelector('.tool-status').textContent === '⏳ Çalışıyor...'
        );
        
        if (item) {
            item.querySelector('.tool-status').textContent = '✓ Tamamlandı';
            const resultDiv = document.createElement('div');
            resultDiv.className = 'tool-result';
            resultDiv.textContent = result;
            item.appendChild(resultDiv);
        }
    }

    finishStreaming(finalResponse, toolCalls) {
        this.isStreaming = false;
        this.setInputDisabled(false);
        
        // Update final response if different
        if (finalResponse && finalResponse !== this.messageBuffer) {
            this.messageBuffer = finalResponse;
            const lastMsg = this.elements.messages.lastElementChild;
            if (lastMsg && lastMsg.classList.contains('assistant')) {
                const body = lastMsg.querySelector('.message-body');
                if (body) body.textContent = finalResponse;
            }
        }
        
        this.currentToolCalls = toolCalls || [];
        this.scrollToBottom();
    }

    hideWelcome() {
        const welcome = this.elements.messages.querySelector('.welcome');
        if (welcome) welcome.remove();
    }

    toggleToolPanel(show) {
        if (show) this.elements.toolPanel.classList.add('open');
        else this.elements.toolPanel.classList.remove('open');
    }

    toggleSidebar(open) {
        this.elements.sidebar.classList.toggle('open', open);
    }

    newChat() {
        if (confirm('Yeni sohbet başlatılsın mı? Mevcut geçmiş silinecek.')) {
            // Clear messages
            this.elements.messages.innerHTML = '';
            this.elements.toolList.innerHTML = '';
            this.toggleToolPanel(false);
            
            // Create new session
            this.connect();
            
            // Show welcome again
            this.showWelcome();
        }
    }

    showWelcome() {
        const welcome = document.createElement('div');
        welcome.className = 'welcome';
        welcome.innerHTML = `
            <div class="welcome-icon">🤖</div>
            <h3>Saerix Agent</h3>
            <p>Full-stack geliştirme, Siber Güvenlik, OSINT, Ağ Yönetimi, Teorik Fizik, UAV/İHA</p>
            <div class="examples">
                <button class="example-btn" data-msg="Projeyi listele">📂 Projeyi listele</button>
                <button class="example-btn" data-msg="src/main.py dosyasını oku">📄 Dosya oku</button>
                <button class="example-btn" data-msg="Port 8080'de ne var?">🔍 Port tara</button>
                <button class="example-btn" data-msg="example.com whois sorgula">🌐 WHOIS sorgula</button>
            </div>
        `;
        this.elements.messages.appendChild(welcome);
        
        // Re-bind example buttons
        welcome.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.elements.messageInput.value = btn.dataset.msg;
                this.elements.messageInput.dispatchEvent(new Event('input'));
                this.sendMessage();
            });
        });
    }

    openSettings() {
        this.elements.settingsModal.classList.add('open');
    }

    closeSettings() {
        this.elements.settingsModal.classList.remove('open');
    }

    setInputDisabled(disabled) {
        this.elements.messageInput.disabled = disabled;
        this.elements.sendBtn.disabled = disabled;
    }

    scrollToBottom() {
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    showError(msg) {
        const div = document.createElement('div');
        div.className = 'message assistant';
        div.innerHTML = `
            <div class="avatar assistant">⚠️</div>
            <div class="message-content">
                <div class="message-body" style="color: var(--danger);">Hata: ${this.escapeHtml(msg)}</div>
            </div>
        `;
        this.elements.messages.appendChild(div);
        this.scrollToBottom();
    }

    async loadFileTree() {
        try {
            const res = await fetch('/api/workspace/tree');
            const tree = await res.json();
            this.renderFileTree(tree, this.elements.fileTree);
        } catch (e) {
            console.error('[Chat] File tree load failed:', e);
            this.elements.fileTree.innerHTML = '<div class="loading">Yüklenemedi</div>';
        }
    }

    renderFileTree(node, container, isRoot = true) {
        if (isRoot) container.innerHTML = '';
        
        if (!node) return;
        
        const div = document.createElement('div');
        div.className = `tree-node ${node.type}`;
        
        if (node.type === 'dir') {
            div.innerHTML = `
                <span class="icon" data-toggle="true">▼</span>
                <span class="name">${this.escapeHtml(node.name)}</span>
            `;
            div.style.cursor = 'pointer';
            div.addEventListener('click', (e) => {
                if (e.target.classList.contains('icon')) {
                    const children = div.querySelector('.tree-children');
                    const icon = div.querySelector('.icon');
                    if (children) {
                        children.classList.toggle('collapsed');
                        icon.textContent = children.classList.contains('collapsed') ? '▶' : '▼';
                    }
                }
            });
            
            if (node.children && node.children.length > 0) {
                const childrenDiv = document.createElement('div');
                childrenDiv.className = 'tree-children';
                node.children.forEach(child => this.renderFileTree(child, childrenDiv, false));
                div.appendChild(childrenDiv);
            }
        } else {
            div.innerHTML = `<span class="icon">📄</span><span class="name">${this.escapeHtml(node.name)}</span>`;
            div.title = node.path;
            div.addEventListener('click', () => {
                this.elements.messageInput.value = `dosya oku ${node.path}`;
                this.elements.messageInput.dispatchEvent(new Event('input'));
                this.sendMessage();
                if (window.innerWidth <= 768) this.toggleSidebar(false);
            });
        }
        
        container.appendChild(div);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.chat = new AgentChat();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.chat && window.chat.ws) {
        window.chat.ws.close();
    }
});