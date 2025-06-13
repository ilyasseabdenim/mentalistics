// static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const chatContainer = document.getElementById('chat-container');
    const languageSelector = document.getElementById('language-selector');
    const sendButton = document.getElementById('send-button');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const startChatButton = document.getElementById('start-chat-button');
    const chatSection = document.getElementById('chat-section');
    const suggestionChips = document.querySelectorAll('.suggestion-chip');
    const thinkingAnimationTemplate = document.getElementById('thinking-animation-template');
    
    // --- State ---
    let isLoading = false;

    // --- i18n Translations (Updated for Mental Health Theme) ---
    const i18n = {
        en: {
            title: "Mind-Soothe | Your Space to Reflect",
            description: "An AI companion for mental well-being. A safe space to explore your thoughts and feelings, with gentle guidance and support.",
            headline1: "A quiet place",
            headline2: "for your thoughts.",
            subheadline: "An empathetic AI assistant designed to listen, support, and help you navigate your feelings. Start a conversation whenever you need.",
            cta_button: "Begin Session",
            chip_anxiety: "Coping with anxiety",
            chip_stress: "Managing stress",
            chip_mindfulness: "What is mindfulness?",
            placeholder_input: "How are you feeling today?",
            welcome_message: "Hello. I'm Mind-Soothe, your AI companion for reflection. Feel free to share what's on your mind. I'm here to listen without judgment."
        },
        fr: {
            title: "Mind-Soothe | Votre Espace pour Réfléchir",
            description: "Un compagnon IA pour le bien-être mental. Un espace sûr pour explorer vos pensées et sentiments, avec un soutien et des conseils bienveillants.",
            headline1: "Un lieu apaisant",
            headline2: "pour vos pensées.",
            subheadline: "Un assistant IA empathique conçu pour écouter, soutenir et vous aider à naviguer vos émotions. Commencez la conversation quand vous en avez besoin.",
            cta_button: "Commencer la Session",
            chip_anxiety: "Gérer l'anxiété",
            chip_stress: "Faire face au stress",
            chip_mindfulness: "Qu'est-ce que la pleine conscience ?",
            placeholder_input: "Comment vous sentez-vous aujourd'hui ?",
            welcome_message: "Bonjour. Je suis Mind-Soothe, votre compagnon IA pour la réflexion. N'hésitez pas à partager ce qui vous préoccupe. Je suis là pour écouter sans jugement."
        },
        ar: {
            title: "Mind-Soothe | مساحتك للتفكير",
            description: "رفيق ذكاء اصطناعي للصحة النفسية. مساحة آمنة لاستكشاف أفكارك ومشاعرك، مع توجيه ودعم لطيف.",
            headline1: "مكان هادئ",
            headline2: "لأفكارك.",
            subheadline: "مساعد ذكاء اصطناعي متعاطف مصمم للاستماع والدعم ومساعدتك في التعامل مع مشاعرك. ابدأ المحادثة متى احتجت.",
            cta_button: "ابدأ الجلسة",
            chip_anxiety: "التعامل مع القلق",
            chip_stress: "إدارة التوتر",
            chip_mindfulness: "ما هو الوعي التام؟",
            placeholder_input: "كيف تشعر اليوم؟",
            welcome_message: "مرحباً. أنا Mind-Soothe، رفيقك الذكي للتفكير. لا تتردد في مشاركة ما يدور في ذهنك. أنا هنا للاستماع دون أي حكم."
        }
    };

    // --- Initial Setup ---
    const init = () => {
        feather.replace();
        setupEventListeners();
        autoResizeTextarea();
        setupIntersectionObserver();
        initializeLanguage();
        setupViewportListener();
    };

    const initializeLanguage = () => {
        const browserLang = navigator.language.split('-')[0];
        const lang = ['fr', 'ar'].includes(browserLang) ? browserLang : 'en';
        languageSelector.value = lang;
        changeLanguage(lang);
    };

    const addWelcomeMessage = (lang) => {
        setTimeout(() => {
            addMessage('bot', i18n[lang].welcome_message);
        }, 1000);
    };
    
    // --- Event Listeners ---
    const setupEventListeners = () => {
        languageSelector.addEventListener('change', (e) => changeLanguage(e.target.value));
        sendButton.addEventListener('click', handleSendMessage);
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }
        });
        userInput.addEventListener('input', autoResizeTextarea);
        startChatButton.addEventListener('click', () => {
            chatSection.scrollIntoView({ behavior: 'smooth' });
            setTimeout(() => userInput.focus(), 500);
        });
        suggestionChips.forEach(chip => {
            chip.addEventListener('click', (e) => {
                const query = e.target.getAttribute('data-query');
                const lang = document.documentElement.lang;
                const promptText = i18n[lang][query] || query; // Use translated query if available
                userInput.value = promptText;
                userInput.focus(); handleSendMessage();
            });
        });
    };
    
    // --- Core Functions ---
    const handleSendMessage = async () => {
        const messageText = userInput.value.trim();
        if (messageText === '' || isLoading) return;
        setLoading(true);
        addMessage('user', messageText);
        const thinkingMessageId = addThinkingMessage();
        userInput.value = ''; autoResizeTextarea();
        try {
            const response = await fetch('/ask', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText }),
            });
            if (!response.ok) throw new Error('Network response was not ok.');
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            updateThinkingMessage(thinkingMessageId, data.response);
        } catch (error) {
            console.error('Error:', error);
            updateThinkingMessage(thinkingMessageId, "I'm sorry, but I encountered an error. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const changeLanguage = (lang) => {
        document.documentElement.lang = lang;
        document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
        const translations = i18n[lang];
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (translations[key]) el.textContent = translations[key];
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (translations[key]) el.placeholder = translations[key];
        });
        // Update suggestion chip text without changing their query
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            const key = chip.getAttribute('data-i18n');
             if (translations[key]) chip.textContent = translations[key];
        });
        chatMessages.innerHTML = '';
        addWelcomeMessage(lang);
    };
    
    const addMessage = (sender, text) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = `<div class="message-content">${processMarkdown(text)}</div>`;
        chatMessages.appendChild(messageDiv); scrollToBottom();
        return messageDiv.id = `msg-${Date.now()}`;
    };

    const addThinkingMessage = () => {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message is-thinking';
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.appendChild(thinkingAnimationTemplate.firstElementChild.cloneNode(true));
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv); scrollToBottom();
        return messageDiv.id = `msg-thinking-${Date.now()}`;
    };

    const updateThinkingMessage = (messageId, newText) => {
        const thinkingMessage = document.getElementById(messageId);
        if (thinkingMessage) {
            thinkingMessage.classList.remove('is-thinking');
            const contentDiv = thinkingMessage.querySelector('.message-content');
            contentDiv.style.opacity = '0';
            setTimeout(() => {
                contentDiv.innerHTML = processMarkdown(newText);
                contentDiv.style.opacity = '1'; scrollToBottom();
            }, 300);
        }
    };

    const processMarkdown = (text) => {
        let html = text
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/^\s*###\s*(.*)/gm, '<h3>$1</h3>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code>$1</code>');
        
        html = html.replace(/^\s*--\s*(.*)/gm, '<li>$1</li>');
        html = html.replace(/(<li>(?:.|\n)*?<\/li>)/g, '<ul>$1</ul>').replace(/<\/ul>\n?<ul>/g, '');

        return html.replace(/\n/g, '<br>');
    };
    
    // --- Utility & Setup Functions ---
    const setLoading = (state) => {
        isLoading = state; chatContainer.classList.toggle('is-loading', state);
        userInput.disabled = state; sendButton.disabled = state;
    };
    const scrollToBottom = () => chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
    const autoResizeTextarea = () => { userInput.style.height = 'auto'; userInput.style.height = `${userInput.scrollHeight}px`; };
    const setupIntersectionObserver = () => {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => document.body.classList.toggle('chat-active', entry.isIntersecting));
        }, { threshold: 0.5 });
        observer.observe(chatSection);
    };

    // --- Mobile Keyboard/Viewport Handling ---
    const setupViewportListener = () => {
        if (window.matchMedia("(pointer: coarse)").matches) {
            let initialViewportHeight = window.innerHeight;
            const handleViewportChange = () => {
                if (document.activeElement !== userInput) {
                     document.documentElement.style.setProperty('--keyboard-offset', `0px`);
                     return;
                }
                const keyboardOffset = initialViewportHeight - window.visualViewport.height;
                if (keyboardOffset > 100) {
                    document.documentElement.style.setProperty('--keyboard-offset', `${keyboardOffset}px`);
                }
                scrollToBottom();
            };
            const resetViewport = () => {
                 document.documentElement.style.setProperty('--keyboard-offset', `0px`);
            }
            userInput.addEventListener('focus', () => {
                initialViewportHeight = window.innerHeight;
                if(window.visualViewport) {
                    window.visualViewport.addEventListener('resize', handleViewportChange);
                }
            });
            userInput.addEventListener('blur', () => {
                if(window.visualViewport) {
                    window.visualViewport.removeEventListener('resize', handleViewportChange);
                }
                resetViewport();
            });
        }
    };

    // --- Run ---
    init();
});
