const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

let chatHistory = []; // Keep track of the conversation

function addMessage(text, type) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}-message`;
    msgDiv.innerHTML = `<div class="bubble">${text}</div>`;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    
    // Save to history (clean text if it has HTML)
    chatHistory.push({ type, text: text.replace(/<[^>]*>/g, '') });
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    userInput.value = '';

    // Show thinking indicator
    const thinkingId = 'thinking-' + Date.now();
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message ai-message';
    thinkingDiv.id = thinkingId;
    thinkingDiv.innerHTML = `<div class="bubble"><i>AI is processing...</i></div>`;
    chatWindow.appendChild(thinkingDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const response = await fetch('/tasks/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                user_input: text,
                chat_history: chatHistory.slice(-6) // Send last 6 messages for context
            })
        });

        const data = await response.json();
        
        // Remove thinking
        document.getElementById(thinkingId).remove();

        if (response.ok) {
            let reminderList = data.suggested_reminders.map(r => `• <b>${r.date}:</b> ${r.friendly_message}`).join('<br>');
            
            const html = `
                ✅ ${data.ai_summary}<br><br>
                <b>Suggested Reminder Schedule:</b><br>
                ${reminderList}<br><br>
                <div class="actions">
                    <button class="confirm-btn" onclick="confirmTask(${JSON.stringify(data).replace(/"/g, '&quot;')})">Confirm Schedule</button>
                    <button class="cancel-btn" onclick="this.parentElement.parentElement.innerHTML='❌ Task cancelled.'">Cancel</button>
                </div>
            `;
            addMessage(html, 'ai');
        } else {
            addMessage(`❌ Error: ${data.detail || 'Something went wrong.'}`, 'ai');
        }
    } catch (error) {
        if (document.getElementById(thinkingId)) document.getElementById(thinkingId).remove();
        addMessage("❌ Connection error. Is the server running?", "ai");
    }
}

async function confirmTask(taskData) {
    try {
        const response = await fetch(`/tasks/${taskData.task_details.id}/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData.suggested_reminders)
        });

        if (response.ok) {
            addMessage("🚀 ممتاز! تم جدولة المواعيد بنجاح. رح يوصلك إيميلات تذكير في الأوقات المحددة.", "ai");
        } else {
            addMessage("❌ حصل خطأ أثناء حفظ المواعيد. جرب مرة ثانية.", "ai");
        }
    } catch (error) {
        addMessage("❌ مشكلة في الاتصال بالسيرفر.", "ai");
    }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
