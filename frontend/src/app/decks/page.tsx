'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

interface Deck {
  deck_id: string;
  title: string;
  status: 'generating' | 'completed' | 'failed' | 'cancelled';
  slide_count: number;
  progress?: number;
  step?: string;
  created_at: string;
  updated_at?: string;
}

export default function DecksPage() {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDecks = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/decks?limit=20');
      if (response.ok) {
        const deckList = await response.json();
        
        // For each deck, fetch detailed status if generating
        const enrichedDecks = await Promise.all(
          deckList.map(async (deck: any) => {
            if (deck.status === 'generating') {
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
    if (decks.some(deck => deck.status === 'generating')) {
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
      case 'failed':
        return '실패';
      case 'cancelled':
        return '취소됨';
      default:
        return status;
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
                className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {deck.title}
                      </h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(deck.status)}`}>
                        {getStatusText(deck.status)}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                      <span>{deck.slide_count}개 슬라이드</span>
                      <span>•</span>
                      <span>{new Date(deck.created_at).toLocaleDateString('ko-KR')}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {deck.status === 'completed' && (
                      <>
                        <Link 
                          href={`/decks/${deck.deck_id}/preview`}
                          className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                          미리보기
                        </Link>
                        <button className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                          내보내기
                        </button>
                      </>
                    )}
                    
                    {deck.status === 'generating' && (
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-2 text-sm text-blue-600">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                          {deck.step || '생성 중...'}
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