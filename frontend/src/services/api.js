const API_BASE = '/api';

export const api = {
    // Start or continue a chat
    sendMessage: async (message, sessionId = null) => {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId }),
        });
        return response.json();
    },

    // Get session details
    getSession: async (sessionId) => {
        const response = await fetch(`${API_BASE}/chat/${sessionId}`);
        return response.json();
    },

    // Get SSE stream URL
    getStreamUrl: (sessionId) => {
        return `${API_BASE}/chat/${sessionId}/stream`;
    },
};
