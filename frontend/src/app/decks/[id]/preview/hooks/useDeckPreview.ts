'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { DeckData, DeckStatus, SlideVersion } from '../types';

export function useDeckPreview(deckId: string | undefined) {
  const router = useRouter();

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

  const hasCurrentSlideModifying = useMemo(
    () => modifyingSlides.has(currentSlide + 1),
    [modifyingSlides, currentSlide]
  );

  useEffect(() => {
    if (deckId) {
      fetchDeckData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deckId]);

  // Refresh when window regains focus and modifications are pending
  useEffect(() => {
    const handleFocus = () => {
      if (modifyingSlides.size > 0) {
        fetchDeckData();
      }
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [modifyingSlides.size]);

  // Poll deck status while any slide is being modified
  useEffect(() => {
    if (modifyingSlides.size > 0) {
      const interval = setInterval(async () => {
        const status = await fetchDeckStatus();
        if (status && (status.status === 'completed' || status.status !== 'modifying')) {
          await fetchDeckData();
          setModifyingSlides(new Set());
        }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [modifyingSlides.size]);

  const fetchDeckStatus = async (): Promise<DeckStatus | null> => {
    if (!deckId) return null;
    try {
      const response = await fetch(`http://localhost:8000/api/decks/${deckId}`);
      if (response.ok) {
        const status = (await response.json()) as DeckStatus;
        return status;
      }
    } catch (e) {
      console.error('Error fetching deck status:', e);
    }
    return null;
  };

  const fetchDeckData = async () => {
    if (!deckId) return;
    try {
      const status = await fetchDeckStatus();
      const response = await fetch(`http://localhost:8000/api/decks/${deckId}/data`);
      if (response.ok) {
        const data = (await response.json()) as DeckData;
        setDeckData(data);

        if (status?.status === 'completed' && modifyingSlides.size > 0) {
          setModifyingSlides(new Set());
        }

        if (data.status !== 'completed' && data.status !== 'modifying') {
          router.push(`/decks/${deckId}/status`);
          return;
        }
      } else if (response.status === 404) {
        setError('덱을 찾을 수 없습니다.');
      } else {
        setError('덱 데이터를 불러오는데 실패했습니다.');
      }
    } catch (e) {
      console.error('Error fetching deck data:', e);
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
    if (!deckId || !modificationPrompt.trim()) return;
    const slideNumber = currentSlide + 1;
    setIsModifying(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/decks/${deckId}/slides/${slideNumber}/modify`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ modification_prompt: modificationPrompt.trim() }),
        }
      );
      if (response.ok) {
        setModifyingSlides((prev) => new Set([...prev, slideNumber]));
        setModificationPrompt('');
      } else {
        alert('슬라이드 수정 요청에 실패했습니다.');
      }
    } catch (e) {
      console.error('Error modifying slide:', e);
      alert('네트워크 오류가 발생했습니다.');
    }
    setIsModifying(false);
  };

  const fetchSlideVersions = async (slideOrder: number) => {
    if (!deckId) return;
    setLoadingVersions(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/decks/${deckId}/slides/${slideOrder}/versions`
      );
      if (response.ok) {
        const data = (await response.json()) as { versions?: SlideVersion[] };
        setSlideVersions(data.versions || []);
      } else {
        console.error('Failed to fetch slide versions');
        setSlideVersions([]);
      }
    } catch (e) {
      console.error('Error fetching slide versions:', e);
      setSlideVersions([]);
    }
    setLoadingVersions(false);
  };

  const revertToVersion = async (versionId: string) => {
    if (!deckId) return;
    try {
      const response = await fetch(
        `http://localhost:8000/api/decks/${deckId}/slides/${currentSlide + 1}/revert`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ version_id: versionId }),
        }
      );
      if (response.ok) {
        alert('버전이 복원되었습니다!');
        await fetchDeckData();
        await fetchSlideVersions(currentSlide + 1);
      } else {
        alert('버전 복원에 실패했습니다.');
      }
    } catch (e) {
      console.error('Error reverting to version:', e);
      alert('네트워크 오류가 발생했습니다.');
    }
  };

  const handleSaveSlide = async () => {
    if (!deckId) return;
    setIsSaving(true);
    try {
      const iframe = document.querySelector('iframe') as HTMLIFrameElement | null;
      let htmlContent = '';
      if (iframe && iframe.contentDocument) {
        const w = iframe.contentWindow as typeof window & {
          tinymce?: { editors: Array<{ undoManager?: { add: () => void } }> };
        };
        if (w?.tinymce?.editors) {
          const editors = w.tinymce.editors;
          for (let i = 0; i < editors.length; i++) {
            const ed = editors[i];
            if (ed && ed.undoManager && ed.undoManager.add) {
              ed.undoManager.add();
            }
          }
        }
        htmlContent = '<!DOCTYPE html>\n' + iframe.contentDocument.documentElement.outerHTML;
      } else {
        throw new Error('iframe 접근 실패');
      }

      const response = await fetch(
        `http://localhost:8000/api/save?deck_id=${deckId}&slide_order=${currentSlide + 1}`,
        { method: 'POST', headers: { 'Content-Type': 'text/html;charset=utf-8' }, body: htmlContent }
      );
      if (response.ok) {
        alert('슬라이드가 저장되었습니다!');
        if (showVersionHistory) {
          await fetchSlideVersions(currentSlide + 1);
        }
      } else {
        throw new Error('서버 저장 실패');
      }
    } catch (e) {
      console.error('Save error:', e);
      alert('저장 중 오류가 발생했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  return {
    // data
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
    // actions
    nextSlide,
    prevSlide,
    handleModifySlide,
    fetchSlideVersions,
    revertToVersion,
    handleSaveSlide,
    fetchDeckData,
  } as const;
}
