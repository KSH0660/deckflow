'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface SlideVersion {
  version_id: string;
  content: string;
  timestamp: string;
  is_current: boolean;
  created_by: string;
}

interface Slide {
  order: number;
  plan: {
    slide_title: string;
    key_points?: string[];
    data_points?: string[];
    expert_insights?: string[];
  };
  content: {
    html_content: string;
    current_version_id?: string;
  };
  versions?: SlideVersion[];
}

interface DeckData {
  id: string;
  deck_title: string;
  status: string;
  slides: Slide[];
  progress: number;
  step: string;
  created_at: string;
  updated_at?: string;
}

interface DeckStatus {
  deck_id: string;
  status: 'completed' | 'modifying' | 'generating' | 'failed' | 'cancelled';
  slide_count: number;
  progress?: number;
  step?: string;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

export default function DeckPreview() {
  const params = useParams();
  const router = useRouter();
  const deckId = params.id as string;

  const [deckData, setDeckData] = useState<DeckData | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modificationPrompt, setModificationPrompt] = useState('');
  const [isModifying, setIsModifying] = useState(false);
  const [modifyingSlides, setModifyingSlides] = useState<Set<number>>(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [slideVersions, setSlideVersions] = useState<SlideVersion[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);

  useEffect(() => {
    if (deckId) {
      fetchDeckData();
    }
  }, [deckId]);

  // 페이지 포커스 시 상태 재확인
  useEffect(() => {
    const handleFocus = () => {
      if (modifyingSlides.size > 0) {
        fetchDeckData();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [modifyingSlides.size]);

  // 슬라이드 수정 중일 때 상태 폴링
  useEffect(() => {
    if (modifyingSlides.size > 0) {
      const interval = setInterval(async () => {
        const status = await fetchDeckStatus();
        // 덱 상태가 completed이거나 modifying이 아닌 경우 수정 완료로 간주
        if (status && (status.status === 'completed' || status.status !== 'modifying')) {
          console.log('Modification completed, refreshing deck data...');
          // 수정이 완료되면 덱 데이터를 다시 불러오고 수정 중인 슬라이드 목록 초기화
          await fetchDeckData();
          setModifyingSlides(new Set());
        }
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [modifyingSlides.size]);

  const fetchDeckStatus = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/decks/${deckId}`);
      if (response.ok) {
        const status = await response.json();
        return status;
      }
    } catch (error) {
      console.error('Error fetching deck status:', error);
    }
    return null;
  };

  const fetchDeckData = async () => {
    try {
      // 상태도 함께 확인
      const status = await fetchDeckStatus();

      const response = await fetch(`http://localhost:8000/api/v1/decks/${deckId}/data`);
      if (response.ok) {
        const data = await response.json();
        setDeckData(data);

        // 덱 상태가 completed이고 수정 중인 슬라이드가 있다면 수정이 완료된 것으로 간주
        if (status?.status === 'completed' && modifyingSlides.size > 0) {
          console.log('Deck is completed, clearing modifying slides...');
          setModifyingSlides(new Set());
        }

        // 덱이 완료되지 않은 경우에만 상태 페이지로 리다이렉트
        if (data.status !== 'completed' && data.status !== 'modifying') {
          router.push(`/decks/${deckId}/status`);
          return;
        }
      } else if (response.status === 404) {
        setError('덱을 찾을 수 없습니다.');
      } else {
        setError('덱 데이터를 불러오는데 실패했습니다.');
      }
    } catch (error) {
      console.error('Error fetching deck data:', error);
      setError('네트워크 오류가 발생했습니다.');
    }
    setIsLoading(false);
  };

  const nextSlide = () => {
    if (deckData && currentSlide < deckData.slides.length - 1) {
      const newSlide = currentSlide + 1;
      setCurrentSlide(newSlide);
      if (showVersionHistory) {
        fetchSlideVersions(newSlide + 1);
      }
    }
  };

  const prevSlide = () => {
    if (currentSlide > 0) {
      const newSlide = currentSlide - 1;
      setCurrentSlide(newSlide);
      if (showVersionHistory) {
        fetchSlideVersions(newSlide + 1);
      }
    }
  };

  const handleModifySlide = async () => {
    if (!modificationPrompt.trim()) {
      return;
    }

    const slideNumber = currentSlide + 1;
    setIsModifying(true);

    try {
      const response = await fetch(`http://localhost:8000/api/v1/decks/${deckId}/slides/${slideNumber}/modify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          modification_prompt: modificationPrompt.trim(),
        }),
      });

      if (response.ok) {
        // 현재 슬라이드를 수정 중인 슬라이드 목록에 추가
        setModifyingSlides(prev => new Set([...prev, slideNumber]));
        // 프롬프트 초기화
        setModificationPrompt('');
      } else {
        alert('슬라이드 수정 요청에 실패했습니다.');
      }
    } catch (error) {
      console.error('Error modifying slide:', error);
      alert('네트워크 오류가 발생했습니다.');
    }
    setIsModifying(false);
  };

  const fetchSlideVersions = async (slideOrder: number) => {
    setLoadingVersions(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/decks/${deckId}/slides/${slideOrder}/versions`);
      if (response.ok) {
        const data = await response.json();
        setSlideVersions(data.versions || []);
      } else {
        console.error('Failed to fetch slide versions');
        setSlideVersions([]);
      }
    } catch (error) {
      console.error('Error fetching slide versions:', error);
      setSlideVersions([]);
    }
    setLoadingVersions(false);
  };

  const revertToVersion = async (versionId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/decks/${deckId}/slides/${currentSlide + 1}/revert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          version_id: versionId,
        }),
      });

      if (response.ok) {
        alert('버전이 복원되었습니다!');
        // Refresh deck data to show the reverted content
        await fetchDeckData();
        // Refresh version history
        await fetchSlideVersions(currentSlide + 1);
      } else {
        alert('버전 복원에 실패했습니다.');
      }
    } catch (error) {
      console.error('Error reverting to version:', error);
      alert('네트워크 오류가 발생했습니다.');
    }
  };

  const handleSaveSlide = async () => {
    setIsSaving(true);
    try {
      // Get the current slide's HTML from iframe
      const iframe = document.querySelector('iframe') as HTMLIFrameElement;
      let htmlContent = '';

      if (iframe && iframe.contentDocument) {
        // Apply any TinyMCE changes first
        if ((iframe.contentWindow as typeof window & { tinymce?: { editors: Array<{ undoManager?: { add: () => void } }> } })?.tinymce?.editors) {
          const editors = (iframe.contentWindow as typeof window & { tinymce: { editors: Array<{ undoManager?: { add: () => void } }> } }).tinymce.editors;
          for (let i = 0; i < editors.length; i++) {
            const ed = editors[i];
            if (ed && ed.undoManager && ed.undoManager.add) {
              ed.undoManager.add();
            }
          }
        }

        // Get the complete HTML
        htmlContent = '<!DOCTYPE html>\n' + iframe.contentDocument.documentElement.outerHTML;
      } else {
        throw new Error('iframe 접근 실패');
      }

      // Save to backend
      const response = await fetch(`http://localhost:8000/api/v1/save?deck_id=${deckId}&slide_order=${currentSlide + 1}`, {
        method: 'POST',
        headers: {'Content-Type': 'text/html;charset=utf-8'},
        body: htmlContent
      });

      if (response.ok) {
        alert('슬라이드가 저장되었습니다!');
        // Refresh version history after saving
        if (showVersionHistory) {
          await fetchSlideVersions(currentSlide + 1);
        }
      } else {
        throw new Error('서버 저장 실패');
      }

    } catch (error) {
      console.error('Save error:', error);
      alert('저장 중 오류가 발생했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-4"></div>
          <p className="text-gray-600">덱 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="text-4xl mb-4">❌</div>
          <h2 className="text-xl font-medium text-gray-800 mb-2">오류가 발생했습니다</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => router.back()}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            돌아가기
          </button>
        </div>
      </div>
    );
  }

  if (!deckData || !deckData.slides.length) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="text-4xl mb-4">📝</div>
          <h2 className="text-xl font-medium text-gray-800 mb-2">슬라이드가 없습니다</h2>
          <p className="text-gray-600">이 덱에는 표시할 슬라이드가 없습니다.</p>
        </div>
      </div>
    );
  }

  const currentSlideData = deckData.slides[currentSlide];

  return (
    <div className="h-full bg-gray-100 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ChevronLeftIcon className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">{deckData.deck_title}</h1>
              <div className="flex items-center gap-2">
                <p className="text-sm text-gray-500">
                  {currentSlide + 1} / {deckData.slides.length} 슬라이드
                </p>
                {modifyingSlides.has(currentSlide + 1) && (
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
              onClick={() => {
                setShowVersionHistory(!showVersionHistory);
                if (!showVersionHistory) {
                  fetchSlideVersions(currentSlide + 1);
                }
              }}
              className="px-4 py-2 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              버전 기록
            </button>
            <div className="flex items-center gap-2">
              <button
                onClick={handleSaveSlide}
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

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Slide Content */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="bg-white rounded-lg shadow-lg max-w-4xl w-full aspect-[16/9] relative overflow-hidden">
            {currentSlideData.content?.html_content ? (
              <iframe
                srcDoc={currentSlideData.content.html_content}
                className="w-full h-full border-0"
                title={`슬라이드 ${currentSlide + 1}`}
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-500">
                슬라이드 내용을 불러오는 중...
              </div>
            )}
          </div>
        </div>

        {/* Side Panel */}
        <div className="w-80 bg-white border-l border-gray-200 p-6">
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              슬라이드 {currentSlide + 1}
            </h3>
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
              {(!currentSlideData.plan?.key_points && !currentSlideData.plan?.data_points && !currentSlideData.plan?.expert_insights) && (
                <li className="text-gray-500">내용을 불러오는 중...</li>
              )}
            </ul>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button
              onClick={prevSlide}
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
              onClick={nextSlide}
              disabled={currentSlide === deckData.slides.length - 1}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed rounded-lg transition-colors"
            >
              다음
              <ChevronRightIcon className="w-4 h-4" />
            </button>
          </div>

          {/* Version History or Slide Thumbnails */}
          <div className="mt-6">
            {showVersionHistory ? (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">버전 기록</h4>
                    <p className="text-xs text-gray-500 mt-1">저장 버튼으로 생성된 영구 버전</p>
                  </div>
                  <button
                    onClick={() => setShowVersionHistory(false)}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
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
                    {slideVersions.map((version, index) => (
                      <div
                        key={version.version_id}
                        className={`p-3 rounded-lg border ${
                          version.is_current
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 bg-white'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-xs font-medium text-gray-900">
                            {version.is_current ? '현재 버전' : `버전 ${index + 1}`}
                          </div>
                          {!version.is_current && (
                            <button
                              onClick={() => revertToVersion(version.version_id)}
                              className="text-xs px-2 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded transition-colors"
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
                  <div className="text-center py-4 text-sm text-gray-500">
                    아직 저장된 버전이 없습니다.
                  </div>
                )}
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <h5 className="text-xs font-medium text-blue-900 mb-2">💡 버전 관리 안내</h5>
                  <div className="text-xs text-blue-700 space-y-1">
                    <div><strong>실시간 편집:</strong> Ctrl+Z/Ctrl+Shift+Z로 실행취소/다시실행</div>
                    <div><strong>영구 저장:</strong> 저장 버튼으로 새 버전 생성</div>
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
                        if (showVersionHistory) {
                          fetchSlideVersions(index + 1);
                        }
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
                      <div className="text-xs text-gray-500 mt-1">
                        슬라이드 {index + 1}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>


      {/* Bottom Prompt-style Modification Section */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg">
        <div className="max-w-6xl mx-auto p-4">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <textarea
                value={modificationPrompt}
                onChange={(e) => setModificationPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey && modificationPrompt.trim() && !modifyingSlides.has(currentSlide + 1)) {
                    e.preventDefault();
                    handleModifySlide();
                  }
                }}
                placeholder="💬 이 슬라이드를 어떻게 수정할까요? 자연어로 설명해주세요. (Enter로 실행, Shift+Enter로 줄바꿈)"
                className="w-full p-3 border border-gray-300 rounded-lg text-sm resize-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500 bg-gray-50"
                rows={2}
                disabled={modifyingSlides.has(currentSlide + 1)}
              />
              {modifyingSlides.has(currentSlide + 1) && (
                <div className="mt-2 flex items-center gap-2 text-sm text-orange-600">
                  <div className="w-4 h-4 border-2 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
                  <span>AI가 슬라이드를 수정하고 있습니다...</span>
                </div>
              )}
            </div>
            <button
              onClick={handleModifySlide}
              disabled={modifyingSlides.has(currentSlide + 1) || !modificationPrompt.trim()}
              className={`px-6 py-3 rounded-lg transition-colors flex items-center gap-2 ${
                modifyingSlides.has(currentSlide + 1) || !modificationPrompt.trim()
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-orange-600 hover:bg-orange-700 text-white shadow-md hover:shadow-lg'
              }`}
            >
              <span>✨</span>
              {modifyingSlides.has(currentSlide + 1) ? '수정 중...' : 'AI 수정'}
            </button>
          </div>
        </div>
      </div>

      {/* Add bottom padding to prevent overlap with fixed prompt */}
      <div className="h-24"></div>
    </div>
  );
}
