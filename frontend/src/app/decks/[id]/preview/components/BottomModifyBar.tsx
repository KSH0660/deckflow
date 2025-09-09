'use client';

interface BottomModifyBarProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  isWorking: boolean;
}

export default function BottomModifyBar({ value, onChange, onSubmit, disabled, isWorking }: BottomModifyBarProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg">
      <div className="max-w-6xl mx-auto p-4">
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <textarea
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && value.trim() && !disabled) {
                  e.preventDefault();
                  onSubmit();
                }
              }}
              placeholder="💬 이 슬라이드를 어떻게 수정할까요? 자연어로 설명해주세요. (Enter로 실행, Shift+Enter로 줄바꿈)"
              className="w-full p-3 border border-gray-300 rounded-lg text-sm resize-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500 bg-gray-50"
              rows={2}
              disabled={disabled}
            />
            {isWorking && (
              <div className="mt-2 flex items-center gap-2 text-sm text-orange-600">
                <div className="w-4 h-4 border-2 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
                <span>AI가 슬라이드를 수정하고 있습니다...</span>
              </div>
            )}
          </div>
          <button
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            className={`px-6 py-3 rounded-lg transition-colors flex items-center gap-2 ${
              disabled || !value.trim()
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-orange-600 hover:bg-orange-700 text-white shadow-md hover:shadow-lg'
            }`}
          >
            <span>✨</span>
            {isWorking ? '수정 중...' : 'AI 수정'}
          </button>
        </div>
      </div>
    </div>
  );
}
