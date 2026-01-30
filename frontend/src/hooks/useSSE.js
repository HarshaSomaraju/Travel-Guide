import { useState, useEffect, useCallback, useRef } from 'react';

export function useSSE(url) {
    const [events, setEvents] = useState([]);
    const [status, setStatus] = useState('idle'); // idle, connecting, connected, complete, error
    const [latestEvent, setLatestEvent] = useState(null);
    const eventSourceRef = useRef(null);

    const connect = useCallback(() => {
        if (!url) return;

        // Close existing connection
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        setStatus('connecting');
        setEvents([]);

        const eventSource = new EventSource(url);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
            setStatus('connected');
        };

        eventSource.onerror = (error) => {
            console.error('SSE Error:', error);
            setStatus('error');
            eventSource.close();
        };

        // Listen for all event types
        const eventTypes = ['thinking', 'question', 'searching', 'progress', 'plan', 'complete', 'error'];

        eventTypes.forEach((type) => {
            eventSource.addEventListener(type, (e) => {
                try {
                    const data = JSON.parse(e.data);
                    const event = { type, ...data };
                    setEvents((prev) => [...prev, event]);
                    setLatestEvent(event);

                    if (type === 'complete') {
                        setStatus('complete');
                        eventSource.close();
                    }

                    if (type === 'error') {
                        setStatus('error');
                        eventSource.close();
                    }
                } catch (err) {
                    console.error('Failed to parse event:', err);
                }
            });
        });

        return () => {
            eventSource.close();
        };
    }, [url]);

    const disconnect = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
        setStatus('idle');
    }, []);

    const reset = useCallback(() => {
        disconnect();
        setEvents([]);
        setLatestEvent(null);
    }, [disconnect]);

    // Auto-connect when URL changes
    useEffect(() => {
        if (url) {
            connect();
        }
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, [url, connect]);

    return {
        events,
        status,
        latestEvent,
        connect,
        disconnect,
        reset,
    };
}
