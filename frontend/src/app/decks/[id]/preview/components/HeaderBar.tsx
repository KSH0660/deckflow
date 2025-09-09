'use client';

import { ChevronLeftIcon } from '@heroicons/react/24/outline';

interface HeaderBarProps {
  deckTitle: string;
  current: number;
  total: number;
  isCurrentSlideModifying: boolean;
  showVersionHistory: boolean;
  onToggleVersionHistory: () => void;
  onSave: () => void;
  isSaving: boolean;
  onBack: () => void;
}

export default function HeaderBar({
  deckTitle,
  current,
  total,
  isCurrentSlideModifying,
  showVersionHistory,
  onToggleVersionHistory,
  onSave,
  isSaving,
  onBack,
}: HeaderBarProps) {
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <ChevronLeftIcon className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">{deckTitle}</h1>
            <div className="flex items-center gap-2">
              <p className="text-sm text-gray-500">
                {current + 1} / {total} 슬라이드
              </p>
              {isCurrentSlideModifying && (
                <div className="flex items-center gap-1 px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs">
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-orange-600"></div>
                  <span>이 슬라이드 수정 중...</span>
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onToggleVersionHistory}
            className="px-4 py-2 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            {showVersionHistory ? '버전 닫기' : '버전 기록'}
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onSave}
              disabled={isSaving}
              className="px-4 py-2 text-sm bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white rounded-lg transition-colors flex items-center gap-2"
              title="현재 편집 내용을 새 버전으로 저장 (영구 저장)"
            >
              {isSaving && (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              )}
              {isSaving ? '저장 중...' : '저장'}
            </button>
            <div className="text-xs text-gray-500 hidden lg:block">
              편집: Ctrl+Z (실행취소) | Ctrl+Shift+Z (다시실행)
            </div>
          </div>
          <button className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
            내보내기
          </button>
        </div>
      </div>
    </div>
  );
}
