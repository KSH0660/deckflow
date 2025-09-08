'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface Deck {
  deck_id: string;
  title: string;
  status: 'generating' | 'completed' | 'failed' | 'cancelled';
  slide_count: number;
  progress?: number;
  step?: string;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

export default function DecksPage() {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingDecks, setDeletingDecks] = useState<Set<string>>(new Set());
  const router = useRouter();

  const fetchDecks = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/decks?limit=20');
      if (response.ok) {
        const deckList = await response.json();
        
        // For each deck, fetch detailed status if generating or modifying
        const enrichedDecks = await Promise.all(
          deckList.map(async (deck: any) => {
            if (deck.status === 'generating' || deck.status === 'modifying') {
              try {
                const statusResponse = await fetch(`http://localhost:8000/api/v1/decks/${deck.deck_id}`);
                if (statusResponse.ok) {
                  const statusData = await statusResponse.json();
                  return {
                    ...deck,
                    progress: statusData.progress,
                    step: statusData.step,
                    status: statusData.status, // Update status in case it changed
                    slide_count: statusData.slide_count
                  };
                }
              } catch (error) {
                console.error(`Error fetching status for deck ${deck.deck_id}:`, error);
              }
            }
            return deck;
          })
        );
        
        setDecks(enrichedDecks);
      }
    } catch (error) {
      console.error('Error fetching decks:', error);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchDecks();
  }, [fetchDecks]);

  // Separate effect for polling
  useEffect(() => {
    if (decks.some(deck => deck.status === 'generating' || deck.status === 'modifying')) {
      const interval = setInterval(fetchDecks, 3000);
      return () => clearInterval(interval);
    }
  }, [decks, fetchDecks]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'generating':
        return 'bg-blue-100 text-blue-800';
      case 'modifying':
        return 'bg-orange-100 text-orange-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '완료됨';
      case 'generating':
        return '생성 중';
      case 'modifying':
        return '수정 중';
      case 'failed':
        return '실패';
      case 'cancelled':
        return '취소됨';
      default:
        return status;
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    
    // 디버깅을 위한 로그
    console.log('Duration calculation:', {
      startTime,
      endTime,
      start: start.toISOString(),
      end: end.toISOString(),
      diffMs,
      diffSeconds
    });
    
    if (diffSeconds < 0) {
      return '계산 오류';
    }
    
    if (diffSeconds < 60) {
      return `${diffSeconds}초`;
    } else if (diffSeconds < 3600) {
      const minutes = Math.floor(diffSeconds / 60);
      const seconds = diffSeconds % 60;
      return seconds > 0 ? `${minutes}분 ${seconds}초` : `${minutes}분`;
    } else {
      const hours = Math.floor(diffSeconds / 3600);
      const minutes = Math.floor((diffSeconds % 3600) / 60);
      return minutes > 0 ? `${hours}시간 ${minutes}분` : `${hours}시간`;
    }
  };

  const handleDoubleClick = (deck: Deck) => {
    // Only navigate to preview for completed or modifying decks
    if (deck.status === 'completed' || deck.status === 'modifying') {
      router.push(`/decks/${deck.deck_id}/preview`);
    }
  };

  const handleCancel = async (deckId: string, deckTitle: string) => {
    const confirmed = window.confirm(`"${deckTitle}" 덱 생성을 취소하시겠습니까?`);
    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/v1/decks/${deckId}/cancel`, {
        method: 'POST',
      });
      if (response.ok) {
        // Refresh decks after cancellation
        fetchDecks();
      }
    } catch (error) {
      console.error('Error cancelling deck:', error);
    }
  };

  const handleDeleteDeck = async (deckId: string, deckTitle: string) => {
    const confirmed = window.confirm(`"${deckTitle}"을(를) 정말 삭제하시겠습니까?\n\n삭제된 덱은 복구할 수 없습니다.`);
    if (!confirmed) return;
    
    setDeletingDecks(prev => new Set([...prev, deckId]));
    try {
      const response = await fetch(`http://localhost:8000/api/v1/decks/${deckId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        // Remove deck from local state
        setDecks(prev => prev.filter(deck => deck.deck_id !== deckId));
        alert('덱이 성공적으로 삭제되었습니다.');
      } else {
        throw new Error('삭제 실패');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('덱 삭제 중 오류가 발생했습니다.');
    } finally {
      setDeletingDecks(prev => {
        const newSet = new Set(prev);
        newSet.delete(deckId);
        return newSet;
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-light text-gray-800">덱 목록</h1>
          <p className="text-gray-600 mt-2">생성된 프레젠테이션 덱들을 확인하세요</p>
        </div>

        {decks.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">📝</div>
            <h3 className="text-xl font-medium text-gray-600 mb-2">아직 생성된 덱이 없습니다</h3>
            <p className="text-gray-500 mb-6">새로운 프레젠테이션을 만들어보세요</p>
            <Link 
              href="/"
              className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-lg transition-colors inline-block"
            >
              새 덱 만들기
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {decks.map((deck) => (
              <div
                key={deck.deck_id}
                className={`bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow ${
                  (deck.status === 'completed' || deck.status === 'modifying') 
                    ? 'cursor-pointer' 
                    : ''
                }`}
                onDoubleClick={() => handleDoubleClick(deck)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-medium text-gray-900 truncate max-w-md">
                        {deck.title}
                      </h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getStatusColor(deck.status)}`}>
                        {getStatusText(deck.status)}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                      <span>{deck.slide_count}개 슬라이드</span>
                      <span>•</span>
                      <span>{new Date(deck.created_at).toLocaleDateString('ko-KR')}</span>
                      {(deck.status === 'completed' || deck.status === 'failed' || deck.status === 'cancelled') && (
                        <>
                          <span>•</span>
                          <span className="font-medium text-blue-600">
                            소요시간: {formatDuration(deck.created_at, deck.completed_at || deck.updated_at)}
                          </span>
                        </>
                      )}
                      {deck.status === 'generating' && (
                        <>
                          <span>•</span>
                          <span className="text-orange-600">
                            진행시간: {formatDuration(deck.created_at)}
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {(deck.status === 'completed' || deck.status === 'modifying') && (
                      <>
                        <Link 
                          href={`/decks/${deck.deck_id}/preview`}
                          className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                          title="미리보기"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        </Link>
                        <button 
                          disabled={deck.status === 'modifying'}
                          className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                            deck.status === 'modifying'
                              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                              : 'bg-blue-600 hover:bg-blue-700 text-white'
                          }`}
                        >
                          내보내기
                        </button>
                        <button 
                          onClick={() => handleDeleteDeck(deck.deck_id, deck.title)}
                          disabled={deletingDecks.has(deck.deck_id)}
                          className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors flex items-center gap-1"
                          title="삭제"
                        >
                          {deletingDecks.has(deck.deck_id) ? (
                            <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
                          ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          )}
                        </button>
                      </>
                    )}
                    
                    {deck.status === 'generating' && (
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2 text-sm text-blue-600">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                            {deck.step || '생성 중...'}
                          </div>
                          <button 
                            onClick={() => handleCancel(deck.deck_id, deck.title)}
                            className="px-3 py-1 text-xs text-red-600 hover:bg-red-50 border border-red-200 rounded-lg transition-colors"
                          >
                            취소
                          </button>
                        </div>
                        {deck.progress && (
                          <div className="w-32">
                            <div className="flex justify-between text-xs text-gray-500 mb-1">
                              <span>진행률</span>
                              <span>{deck.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                                style={{ width: `${deck.progress}%` }}
                              ></div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {(deck.status === 'failed' || deck.status === 'cancelled') && (
                      <button 
                        onClick={() => handleDeleteDeck(deck.deck_id, deck.title)}
                        disabled={deletingDecks.has(deck.deck_id)}
                        className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors flex items-center gap-1"
                        title="삭제"
                      >
                        {deletingDecks.has(deck.deck_id) ? (
                          <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}