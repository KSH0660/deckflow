'use client';

interface SlideViewerProps {
  html?: string;
  title: string;
  showCode?: boolean;
}

export default function SlideViewer({ html, title, showCode = false }: SlideViewerProps) {
  return (
    <div className="flex-1 flex items-center justify-center p-4 md:p-6">
      {/* <div className="bg-white rounded-lg shadow-lg max-w-6xl w-full aspect-[16/9] relative overflow-hidden"> */}
      <div className="bg-white rounded-lg shadow-lg h-[60vh] w-auto aspect-[16/9] relative overflow-hidden">

        {showCode ? (
          <div className="absolute inset-0 bg-gray-900 text-green-100 text-xs leading-relaxed">
            <pre className="w-full h-full overflow-auto p-3 whitespace-pre-wrap break-words">{html || 'HTML 없음'}</pre>
            <button
              onClick={() => navigator.clipboard.writeText(html || '')}
              className="absolute top-2 right-2 px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 text-xs"
              title="HTML 복사"
            >
              복사
            </button>
          </div>
        ) : html ? (
          <iframe
            srcDoc={html}
            className="w-full h-full border-0"
            title={title}
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500">슬라이드 내용을 불러오는 중...</div>
        )}
      </div>
    </div>
  );
}
