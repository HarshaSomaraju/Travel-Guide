const statusConfig = {
  thinking: {
    icon: '🤔',
    label: 'Thinking...',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    animation: 'animate-pulse',
  },
  searching: {
    icon: '🔍',
    label: 'Searching...',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    animation: 'animate-pulse',
  },
  progress: {
    icon: '✅',
    label: 'Progress',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    animation: '',
  },
  question: {
    icon: '❓',
    label: 'Question',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    animation: '',
  },
  plan: {
    icon: '📋',
    label: 'Travel Plan',
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    animation: '',
  },
  complete: {
    icon: '🎉',
    label: 'Complete!',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    animation: '',
  },
  error: {
    icon: '❌',
    label: 'Error',
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    animation: '',
  },
};

export function StatusIndicator({ type, content }) {
  const config = statusConfig[type] || statusConfig.progress;

  return (
    <div className={`flex items-start gap-3 p-4 rounded-xl ${config.bgColor} ${config.animation}`}>
      <span className="text-2xl">{config.icon}</span>
      <div className="flex-1 min-w-0">
        <div className={`font-medium ${config.color}`}>{config.label}</div>
        {content && (
          <div className="text-gray-700 text-sm mt-1 whitespace-pre-wrap">{content}</div>
        )}
      </div>
    </div>
  );
}
