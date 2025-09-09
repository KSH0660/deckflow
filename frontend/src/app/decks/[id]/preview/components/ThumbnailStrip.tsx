'use client';

import type { DeckData } from '../types';
import { useEffect, useRef } from 'react';

interface ThumbnailStripProps {
  deckData: DeckData;
  currentSlide: number;
  setCurrentSlide: (i: number) => void;
}

export default function ThumbnailStrip({ deckData, currentSlide, setCurrentSlide }: ThumbnailStripProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const active = container.querySelector('[data-active="true"]') as HTMLElement | null;
    if (active) {
      const left = active.offsetLeft - container.clientWidth / 2 + active.clientWidth / 2;
      container.scrollTo({ left, behavior: 'smooth' });
    }
  }, [currentSlide]);

  return (
    <div className="border-b border-gray-200 bg-white">
      <div className="px-4 py-3">
        <div ref={containerRef} className="flex gap-3 overflow-x-auto no-scrollbar">
          {deckData.slides.map((slide, index) => (
            <button
              key={index}
              data-active={index === currentSlide}
              onClick={() => setCurrentSlide(index)}
              className={`shrink-0 rounded-md border relative transition-all text-left ${
                index === currentSlide
                  ? 'border-orange-500 ring-2 ring-orange-300'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              style={{ width: 200 }}
              title={slide.plan?.slide_title || `슬라이드 ${index + 1}`}
            >
              <div className="w-[200px] aspect-[16/9] bg-gray-50 rounded-t-md overflow-hidden">
                {slide.content?.html_content ? (
                  <iframe
                    srcDoc={slide.content.html_content}
                    className="w-full h-full border-0 pointer-events-none"
                    title={`thumbnail-${index + 1}`}
                    loading="lazy"
                    sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400 text-xs">
                    미리보기 없음
                  </div>
                )}
              </div>
              <div className="px-2 py-1">
                <div className="text-xs font-medium text-gray-900 truncate">
                  {slide.plan?.slide_title || `슬라이드 ${index + 1}`}
                </div>
                <div className="text-[10px] text-gray-500">슬라이드 {index + 1}</div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
