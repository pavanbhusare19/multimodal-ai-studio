
const $ = id => document.getElementById(id);

const show = (id, html) => {
    $(id).innerHTML = html;
};

async function post(url, body, isForm = false) {
    const res = await fetch(url, {
        method: 'POST',
        headers: isForm ? {} : {
            'Content-Type': 'application/json'
        },
        body: isForm ? body : JSON.stringify(body)
    });

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.error || 'Request failed');
    }

    return data;
}

// --------------------------------------------------
// TAB SWITCHING
// --------------------------------------------------

document.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab, .panel').forEach(item => {
            item.classList.remove('active');
        });

        btn.classList.add('active');
        $(btn.dataset.tab).classList.add('active');
    });
});

// --------------------------------------------------
// API HEALTH STATUS
// --------------------------------------------------

fetch('/api/health')
    .then(res => res.json())
    .then(data => {
        $('status').textContent = data.api_key_configured
            ? '● Gemini connected'
            : '● Add Gemini API key';

        $('status').style.color = data.api_key_configured
            ? '#76d8b4'
            : '#f2c879';
    })
    .catch(() => {
        $('status').textContent = 'API unavailable';
    });

// --------------------------------------------------
// RESEARCHMATE AI AGENT CHAT
// --------------------------------------------------

$('chatform').addEventListener('submit', async e => {
    e.preventDefault();

    const msg = $('chatinput').value.trim();

    if (!msg) return;

    // Display user message
    const userBubble = document.createElement('div');
    userBubble.className = 'bubble user';
    userBubble.textContent = msg;

    $('chatlog').appendChild(userBubble);
    $('chatinput').value = '';

    // Loading message
    const loadingBubble = document.createElement('div');
    loadingBubble.className = 'bubble bot';
    loadingBubble.textContent = 'ResearchMate is thinking...';

    $('chatlog').appendChild(loadingBubble);
    $('chatlog').scrollTop = $('chatlog').scrollHeight;

    try {
        // Call ResearchMate agent API
        const data = await post('/api/agent', {
            message: msg
        });

        // Remove loading message
        loadingBubble.remove();

        // Format agent tool activity
        const events = (data.tool_events || []).map(event => {
            if (event.event === 'tool_call') {
                return 'Tool called: ' + event.tool;
            }

            if (event.event === 'tool_result') {
                return 'Tool result: ' + event.tool +
                    ' - ' + event.output_preview;
            }

            return event.event;
        }).join('\n');

        // Display agent response
        const botBubble = document.createElement('div');
        botBubble.className = 'bubble bot';

        botBubble.textContent = data.answer +
            (events
                ? '\n\n--- Tool Activity ---\n' + events
                : '');

        $('chatlog').appendChild(botBubble);
        $('chatlog').scrollTop = $('chatlog').scrollHeight;

        window.lastAnswer = data.answer;

    } catch (error) {
        loadingBubble.remove();

        const errorBubble = document.createElement('div');
        errorBubble.className = 'bubble bot';
        errorBubble.textContent = 'Error: ' + error.message;

        $('chatlog').appendChild(errorBubble);
        $('chatlog').scrollTop = $('chatlog').scrollHeight;
    }
});

// --------------------------------------------------
// IMAGE STUDIO
// --------------------------------------------------

$('imagefile').addEventListener('change', () => {
    const file = $('imagefile').files[0];

    if (file) {
        $('preview').src = URL.createObjectURL(file);
        $('preview').hidden = false;
    }
});

$('imageform').addEventListener('submit', async e => {
    e.preventDefault();

    show('visionout', 'Analyzing image...');

    const formData = new FormData();

    formData.append('image', $('imagefile').files[0]);
    formData.append('question', $('imagequestion').value);

    try {
        const data = await post(
            '/api/analyze-image',
            formData,
            true
        );

        show('visionout', escapeHtml(data.answer));

    } catch (error) {
        show(
            'visionout',
            'Error: ' + escapeHtml(error.message)
        );
    }
});

