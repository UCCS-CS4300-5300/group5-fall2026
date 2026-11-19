document.addEventListener('DOMContentLoaded', () => {
    const bellStage = document.getElementById('chef-bell-stage');
    const bellBtn = document.getElementById('chef-bell-btn');
    const loadingBox = document.getElementById('chef-loading');
    const loadingText = document.getElementById('chef-loading-text');
    const chatRoom = document.getElementById('chef-chat-room');
    const messagesBox = document.getElementById('chef-messages');
    const chatForm = document.getElementById('chef-chat-form');
    const messageInput = document.getElementById('chef-message-input');
    const sendBtn = chatForm ? chatForm.querySelector('.chef-send-btn') : null;

    if (!bellBtn || !bellStage || !loadingBox || !chatRoom) {
        return;
    }

    const FALLBACK_CLEANING = 'The Chef is cleaning the kitchen, come back later...';
    const FALLBACK_BUSY = 'The Chef is busy right now, come back later...';
    const REQUEST_TIMEOUT_MS = 10000; // 10 seconds max before falling back

    const history = [];
    let isSummoning = false;
    let isSending = false;

    // Guarantees only one stage is visible on screen at any moment
    function setChefStage(stage) {
        bellStage.hidden = stage !== 'bell';
        loadingBox.hidden = stage !== 'loading';
        chatRoom.hidden = stage !== 'chat';
    }

    // Start strictly on the bell stage
    setChefStage('bell');

    function getCsrfToken() {
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return tokenInput ? tokenInput.value : '';
    }

    function appendMessage(role, text) {
        if (!messagesBox || !text) {
            return;
        }
        const bubble = document.createElement('div');
        bubble.className = `chef-message ${role}`;
        bubble.textContent = text;
        messagesBox.appendChild(bubble);
        messagesBox.scrollTop = messagesBox.scrollHeight;
        history.push({ role, text });
    }

    async function postChefRequest(payload, fallbackText) {
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

        try {
            const response = await fetch('/ai-chef/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(payload),
                signal: controller.signal,
            });

            if (!response.ok) {
                return { ok: false, reply: fallbackText, fallback: true };
            }

            const data = await response.json();
            return {
                ok: Boolean(data.ok),
                reply: data.reply || fallbackText,
                fallback: Boolean(data.fallback),
            };
        } catch (err) {
            // Covers AbortError (timeout), offline network, or server unreachable
            return { ok: false, reply: fallbackText, fallback: true };
        } finally {
            window.clearTimeout(timeoutId);
        }
    }

    bellBtn.addEventListener('click', () => {
        if (isSummoning) {
            return;
        }
        isSummoning = true;
        bellBtn.disabled = true;

        // 1. Phase out the bell
        bellStage.classList.add('phasing-out');

        window.setTimeout(async () => {
            // 2. Switch exclusively to the spinner stage
            if (loadingText) {
                loadingText.textContent = 'Summoning chef...';
            }
            setChefStage('loading');

            // 3. Call backend (with automatic 10s timeout -> fallback)
            const result = await postChefRequest({ action: 'init' }, FALLBACK_CLEANING);

            // 4. Switch exclusively to the chatroom with either recipes or fallback message
            setChefStage('chat');
            appendMessage('assistant', result.reply);
            if (messageInput) {
                messageInput.focus();
            }
        }, 300);
    });

    if (chatForm && messageInput) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (isSending) {
                return;
            }
            const text = messageInput.value.trim();
            if (!text) {
                return;
            }

            isSending = true;
            if (sendBtn) {
                sendBtn.disabled = true;
            }
            messageInput.disabled = true;

            appendMessage('user', text);
            messageInput.value = '';

            // Temporary "Chef is thinking..." bubble while awaiting follow-up
            const thinkingBubble = document.createElement('div');
            thinkingBubble.className = 'chef-message assistant';
            thinkingBubble.textContent = 'Chef is thinking...';
            messagesBox.appendChild(thinkingBubble);
            messagesBox.scrollTop = messagesBox.scrollHeight;

            const result = await postChefRequest(
                { action: 'message', message: text, history: history.slice(0, -1) },
                FALLBACK_BUSY
            );

            thinkingBubble.remove();
            appendMessage('assistant', result.reply);

            isSending = false;
            if (sendBtn) {
                sendBtn.disabled = false;
            }
            messageInput.disabled = false;
            messageInput.focus();
        });
    }
});