'use client';

import { useState, useRef } from 'react';

export interface FileInfo {
  filename: string;
  content_type: string;
  size: number;
  extracted_text: string;
}

interface FileUploadProps {
  onFilesChange: (files: FileInfo[]) => void;
  disabled?: boolean;
}

export default function FileUpload({ onFilesChange, disabled = false }: FileUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<FileInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = ['.txt', '.md', '.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.gif', '.bmp'];
  const maxFileSize = 10 * 1024 * 1024; // 10MB

  const validateFile = (file: File): string | null => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedExtensions.includes(extension)) {
      return `지원하지 않는 파일 형식입니다. 허용된 확장자: ${allowedExtensions.join(', ')}`;
    }
    if (file.size > maxFileSize) {
      return `파일 크기가 너무 큽니다. 최대 10MB까지 지원합니다.`;
    }
    return null;
  };

  const uploadFile = async (file: File): Promise<FileInfo> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('http://localhost:8000/api/v1/files/upload', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '파일 업로드에 실패했습니다.');
    }

    return response.json();
  };

  const handleFileChange = async (files: FileList | null) => {
    if (!files || files.length === 0 || disabled) return;

    setIsUploading(true);
    const newFiles: FileInfo[] = [];

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // 파일 검증
        const validationError = validateFile(file);
        if (validationError) {
          alert(`${file.name}: ${validationError}`);
          continue;
        }

        try {
          const fileInfo = await uploadFile(file);
          newFiles.push(fileInfo);
        } catch (error) {
          console.error(`Error uploading ${file.name}:`, error);
          alert(`${file.name} 업로드 실패: ${error}`);
        }
      }

      const updatedFiles = [...uploadedFiles, ...newFiles];
      setUploadedFiles(updatedFiles);
      onFilesChange(updatedFiles);
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = (index: number) => {
    const updatedFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(updatedFiles);
    onFilesChange(updatedFiles);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (!disabled) {
      handleFileChange(e.dataTransfer.files);
    }
  };

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="space-y-4">
      {/* File Upload Area */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${isDragOver 
            ? 'border-orange-400 bg-orange-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={allowedExtensions.join(',')}
          onChange={(e) => handleFileChange(e.target.files)}
          className="hidden"
          disabled={disabled}
        />
        
        {isUploading ? (
          <div className="flex flex-col items-center">
            <svg className="w-8 h-8 text-orange-500 animate-spin mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <p className="text-gray-600">파일 업로드 중...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <svg className="w-8 h-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-gray-600 mb-1">파일을 드래그하거나 클릭하여 업로드</p>
            <p className="text-xs text-gray-500">
              지원 형식: {allowedExtensions.join(', ')} (최대 10MB)
            </p>
          </div>
        )}
      </div>

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">업로드된 파일들:</h4>
          {uploadedFiles.map((file, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.filename}</p>
                  <p className="text-xs text-gray-500">{file.content_type} • {(file.size / 1024).toFixed(1)}KB</p>
                </div>
              </div>
              <button
                onClick={() => removeFile(index)}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
                disabled={disabled}
              >
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}