'use client';

import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import type { DeckData, SlideVersion } from '../types';

interface SidePanelProps {
  deckData: DeckData;
  currentSlide: number;
  setCurrentSlide: (i: number) => void;
  onPrev: () => void;
  onNext: () => void;
  showVersionHistory: boolean;
  closeVersionHistory: () => void;
  slideVersions: SlideVersion[];
  loadingVersions: boolean;
  fetchSlideVersions: (slideOrder: number) => void;
  revertToVersion: (versionId: string) => void | Promise<void>;
}

export default function SidePanel({
  deckData,
  currentSlide,
  setCurrentSlide,
  onPrev,
  onNext,
  showVersionHistory,
  closeVersionHistory,
  slideVersions,
  loadingVersions,
  fetchSlideVersions,
  revertToVersion,
}: SidePanelProps) {
  const currentSlideData = deckData.slides[currentSlide];

  return (
    <div className="w-80 bg-white border-l border-gray-200 p-6">
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-2">슬라이드 {currentSlide + 1}</h3>
        <h4 className="text-xl font-semibold text-gray-800 mb-4">
          {currentSlideData.plan?.slide_title || `슬라이드 ${currentSlide + 1}`}
        </h4>
      </div>

      <div className="mb-6">
        <h4 className="text-sm font-medium text-gray-700 mb-2">주요 포인트</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          {currentSlideData.plan?.key_points?.map((item, index) => (
            <li key={index} className="flex items-start gap-2">
              <span className="text-orange-500 mt-1">•</span>
              <span>{item}</span>
            </li>
          ))}
          {currentSlideData.plan?.data_points?.map((item, index) => (
            <li key={`data-${index}`} className="flex items-start gap-2">
              <span className="text-blue-500 mt-1">📊</span>
              <span>{item}</span>
            </li>
          ))}
          {currentSlideData.plan?.expert_insights?.map((item, index) => (
            <li key={`insight-${index}`} className="flex items-start gap-2">
              <span className="text-green-500 mt-1">💡</span>
              <span>{item}</span>
            </li>
          ))}
          {!currentSlideData.plan?.key_points &&
            !currentSlideData.plan?.data_points &&
            !currentSlideData.plan?.expert_insights && (
              <li className="text-gray-500">내용을 불러오는 중...</li>
            )}
        </ul>
      </div>

      <div className="flex items-center justify-between">
        <button
          onClick={onPrev}
          disabled={currentSlide === 0}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed rounded-lg transition-colors"
        >
          <ChevronLeftIcon className="w-4 h-4" />
          이전
        </button>
        <span className="text-sm text-gray-500">
          {currentSlide + 1} / {deckData.slides.length}
        </span>
        <button
          onClick={onNext}
          disabled={currentSlide === deckData.slides.length - 1}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed rounded-lg transition-colors"
        >
          다음
          <ChevronRightIcon className="w-4 h-4" />
        </button>
      </div>

      <div className="mt-6">
        {showVersionHistory ? (
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="text-sm font-medium text-gray-700">버전 기록</h4>
                <p className="text-xs text-gray-500 mt-1">저장 버튼으로 생성된 영구 버전</p>
              </div>
              <button onClick={closeVersionHistory} className="text-sm text-gray-500 hover:text-gray-700">
                닫기
              </button>
            </div>
            {loadingVersions ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500 mx-auto"></div>
                <p className="text-sm text-gray-500 mt-2">버전 기록을 불러오는 중...</p>
              </div>
            ) : slideVersions.length > 0 ? (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {slideVersions.map((version) => (
                  <div key={version.version_id} className="p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-gray-700">{version.created_by || '시스템'}</div>
                      {version.is_current ? (
                        <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">현재 버전</span>
                      ) : (
                        <button
                          onClick={() => revertToVersion(version.version_id)}
                          className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        >
                          복원
                        </button>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mb-2">
                      {new Date(version.timestamp).toLocaleString('ko-KR')}
                    </div>
                    <div className="text-xs text-gray-600 max-h-16 overflow-hidden">
                      {version.content.slice(0, 100)}...
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-sm text-gray-500">아직 저장된 버전이 없습니다.</div>
            )}
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <h5 className="text-xs font-medium text-blue-900 mb-2">💡 버전 관리 안내</h5>
              <div className="text-xs text-blue-700 space-y-1">
                <div>
                  <strong>실시간 편집:</strong> Ctrl+Z/Ctrl+Shift+Z로 실행취소/다시실행
                </div>
                <div>
                  <strong>영구 저장:</strong> 저장 버튼으로 새 버전 생성
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">슬라이드 목록</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {deckData.slides.map((slide, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setCurrentSlide(index);
                    if (showVersionHistory) fetchSlideVersions(index + 1);
                  }}
                  className={`w-full p-3 text-left rounded-lg border transition-colors ${
                    index === currentSlide
                      ? 'border-orange-500 bg-orange-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {slide.plan?.slide_title || `슬라이드 ${index + 1}`}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">슬라이드 {index + 1}</div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