// --------------------------------------------------
// HTML ESCAPE HELPER
// --------------------------------------------------

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, char => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[char]));
}

// --------------------------------------------------
// VOICE STUDIO - SPEECH TO TEXT
// --------------------------------------------------

let recognition = null;

$('listen').addEventListener('click', () => {
    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        $('voicestatus').textContent =
            'Speech recognition is not supported. Try Chrome desktop.';
        return;
    }

    recognition = new SpeechRecognition();

    recognition.lang = 'en-IN';
    recognition.interimResults = true;

    recognition.onstart = () => {
        $('voicestatus').textContent = 'Listening...';
    };

    recognition.onresult = event => {
        let transcript = '';

        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {
            transcript += event.results[i][0].transcript;
        }

        $('voicetext').value = transcript;
    };

    recognition.onerror = event => {
        $('voicestatus').textContent =
            'Speech error: ' + event.error;
    };

    recognition.onend = () => {
        $('voicestatus').textContent =
            'Speech capture finished.';
    };

    recognition.start();
});

// --------------------------------------------------
// VOICE STUDIO - SEND MESSAGE
// --------------------------------------------------

$('sendvoice').addEventListener('click', async () => {
    const message = $('voicetext').value.trim();

    if (!message) return;

    try {
        const data = await post('/api/chat', {
            message: message
        });

        window.lastAnswer = data.answer;

        show('voiceout', escapeHtml(data.answer));

    } catch (error) {
        show(
            'voiceout',
            'Error: ' + escapeHtml(error.message)
        );
    }
});

// --------------------------------------------------
// VOICE STUDIO - TEXT TO SPEECH
// --------------------------------------------------

$('speak').addEventListener('click', () => {
    if (!window.lastAnswer) {
        $('voicestatus').textContent =
            'Send a message first.';
        return;
    }

    if (!('speechSynthesis' in window)) {
        $('voicestatus').textContent =
            'Speech synthesis is not supported.';
        return;
    }

    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(
        window.lastAnswer
    );

    utterance.lang = 'en-IN';

    speechSynthesis.speak(utterance);
});

// --------------------------------------------------
// AI CONTENT PIPELINE
// --------------------------------------------------

$('pipelineform').addEventListener('submit', async e => {
    e.preventDefault();

    show(
        'pipelineout',
        'Running research → outline → draft → refinement. This may take a minute...'
    );

    try {
        const data = await post('/api/content', {
            topic: $('topic').value,
            content_type: $('ctype').value,
            audience: $('audience').value,
            tone: $('tone').value
        });

        show(
            'pipelineout',
            `
            <div class="resultblock">
                <h3>RESEARCH BRIEF</h3>
                ${escapeHtml(data.research)}
            </div>

            <div class="resultblock">
                <h3>OUTLINE</h3>
                ${escapeHtml(data.outline)}
            </div>

            <div class="resultblock">
                <h3>FIRST DRAFT</h3>
                ${escapeHtml(data.draft)}
            </div>

            <div class="resultblock">
                <h3>FINAL PUBLISHABLE CONTENT</h3>
                ${escapeHtml(data.final)}

                <p>
                    <button class="secondary" id="copyFinal">
                        Copy final content
                    </button>
                </p>
            </div>
            `
        );

        $('copyFinal').onclick = () => {
            navigator.clipboard.writeText(data.final);
        };

    } catch (error) {
        show(
            'pipelineout',
            'Error: ' + escapeHtml(error.message)
        );
    }
});

// --------------------------------------------------
// EVALUATION
// --------------------------------------------------

$('runEval').addEventListener('click', async () => {
    show('evalout', 'Running checks...');

    try {
        const data = await post('/api/evaluate', {});

        show(
            'evalout',
            data.checks.map(check => `
                <div class="check">
                    ${check.passed ? '✓' : '✕'}
                    ${escapeHtml(check.name)}
                </div>
            `).join('') +
            `<p><b>${data.passed}/${data.total} checks passed</b></p>`
        );

    } catch (error) {
        show(
            'evalout',
            'Error: ' + escapeHtml(error.message)
        );
    }
});
