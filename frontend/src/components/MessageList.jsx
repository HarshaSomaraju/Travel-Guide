import { useRef, useEffect } from 'react';
import { StatusIndicator } from './StatusIndicator';
import { TravelPlan } from './TravelPlan';

export function MessageList({ messages, events }) {
  const bottomRef = useRef(null);

  // Auto-scroll to bottom when messages or events change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, events]);

  // Helper to check if event should be filtered
  const shouldShowEvent = (event) => {
    if (event.type === 'question' && event.content === 'Please answer the questions above') {
      return false;
    }
    if (event.type === 'progress' && !event.content) {
      return false;
    }
    if (event.type === 'progress' && event.content?.startsWith('Waiting for:')) {
      return false;
    }
    return true;
  };

  // Build proper interleaved timeline using raw event indices
  const buildTimeline = () => {
    const timeline = [];
    let rawEventIndex = 0;

    messages.forEach((msg, msgIndex) => {
      // Add events that occurred BEFORE this message was sent
      const eventsBeforeThisMessage = msg.eventIndexAtSend ?? 0;
      
      while (rawEventIndex < eventsBeforeThisMessage && rawEventIndex < events.length) {
        const event = events[rawEventIndex];
        // Only add if it passes filter
        if (shouldShowEvent(event)) {
          timeline.push({
            ...event,
            itemType: event.type,
            key: `event-${rawEventIndex}`,
          });
        }
        rawEventIndex++;
      }

      // Add the user message
      timeline.push({
        itemType: 'user_message',
        content: msg.content,
        key: `msg-${msgIndex}`,
      });
    });

    // Add remaining events after the last message
    while (rawEventIndex < events.length) {
      const event = events[rawEventIndex];
      if (shouldShowEvent(event)) {
        timeline.push({
          ...event,
          itemType: event.type,
          key: `event-${rawEventIndex}`,
        });
      }
      rawEventIndex++;
    }

    return timeline;
  };

  const timeline = buildTimeline();

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {timeline.map((item) => {
        // User message
        if (item.itemType === 'user_message') {
          return (
            <div key={item.key} className="flex justify-end">
              <div className="max-w-[80%] px-4 py-3 bg-blue-600 text-white rounded-2xl rounded-br-md whitespace-pre-wrap">
                {item.content}
              </div>
            </div>
          );
        }

        // Plan event
        if (item.itemType === 'plan') {
          return (
            <TravelPlan
              key={item.key}
              content={item.content}
              isFinal={item.metadata?.is_final}
            />
          );
        }

        // Other events
        return (
          <div key={item.key} className="flex justify-start">
            <div className="max-w-[90%]">
              <StatusIndicator type={item.itemType} content={item.content} />
            </div>
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
