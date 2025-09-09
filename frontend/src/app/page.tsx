'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import FileUpload, { FileInfo } from '@/components/FileUpload';

export default function Home() {
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [showFileUpload, setShowFileUpload] = useState(false);

  const submitPrompt = async () => {
    if (!prompt.trim()) return;
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/decks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, files }),
      });
      if (response.ok) {
        await response.json();
        router.push('/decks');
      }
    } catch (error) {
      console.error('Error creating deck:', error);
    }
    setIsLoading(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await submitPrompt();
  };

  return (
    <div className="flex flex-col items-center justify-center h-full bg-gray-50 p-8">
      <div className="w-full max-w-4xl">
        {/* Welcome Message */}
        <div className="text-center mb-12">
          <div className="mb-4">
            <span className="text-4xl">🌟</span>
          </div>
          <h1 className="text-4xl font-light text-gray-800 mb-2">
            SUNHO님 다시 오셨네요!
          </h1>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (!isLoading && prompt.trim()) {
                    void submitPrompt();
                  }
                }
              }}
              placeholder="오늘 어떤 프롬프트 드릴까요?"
              className="w-full h-32 p-6 text-lg resize-none border-0 rounded-2xl focus:outline-none focus:ring-0 placeholder-gray-400"
              disabled={isLoading}
            />

            {/* Hint */}
            <div className="px-6 pt-2 pb-1 text-xs text-gray-400">
              Enter 제출 · Shift+Enter 줄바꿈
            </div>

            {/* Toolbar */}
            <div className="flex items-center justify-between p-4 border-t border-gray-100">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowFileUpload(!showFileUpload)}
                  className={`relative p-2 rounded-lg transition-colors ${
                    showFileUpload || files.length > 0
                      ? 'bg-orange-100 text-orange-600'
                      : 'hover:bg-gray-100 text-gray-500'
                  }`}
                  title="파일 첨부"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                  {files.length > 0 && (
                    <span className="absolute -top-1 -right-1 bg-orange-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {files.length}
                    </span>
                  )}
                </button>
                <button
                  type="button"
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  title="검색"
                >
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-sm text-gray-500">
                  Deckflow
                </div>
                <button
                  type="submit"
                  disabled={!prompt.trim() || isLoading}
                  className="bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white p-3 rounded-full transition-colors"
                >
                  {isLoading ? (
                    <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </div>
        </form>

        {/* File Upload Section */}
        {showFileUpload && (
          <div className="mt-4">
            <FileUpload
              onFilesChange={setFiles}
              disabled={isLoading}
            />
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-6 text-center">
          <div className="text-sm text-gray-500">Deckflow</div>
        </div>
      </div>
    </div>
  );
}
