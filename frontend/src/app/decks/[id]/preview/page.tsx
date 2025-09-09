'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';
import HeaderBar from './components/HeaderBar';
import SlideViewer from './components/SlideViewer';
import SidePanel from './components/SidePanel';
import BottomModifyBar from './components/BottomModifyBar';
import ThumbnailStrip from './components/ThumbnailStrip';
import { useDeckPreview } from './hooks/useDeckPreview';

export default function DeckPreview() {
  const params = useParams();
  const router = useRouter();
  const deckId = params.id as string;
  const [showHtml, setShowHtml] = useState(false);

  const {
    deckData,
    isLoading,
    error,
    currentSlide,
    setCurrentSlide,
    modificationPrompt,
    setModificationPrompt,
    isModifying,
    modifyingSlides,
    isSaving,
    showVersionHistory,
    setShowVersionHistory,
    slideVersions,
    loadingVersions,
    hasCurrentSlideModifying,
    nextSlide,
    prevSlide,
    handleModifySlide,
    fetchSlideVersions,
    revertToVersion,
    handleSaveSlide,
  } = useDeckPreview(deckId);

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
      <HeaderBar
        deckTitle={deckData.deck_title}
        current={currentSlide}
        total={deckData.slides.length}
        isCurrentSlideModifying={hasCurrentSlideModifying}
        showVersionHistory={showVersionHistory}
        onToggleVersionHistory={() => {
          setShowVersionHistory(!showVersionHistory);
          if (!showVersionHistory) fetchSlideVersions(currentSlide + 1);
        }}
        showHtml={showHtml}
        onToggleHtml={() => setShowHtml((v) => !v)}
        onSave={handleSaveSlide}
        isSaving={isSaving}
        onBack={() => router.back()}
      />

      {/* Top thumbnails (gallery style) */}
      <ThumbnailStrip deckData={deckData} currentSlide={currentSlide} setCurrentSlide={setCurrentSlide} />

      <div className="flex-1 flex">
        <SlideViewer
          html={currentSlideData.content?.html_content}
          title={`슬라이드 ${currentSlide + 1}`}
          showCode={showHtml}
        />

        <SidePanel
          deckData={deckData}
          currentSlide={currentSlide}
          setCurrentSlide={setCurrentSlide}
          onPrev={prevSlide}
          onNext={nextSlide}
          showVersionHistory={showVersionHistory}
          closeVersionHistory={() => setShowVersionHistory(false)}
          slideVersions={slideVersions}
          loadingVersions={loadingVersions}
          fetchSlideVersions={fetchSlideVersions}
          revertToVersion={revertToVersion}
        />
      </div>

      <BottomModifyBar
        value={modificationPrompt}
        onChange={setModificationPrompt}
        onSubmit={handleModifySlide}
        disabled={modifyingSlides.has(currentSlide + 1)}
        isWorking={isModifying || modifyingSlides.has(currentSlide + 1)}
      />

      <div className="h-24"></div>
    </div>
  );
}
