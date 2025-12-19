// Anonymous random chat client
// - Uses WebSocket (Django Channels) for matchmaking and signaling
// - Uses WebRTC for video; text chat is relayed via the WebSocket room
// Flow summary:
// 1. Client opens a WebSocket to /ws/chat/.
// 2. User clicks "Start Chat" -> send {action: 'find'} to enter queue.
// 3. Server pairs two waiting sockets and sends {action:'matched', room, initiator}.
// 4. The initiator creates an offer, both exchange SDP and ICE via {action:'signal'}.
// 5. Text messages use {action:'chat', message} and are forwarded to the room.

(function() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const nextBtn = document.getElementById('nextBtn');
    const muteBtn = document.getElementById('muteBtn');
    const camBtn = document.getElementById('camBtn');
    const reportBtn = document.getElementById('reportBtn');
    const statusEl = document.getElementById('status');
    const localVideo = document.getElementById('localVideo');
    const remoteVideo = document.getElementById('remoteVideo');
    const messagesEl = document.getElementById('messages');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');

    let socket;
    let pc = null;
    let localStream = null;
    let room = null;
    let isInitiator = false;
    let muted = false;
    let camHidden = false;

    const servers = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };
    ensureLocalStream();

    function logStatus(text) {
        statusEl.textContent = text;
    }

    function appendMessage(text, cls = 'remote') {
        const d = document.createElement('div');
        d.className = 'msg ' + cls;
        d.textContent = text;
        messagesEl.appendChild(d);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function buildSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        socket = new WebSocket(protocol + '://' + window.location.host + '/ws/chat/');

        socket.addEventListener('open', () => {
            logStatus('Connected to signaling server');
        });

        socket.addEventListener('message', async(ev) => {
            let data = {};
            try { data = JSON.parse(ev.data); } catch (e) { return; }

            if (data.action === 'waiting') {
                logStatus('Searching for stranger...');
            } else if (data.action === 'matched') {
                room = data.room;
                isInitiator = !!data.initiator;
                logStatus('Matched — setting up connection');
                createPeerConnection();
                if (isInitiator) {
                    // initiator creates offer
                    const offer = await pc.createOffer();
                    await pc.setLocalDescription(offer);
                    sendSignal(offer);
                }
                // toggle controls: hide Start, show Stop
                startBtn.style.display = 'none';
                stopBtn.style.display = '';
                startBtn.disabled = true;
                nextBtn.disabled = false;
                chatInput.disabled = false;
                reportBtn.hidden = false;

            } else if (data.action === 'signal') {
                const payload = data.data;
                if (!pc) {
                    createPeerConnection();
                }
                if (payload.type === 'offer') {
                    await pc.setRemoteDescription(new RTCSessionDescription(payload));
                    const answer = await pc.createAnswer();
                    await pc.setLocalDescription(answer);
                    sendSignal(answer);
                } else if (payload.type === 'answer') {
                    await pc.setRemoteDescription(new RTCSessionDescription(payload));

                } else if (payload.candidate) {
                    try {
                        // Reconstruct RTCIceCandidate from the plain object received
                        await pc.addIceCandidate(new RTCIceCandidate(payload));
                    } catch (e) {
                        console.warn('Failed to add ICE candidate', e);
                    }
                }
            } else if (data.action === 'chat') {
                appendMessage(data.message, 'remote');
            } else if (data.action === 'partner_left') {
                // clear messages after session ends
                clearMessages();
                cleanupPeer();
                setStartVisible(false);

                appendMessage('Partner disconnected.', 'system');
                // auto-restart search
                logStatus('Searching for stranger...');
                socket.send(JSON.stringify({ action: 'find' }));
            }
        });

        socket.addEventListener('close', () => {
            logStatus('Signaling connection closed');
            clearMessages();
            cleanupPeer();
        });
    }

    function sendSignal(data) {
        if (!socket || socket.readyState !== WebSocket.OPEN) return;
        socket.send(JSON.stringify({ action: 'signal', data }));
    }

    async function ensureLocalStream() {
        if (!localStream) {
            try {
                localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                localVideo.srcObject = localStream;
            } catch (e) {
                console.error('getUserMedia failed:', e);
                alert('Unable to access camera/microphone.');
                throw e;
            }
        }
    }

    function clearMessages() {
        if (messagesEl) messagesEl.innerHTML = '';
    }

    function setStartVisible(visible) {
        if (visible) {
            startBtn.style.display = '';
            stopBtn.style.display = 'none';
        } else {
            startBtn.style.display = 'none';
            stopBtn.style.display = '';
        }
    }

    function createPeerConnection() {
        if (pc) return;
        pc = new RTCPeerConnection(servers);

        // send local tracks
        if (localStream) {
            for (const track of localStream.getTracks()) pc.addTrack(track, localStream);
        }

        pc.ontrack = (ev) => {
            remoteVideo.srcObject = ev.streams[0];
        };

        pc.onicecandidate = (ev) => {
            if (ev.candidate) {
                // Send only the serializable candidate fields to avoid
                // losing sdpMid/sdpMLineIndex during JSON transport.
                const c = ev.candidate;
                sendSignal({ candidate: c.candidate, sdpMid: c.sdpMid, sdpMLineIndex: c.sdpMLineIndex });
            }
        };

        pc.onconnectionstatechange = () => {
            if (!pc) return;
            if (pc.connectionState === 'connected') {
                logStatus('Connected to stranger');
            } else if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
                appendMessage('Connection lost.', 'system');
            }
        };
    }

    function cleanupPeer() {
        if (pc) {
            try { pc.close(); } catch (e) {}
            pc = null;
        }
        if (remoteVideo.srcObject) {
            try { remoteVideo.srcObject.getTracks().forEach(t => t.stop()); } catch (e) {}
            remoteVideo.srcObject = null;
        }
        room = null;
        isInitiator = false;
        // restore UI: show Start, hide Stop; disable Next
        setStartVisible(true);
        startBtn.disabled = false;
        nextBtn.disabled = true;
        chatInput.disabled = true;
        reportBtn.hidden = true;

        // clear messages when session ends
        // (kept here for safety; other handlers also call clearMessages)
        // clearMessages();
    }

    // UI handlers
    startBtn.addEventListener('click', async() => {
        if (!socket || socket.readyState !== WebSocket.OPEN) buildSocket();
        logStatus('Searching for stranger...');
        // toggle UI: hide Start, show Stop
        setStartVisible(false);
        // request to find once socket is open
        socket.addEventListener('open', () => {
            socket.send(JSON.stringify({ action: 'find' }));
        });
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: 'find' }));
        }
    });

    nextBtn.addEventListener('click', () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: 'next' }));
        }
        cleanupPeer();
        // start searching again automatically
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: 'find' }));
            logStatus('Searching for stranger...');
        }
    });

    // Stop: end the current session and do not auto-restart
    stopBtn.addEventListener('click', () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: 'next' }));
        }
        // clear chat history and cleanup
        clearMessages();
        cleanupPeer();
        logStatus('Stopped');
    });

    // Mute/unmute local audio
    muteBtn.addEventListener('click', async() => {
        try {
            await ensureLocalStream();
        } catch (e) { return; }
        muted = !muted;
        localStream.getAudioTracks().forEach(t => t.enabled = !muted);
        muteBtn.innerHTML = muted ? '<i class="fa-solid fa-microphone-slash"></i>' : '<i class="fa-solid fa-microphone"></i>';
        muteBtn.setAttribute('aria-pressed', String(muted));
    });

    // Hide/show local camera
    camBtn.addEventListener('click', async() => {
        try {
            await ensureLocalStream();
        } catch (e) { return; }
        camHidden = !camHidden;
        localStream.getVideoTracks().forEach(t => t.enabled = !camHidden);
        localVideo.style.opacity = camHidden ? '0' : '1';
        camBtn.innerHTML = camHidden ? '<i class="fa-solid fa-video-slash"></i>' : '<i class="fa-solid fa-video"></i>';
        camBtn.setAttribute('aria-pressed', String(camHidden));
    });

    // Report partner: capture a snapshot of local & remote video and send to server
    reportBtn.addEventListener('click', async() => {
        // capture helper
        function captureFrameFromVideo(videoEl) {
            try {
                const w = videoEl.videoWidth || 640;
                const h = videoEl.videoHeight || 360;
                const canvas = document.createElement('canvas');
                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(videoEl, 0, 0, w, h);
                // quality 0.8 to reduce size
                return canvas.toDataURL('image/jpeg', 0.8);
            } catch (e) {
                return null;
            }
        }

        // ensure we have at least the local stream
        try { await ensureLocalStream(); } catch (e) { /* ignore */ }

        const localImage = localVideo ? captureFrameFromVideo(localVideo) : null;
        const remoteImage = (remoteVideo && remoteVideo.srcObject) ? captureFrameFromVideo(remoteVideo) : null;

        const payload = {
            action: 'report',
            room: room || null,
            timestamp: new Date().toISOString(),
            local_image: localImage,
            remote_image: remoteImage,
        };

        if (socket && socket.readyState === WebSocket.OPEN) {
            try {
                socket.send(JSON.stringify(payload));
                appendMessage('Report sent to moderators.', 'system');
            } catch (e) {
                console.error('Failed to send report', e);
                appendMessage('Failed to send report.', 'system');
            }
        } else {
            appendMessage('Cannot send report: not connected.', 'system');
        }
    });

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;
        appendMessage(text, 'local');
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: 'chat', message: text }));
        }
        chatInput.value = '';
    });

    // initialize socket immediately in background (keeps code simple)
    try { buildSocket(); } catch (e) { console.warn('Socket init failed', e); }

})();