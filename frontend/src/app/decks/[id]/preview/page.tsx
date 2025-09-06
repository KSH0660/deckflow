'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

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
  };
}

interface DeckData {
  id: string;
  deck_title: string;
  status: string;
  slides: Slide[];
  progress: number;
  step: string;
  created_at: string;
}

export default function DeckPreview() {
  const params = useParams();
  const router = useRouter();
  const deckId = params.id as string;
  
  const [deckData, setDeckData] = useState<DeckData | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (deckId) {
      fetchDeckData();
    }
  }, [deckId]);

  const fetchDeckData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/decks/${deckId}/data`);
      if (response.ok) {
        const data = await response.json();
        setDeckData(data);
        
        // If deck is not completed, redirect to status page
        if (data.status !== 'completed') {
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
      setCurrentSlide(currentSlide + 1);
    }
  };

  const prevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
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
              <p className="text-sm text-gray-500">
                {currentSlide + 1} / {deckData.slides.length} 슬라이드
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
              편집
            </button>
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
                sandbox="allow-scripts"
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

          {/* Slide Thumbnails */}
          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3">슬라이드 목록</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {deckData.slides.map((slide, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentSlide(index)}
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
        </div>
      </div>
    </div>
  );
}