/* sovereign-widget.js */
(function() {
    const host = document.createElement('div');
    host.id = 'sov-mech-root';
    document.body.appendChild(host);

    const shadow = host.attachShadow({ mode: 'open' });

    // 2026 Glassmorphism Design
    shadow.innerHTML = `
        <style>
            #chat-trigger {
                position: fixed; bottom: 20px; right: 20px;
                width: 60px; height: 60px; border-radius: 50%;
                background: linear-gradient(135deg, #007bff, #00c6ff);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                cursor: pointer; display: flex; align-items: center; justify-content: center;
                transition: transform 0.3s; z-index: 9999;
            }
            #chat-trigger:hover { transform: scale(1.1) rotate(5deg); }
            #chat-window {
                position: fixed; bottom: 90px; right: 20px;
                width: 350px; height: 500px; background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px); border-radius: 20px;
                display: none; flex-direction: column; overflow: hidden;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.3);
                z-index: 9999; font-family: sans-serif;
            }
            #messages { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
            .msg { padding: 8px 12px; border-radius: 12px; max-width: 80%; font-size: 14px; }
            .ai { background: #f0f2f5; align-self: flex-start; }
            .user { background: #007bff; color: white; align-self: flex-end; }
            input { border: none; padding: 15px; background: #fff; outline: none; border-top: 1px solid #eee; }
        </style>

        <div id="chat-window">
            <div id="messages"></div>
            <input type="text" id="chat-input" placeholder="Ask Mechanica...">
        </div>
        <div id="chat-trigger">🤖</div>
    `;

    const trigger = shadow.querySelector('#chat-trigger');
    const window = shadow.querySelector('#chat-window');
    const input = shadow.querySelector('#chat-input');
    const msgBox = shadow.querySelector('#messages');

    trigger.onclick = () => { window.style.display = window.style.display === 'flex' ? 'none' : 'flex'; };

    // WebSocket Logic via Relay
    // Get configuration from attributes on the script tag
    const scriptTag = document.querySelector('script[src*="sovereign-widget.js"]');
    const clientId = scriptTag ? scriptTag.getAttribute('data-id') : 'demo-client';

    // Configurable relay host - default to localhost:8000 for dev, but allows override via data-relay-host
    // Example: <script src="..." data-id="xyz" data-relay-host="relay.sov-mech.ai"></script>
    const configuredHost = scriptTag ? scriptTag.getAttribute('data-relay-host') : null;
    const relayHost = configuredHost || "localhost:8000";

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${relayHost}/chat?client_id=${clientId}`;

    let ws;
    try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
             console.log("Connected to relay");
        };

        ws.onmessage = (e) => {
            const data = JSON.parse(e.data);
            addMsg(data.response, 'ai');
        };

        ws.onerror = (e) => {
            console.error("WebSocket error:", e);
        };

    } catch (e) {
        console.error("Failed to connect to WebSocket", e);
    }

    input.onkeypress = (e) => {
        if (e.key === 'Enter' && input.value.trim()) {
            const val = input.value;
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ text: val }));
            } else {
                // Echo for demo if offline
                console.warn("Offline mode - echoing");
                setTimeout(() => addMsg("I am currently offline (Demo Mode).", 'ai'), 500);
            }
            addMsg(val, 'user');
            input.value = '';
        }
    };

    function addMsg(text, type) {
        const div = document.createElement('div');
        div.className = `msg ${type}`;
        div.textContent = text;
        msgBox.appendChild(div);
        msgBox.scrollTop = msgBox.scrollHeight;
    }
})();
