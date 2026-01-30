import { useState, useEffect, useRef } from 'react';
import { ChatInput } from './components/ChatInput';
import { MessageList } from './components/MessageList';
import { api } from './services/api';
import { useSSE } from './hooks/useSSE';
import './App.css';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [streamUrl, setStreamUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('idle');
  const messagesEndRef = useRef(null);

  const { events, status: sseStatus, reset: resetSSE } = useSSE(streamUrl);

  // Scroll to bottom on new events
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events, messages]);

  // Update connection status and detect when waiting for input
  useEffect(() => {
    setConnectionStatus(sseStatus);
    if (sseStatus === 'complete' || sseStatus === 'error') {
      setIsProcessing(false);
    }
  }, [sseStatus]);

  // Detect when flow is waiting for user input (questions asked)
  useEffect(() => {
    if (events.length > 0) {
      const lastEvent = events[events.length - 1];
      // If the last event is a question or a progress with "Waiting for", enable input
      if (lastEvent.type === 'question' || 
          (lastEvent.type === 'progress' && lastEvent.content?.includes('Waiting for'))) {
        setIsProcessing(false);
      }
    }
  }, [events]);

  const handleSend = async (message) => {
    // Track how many events exist when this message is sent
    // so MessageList can properly interleave
    const eventCountAtSend = events.length;
    
    // Add user message to list with event index marker
    setMessages((prev) => [...prev, { 
      role: 'user', 
      content: message, 
      eventIndexAtSend: eventCountAtSend 
    }]);
    setIsProcessing(true);

    try {
      // Send to API
      const response = await api.sendMessage(message, sessionId);

      // Store session ID
      if (response.session_id) {
        setSessionId(response.session_id);
        // Start SSE stream
        setStreamUrl(api.getStreamUrl(response.session_id));
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setSessionId(null);
    setMessages([]);
    setStreamUrl(null);
    setIsProcessing(false);
    resetSSE();
  };

  // Get placeholder text based on state
  const getPlaceholder = () => {
    if (isProcessing) return 'Processing...';
    if (!sessionId) return 'Describe your travel plans...';
    // Check if last event was a question
    const lastEvent = events[events.length - 1];
    if (lastEvent?.type === 'question') return 'Answer the questions above...';
    if (lastEvent?.type === 'plan') return 'Type "done" or suggest changes...';
    return 'Continue the conversation...';
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🌍</span>
          <div>
            <h1 className="text-xl font-bold text-gray-900">AI Travel Guide</h1>
            <p className="text-sm text-gray-500">Plan your perfect trip</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* Status indicator */}
          {connectionStatus !== 'idle' && (
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              connectionStatus === 'connected' ? 'bg-green-100 text-green-700' :
              connectionStatus === 'connecting' ? 'bg-yellow-100 text-yellow-700' :
              connectionStatus === 'complete' ? 'bg-blue-100 text-blue-700' :
              'bg-red-100 text-red-700'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-500 animate-pulse' :
                connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                connectionStatus === 'complete' ? 'bg-blue-500' :
                'bg-red-500'
              }`} />
              {connectionStatus}
            </div>
          )}
          {sessionId && (
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              New Trip
            </button>
          )}
        </div>
      </header>

      {/* Messages area */}
      <main className="flex-1 min-h-0 overflow-hidden">
        {messages.length === 0 && events.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-8 text-center">
            <span className="text-6xl mb-6">✈️</span>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Where would you like to go?
            </h2>
            <p className="text-gray-600 max-w-md">
              Tell me about your dream trip - destination, duration, budget, interests - and I'll create a personalized travel plan for you.
            </p>
            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="p-4 bg-white rounded-xl border border-gray-200">
                <div className="text-2xl mb-2">🗼</div>
                <div className="font-medium">Paris for 5 days</div>
                <div className="text-gray-500">Art, food, and romance</div>
              </div>
              <div className="p-4 bg-white rounded-xl border border-gray-200">
                <div className="text-2xl mb-2">🏯</div>
                <div className="font-medium">Tokyo for a week</div>
                <div className="text-gray-500">Culture and cuisine</div>
              </div>
              <div className="p-4 bg-white rounded-xl border border-gray-200">
                <div className="text-2xl mb-2">🏖️</div>
                <div className="font-medium">Bali for 10 days</div>
                <div className="text-gray-500">Beaches and wellness</div>
              </div>
            </div>
          </div>
        ) : (
          <MessageList messages={messages} events={events} />
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Input area */}
      <ChatInput
        onSend={handleSend}
        disabled={isProcessing}
        placeholder={getPlaceholder()}
      />
    </div>
  );
}

export default App;
