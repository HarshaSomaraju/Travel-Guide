import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function TravelPlan({ content, isFinal }) {
  if (!content) return null;

  return (
    <div className={`rounded-xl overflow-hidden border ${isFinal ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-white'}`}>
      {/* Header */}
      <div className={`px-4 py-3 ${isFinal ? 'bg-green-100' : 'bg-gray-100'} border-b ${isFinal ? 'border-green-200' : 'border-gray-200'}`}>
        <div className="flex items-center gap-2">
          <span className="text-xl">{isFinal ? '🎉' : '📋'}</span>
          <h3 className="font-semibold text-gray-900">
            {isFinal ? 'Your Travel Plan is Ready!' : 'Draft Travel Plan'}
          </h3>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 prose prose-sm max-w-none overflow-x-auto">
        <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
      </div>
    </div>
  );
}
