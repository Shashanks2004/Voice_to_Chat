const orb = document.getElementById("orb");
const statusText = document.getElementById("status");
const commandInput = document.getElementById("commandInput");
const codeOutput = document.getElementById("codeOutput");

const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

const recognition = new SpeechRecognition();

recognition.continuous = false;
recognition.interimResults = false;
recognition.lang = "en-US";

let activated = false;
let waitingForCommand = false;
let isSpeaking = false;
let femaleVoice = null;
let recognitionActive = false;

/* ================= LOAD FEMALE VOICE ================= */

function loadVoices() {
    const voices = window.speechSynthesis.getVoices();

    femaleVoice = voices.find(v =>
        v.name.toLowerCase().includes("zira") ||
        v.name.toLowerCase().includes("female") ||
        v.name.toLowerCase().includes("samantha")
    );
}

window.speechSynthesis.onvoiceschanged = loadVoices;

/* ================= TEXT TO SPEECH ================= */

function speak(text, callback = null) {

    isSpeaking = true;
    recognition.stop();

    const msg = new SpeechSynthesisUtterance(text);

    if (femaleVoice) {
        msg.voice = femaleVoice;
    }

    msg.pitch = 1.1;
    msg.rate = 1;

    msg.onend = () => {
        isSpeaking = false;
        callback && callback();
    };

    window.speechSynthesis.speak(msg);
}

/* ================= SAFE START ================= */

function safeStartRecognition() {
    if (!recognitionActive && !isSpeaking) {
        try {
            recognition.start();
            recognitionActive = true;
        } catch (e) {}
    }
}

/* ================= SAFE STOP ================= */

function safeStopRecognition() {
    if (recognitionActive) {
        recognition.stop();
        recognitionActive = false;
    }
}

/* ================= MAIN LISTENER ================= */

recognition.onresult = function(event) {

    const transcript = event.results[0][0].transcript
        .toLowerCase()
        .trim();

    commandInput.value = transcript;

    // Wake word detection
    if (!activated && transcript.includes("hey diya")) {

        activated = true;
        waitingForCommand = true;

        statusText.innerText = "Diya is listening...";
        orb.style.boxShadow =
            "0 0 60px #00f5ff, 0 0 120px #a855f7, 0 0 200px #ff00cc";

        speak("Yes, I am listening.", () => {
            safeStartRecognition();
        });

        return;
    }

    // Command capture phase
    if (activated && waitingForCommand) {

        waitingForCommand = false;
        activated = false;

        statusText.innerText = "Processing your request...";
        orb.style.boxShadow =
            "0 0 40px #00f5ff, 0 0 80px #00f5ff";

        sendCommand(transcript);
    }
};

/* ================= RESTART AFTER EACH SESSION ================= */

recognition.onend = function() {
    recognitionActive = false;

    if (!isSpeaking) {
        setTimeout(() => {
            safeStartRecognition();
        }, 600);
    }
};

/* ================= SEND TO BACKEND ================= */

function sendCommand(text) {

    fetch("https://voice-to-chat.onrender.com/generate-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",   // IMPORTANT for session
        body: JSON.stringify({ text: text })
    })
    .then(res => res.json())
    .then(data => {

        codeOutput.innerText = data.code;

        speak("Here is your program.", () => {
            statusText.innerText = "Say 'Hey Diya'";
            safeStartRecognition();
        });

    })
    .catch(() => {

        codeOutput.innerText = "Error connecting to backend.";
        statusText.innerText = "Error occurred.";

        safeStartRecognition();
    });
}

/* ================= COPY ================= */

function copyCode() {
    navigator.clipboard.writeText(codeOutput.innerText);
}

/* ================= PARTICLES ================= */

particlesJS("particles", {
    particles: {
        number: { value: 60 },
        color: { value: "#00f5ff" },
        shape: { type: "circle" },
        opacity: { value: 0.4 },
        size: { value: 3 },
        move: { enable: true, speed: 1 }
    }
});

/* ================= INITIAL START ================= */

window.onload = function () {
    loadVoices();
    setTimeout(() => {
        safeStartRecognition();
    }, 1000);
};