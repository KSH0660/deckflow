/**
 * Layout, Color, and Persona preferences for deck generation
 */

export interface LayoutConfig {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface ColorConfig {
  id: string;
  name: string;
  description: string;
  preview: string; // CSS color for preview
}

export interface PersonaConfig {
  id: string;
  name: string;
  description: string;
  icon: string;
}

// Layout Preferences
export const LAYOUTS: Record<string, LayoutConfig> = {
  'minimal': {
    id: 'minimal',
    name: '미니멀',
    description: '깔끔하고 간단한 레이아웃',
    icon: '📝'
  },
  'professional': {
    id: 'professional',
    name: '프로페셔널',
    description: '기업용 구조화된 레이아웃',
    icon: '💼'
  },
  'creative': {
    id: 'creative',
    name: '크리에이티브',
    description: '역동적이고 현대적인 레이아웃',
    icon: '🎨'
  }
};

// Color Preferences
export const COLORS: Record<string, ColorConfig> = {
  'professional_blue': {
    id: 'professional_blue',
    name: '프로페셔널 블루',
    description: '신뢰감 있는 파란색 조합',
    preview: '#1e40af'
  },
  'warm_corporate': {
    id: 'warm_corporate',
    name: '웜 코퍼릿',
    description: '따뜻한 기업 색상 조합',
    preview: '#dc2626'
  },
  'modern_green': {
    id: 'modern_green',
    name: '모던 그린',
    description: '현대적인 녹색 조합',
    preview: '#059669'
  }
};

// Persona Preferences (spacing and typography)
export const PERSONAS: Record<string, PersonaConfig> = {
  'compact': {
    id: 'compact',
    name: '컴팩트',
    description: '밀도 높은 정보 전달',
    icon: '📋'
  },
  'balanced': {
    id: 'balanced',
    name: '밸런스드',
    description: '균형잡힌 일반적 사용',
    icon: '⚖️'
  },
  'spacious': {
    id: 'spacious',
    name: '스페이셔스',
    description: '여유로운 편안한 읽기',
    icon: '🌅'
  }
};

// Default values
export const DEFAULT_LAYOUT = 'professional';
export const DEFAULT_COLOR = 'professional_blue';
export const DEFAULT_PERSONA = 'balanced';

// Helper functions
export const getLayoutList = () => Object.values(LAYOUTS);
export const getColorList = () => Object.values(COLORS);
export const getPersonaList = () => Object.values(PERSONAS);
