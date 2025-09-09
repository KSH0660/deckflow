'use client';

interface SlideViewerProps {
  html?: string;
  title: string;
}

export default function SlideViewer({ html, title }: SlideViewerProps) {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="bg-white rounded-lg shadow-lg max-w-4xl w-full aspect-[16/9] relative overflow-hidden">
        {html ? (
          <iframe
            srcDoc={html}
            className="w-full h-full border-0"
            title={title}
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500">
            슬라이드 내용을 불러오는 중...
          </div>
        )}
      </div>
    </div>
  );
}
