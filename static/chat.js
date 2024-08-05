document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatContainer = document.querySelector('.chat-container');

    // Создаем кнопки "Выход" и "Очистить чат"
    const buttonContainer = document.createElement('div');
    buttonContainer.classList.add('button-container');
    
    const exitButton = document.createElement('button');
    exitButton.textContent = 'Выход';
    exitButton.classList.add('logout-btn');
    exitButton.addEventListener('click', () => {
        window.location.href = '/'; // Перенаправление на главную страницу
    });

    const clearButton = document.createElement('button');
    clearButton.textContent = 'Очистить чат';
    clearButton.classList.add('chat-btn');
    clearButton.addEventListener('click', () => {
        chatMessages.innerHTML = '';
    });

    buttonContainer.appendChild(exitButton);
    buttonContainer.appendChild(clearButton);
    
    // Добавляем кнопки после формы чата
    chatForm.after(buttonContainer);

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (message) {
            addMessage('user', message);
            userInput.value = '';
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message }),
                });
                const data = await response.json();
                if (data.error) {
                    addMessage('error', data.response);
                } else {
                    addMessage('bot', data.response);
                }
            } catch (error) {
                console.error('Error:', error);
                addMessage('error', 'Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.');
            }
        }
    });

    function addMessage(sender, text) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        const textElement = document.createElement('p');
        textElement.textContent = text;
        messageElement.appendChild(textElement);
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
