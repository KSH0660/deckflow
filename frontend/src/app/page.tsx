'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import FileUpload, { FileInfo } from '@/components/FileUpload';
import { 
  LAYOUTS, COLORS, PERSONAS,
  DEFAULT_LAYOUT, DEFAULT_COLOR, DEFAULT_PERSONA,
  getLayoutList, getColorList, getPersonaList
} from '@/constants/preferences';

export default function Home() {
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [showFileUpload, setShowFileUpload] = useState(false);
  
  // Preferences state
  const [selectedLayout, setSelectedLayout] = useState(DEFAULT_LAYOUT);
  const [selectedColor, setSelectedColor] = useState(DEFAULT_COLOR);
  const [selectedPersona, setSelectedPersona] = useState(DEFAULT_PERSONA);
  
  // UI state for selectors
  const [showLayoutSelector, setShowLayoutSelector] = useState(false);
  const [showColorSelector, setShowColorSelector] = useState(false);
  const [showPersonaSelector, setShowPersonaSelector] = useState(false);

  const submitPrompt = async () => {
    if (!prompt.trim()) return;
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/decks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          files,
          style: { 
            layout_preference: selectedLayout,
            color_preference: selectedColor,
            persona_preference: selectedPersona
          }
        }),
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
                {/* File Upload Button */}
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

                {/* Layout Selector */}
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setShowLayoutSelector(!showLayoutSelector)}
                    className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
                      showLayoutSelector
                        ? 'bg-purple-100 text-purple-600'
                        : 'hover:bg-gray-100 text-gray-500'
                    }`}
                    title="레이아웃 선택"
                  >
                    <span className="text-sm">{LAYOUTS[selectedLayout].icon}</span>
                    <span className="text-xs font-medium">{LAYOUTS[selectedLayout].name}</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {showLayoutSelector && (
                    <div className="absolute top-full left-0 mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                      <div className="p-3 border-b border-gray-100">
                        <h3 className="text-sm font-semibold text-gray-700">레이아웃 선택</h3>
                      </div>
                      {getLayoutList().map((layout) => (
                        <button
                          key={layout.id}
                          type="button"
                          onClick={() => {
                            setSelectedLayout(layout.id);
                            setShowLayoutSelector(false);
                          }}
                          className={`w-full flex items-start gap-3 p-3 text-left hover:bg-gray-50 transition-colors ${
                            selectedLayout === layout.id ? 'bg-purple-50' : ''
                          }`}
                        >
                          <span className="text-lg">{layout.icon}</span>
                          <div>
                            <div className="text-sm font-medium text-gray-800">{layout.name}</div>
                            <div className="text-xs text-gray-500">{layout.description}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Color Selector */}
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setShowColorSelector(!showColorSelector)}
                    className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
                      showColorSelector
                        ? 'bg-green-100 text-green-600'
                        : 'hover:bg-gray-100 text-gray-500'
                    }`}
                    title="색상 조합 선택"
                  >
                    <div 
                      className="w-4 h-4 rounded-full border border-gray-300"
                      style={{ backgroundColor: COLORS[selectedColor].preview }}
                    />
                    <span className="text-xs font-medium">{COLORS[selectedColor].name}</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {showColorSelector && (
                    <div className="absolute top-full left-0 mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                      <div className="p-3 border-b border-gray-100">
                        <h3 className="text-sm font-semibold text-gray-700">색상 조합 선택</h3>
                      </div>
                      {getColorList().map((color) => (
                        <button
                          key={color.id}
                          type="button"
                          onClick={() => {
                            setSelectedColor(color.id);
                            setShowColorSelector(false);
                          }}
                          className={`w-full flex items-start gap-3 p-3 text-left hover:bg-gray-50 transition-colors ${
                            selectedColor === color.id ? 'bg-green-50' : ''
                          }`}
                        >
                          <div 
                            className="w-6 h-6 rounded-full border border-gray-300 mt-0.5"
                            style={{ backgroundColor: color.preview }}
                          />
                          <div>
                            <div className="text-sm font-medium text-gray-800">{color.name}</div>
                            <div className="text-xs text-gray-500">{color.description}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Persona Selector */}
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setShowPersonaSelector(!showPersonaSelector)}
                    className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
                      showPersonaSelector
                        ? 'bg-blue-100 text-blue-600'
                        : 'hover:bg-gray-100 text-gray-500'
                    }`}
                    title="스페이싱 스타일 선택"
                  >
                    <span className="text-sm">{PERSONAS[selectedPersona].icon}</span>
                    <span className="text-xs font-medium">{PERSONAS[selectedPersona].name}</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {showPersonaSelector && (
                    <div className="absolute top-full left-0 mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                      <div className="p-3 border-b border-gray-100">
                        <h3 className="text-sm font-semibold text-gray-700">스페이싱 스타일 선택</h3>
                      </div>
                      {getPersonaList().map((persona) => (
                        <button
                          key={persona.id}
                          type="button"
                          onClick={() => {
                            setSelectedPersona(persona.id);
                            setShowPersonaSelector(false);
                          }}
                          className={`w-full flex items-start gap-3 p-3 text-left hover:bg-gray-50 transition-colors ${
                            selectedPersona === persona.id ? 'bg-blue-50' : ''
                          }`}
                        >
                          <span className="text-lg">{persona.icon}</span>
                          <div>
                            <div className="text-sm font-medium text-gray-800">{persona.name}</div>
                            <div className="text-xs text-gray-500">{persona.description}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
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
