document.addEventListener('DOMContentLoaded', function () {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const speechToggle = document.getElementById('speechToggle');
    const moodButton = document.getElementById('moodButton');
    const moodSelector = document.getElementById('moodSelector');
    const actionButtons = document.querySelectorAll('.action-btn');
    const closeBreathing = document.getElementById('closeBreathing');
    const breathingGuide = document.getElementById('breathingGuide');

    // Function to add a message to the chat
    function addMessage(text, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');

        const textSpan = document.createElement('span');
        textSpan.classList.add('message-text');
        textSpan.textContent = text;

        messageDiv.appendChild(textSpan);

        if (!isUser) {
            const speakBtn = document.createElement('i');
            speakBtn.classList.add('fas', 'fa-volume-up', 'speak-btn');
            speakBtn.onclick = () => speakMessage(text, messageDiv);
            messageDiv.appendChild(speakBtn);
        }

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to speak a message
    function speakMessage(text, messageDiv) {
        fetch('/speak_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const spokenText = document.createElement('div');
                    spokenText.classList.add('spoken-text');
                    spokenText.textContent = `Speaking...`;
                    messageDiv.appendChild(spokenText);
                } else {
                    console.error('Text-to-speech failed.');
                }
            })
            .catch(error => {
                console.error('Error speaking message:', error);
                addMessage("Sorry, I couldn't speak that message. Please try again.", false);
            });
    }

    // Function to send a message to the backend
    async function sendMessageToBackend(message) {
        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    speak: speechToggle.checked,
                }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            return data.response;
        } catch (error) {
            console.error('Error sending message:', error);
            return "Oops, something went wrong. Try again or contact support.";
        }
    }

    // Handle user input
    sendButton.addEventListener('click', async () => {
        const userText = userInput.value.trim();
        if (userText) {
            addMessage(userText, true);
            userInput.value = '';

            const botResponse = await sendMessageToBackend(userText);
            addMessage(botResponse, false);

            if (speechToggle.checked) {
                speakMessage(botResponse, chatMessages.lastChild);
            }
        }
    });

    // Allow pressing Enter to send a message
    userInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            const userText = userInput.value.trim();
            if (userText) {
                addMessage(userText, true);
                userInput.value = '';

                const botResponse = await sendMessageToBackend(userText);
                addMessage(botResponse, false);

                if (speechToggle.checked) {
                    speakMessage(botResponse, chatMessages.lastChild);
                }
            }
        }
    });

    // Handle quick action buttons
    actionButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const message = button.getAttribute('data-message');
            addMessage(message, true);

            const botResponse = await sendMessageToBackend(message);
            addMessage(botResponse, false);

            if (speechToggle.checked) {
                speakMessage(botResponse, chatMessages.lastChild);
            }
        });
    });

    // Toggle mood selector
    moodButton.addEventListener('click', () => {
        moodSelector.classList.toggle('active');
    });

    // Handle mood selection
    moodSelector.querySelectorAll('.mood').forEach(mood => {
        mood.addEventListener('click', async () => {
            const selectedMood = mood.getAttribute('data-mood');
            const moodMessage = `I’m feeling ${selectedMood.toLowerCase()} about my career.`;
            addMessage(moodMessage, true);
            moodSelector.classList.remove('active');

            // Show breathing guide if stressed or overwhelmed
            if (selectedMood === 'Stressed' || selectedMood === 'Overwhelmed') {
                breathingGuide.classList.add('active');
            }

            const botResponse = await sendMessageToBackend(moodMessage);
            addMessage(botResponse, false);

            if (speechToggle.checked) {
                speakMessage(botResponse, chatMessages.lastChild);
            }
        });
    });

    // Handle breathing guide close button
    closeBreathing.addEventListener('click', () => {
        breathingGuide.classList.remove('active');
        addMessage("Great, let's get back to your career journey! What would you like to explore next?", false);
    });

    // Add feedback button dynamically
    const feedbackBtn = document.createElement('button');
    feedbackBtn.textContent = "Provide Feedback";
    feedbackBtn.classList.add('action-btn');
    feedbackBtn.addEventListener('click', () => {
        const feedback = prompt("Share your feedback about Asha:");
        if (feedback) {
            fetch('/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ feedback: feedback }),
            })
                .then(response => response.json())
                .then(data => addMessage(data.response, false))
                .catch(error => {
                    console.error('Error submitting feedback:', error);
                    addMessage("Sorry, I couldn't submit your feedback. Please try again.", false);
                });
        }
    });
    document.querySelector('.quick-actions').appendChild(feedbackBtn);
});