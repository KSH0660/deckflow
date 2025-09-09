/**
 * Personas configuration for deck generation
 * These should match the personas defined in the backend
 */

export interface PersonaConfig {
  name: string;
  description: string;
  icon: string;
}

export const PERSONAS: Record<string, PersonaConfig> = {
  'EXPERT_DATA_STRATEGIST': {
    name: '데이터 전략가',
    description: '데이터가 풍부한 전문가급 프레젠테이션',
    icon: '📊'
  },
  'SALES_PITCH_CLOSER': {
    name: '세일즈 전문가',
    description: '설득력 있는 영업 프레젠테이션',
    icon: '💼'
  },
  'TECHNICAL_EDUCATOR': {
    name: '기술 교육자',
    description: '명확한 기술 교육 프레젠테이션',
    icon: '🎯'
  },
  'STARTUP_PITCH_MASTER': {
    name: '스타트업 피치',
    description: '투자자를 위한 매력적인 스타트업 피치',
    icon: '🚀'
  },
  'ACADEMIC_RESEARCHER': {
    name: '학술 연구자',
    description: '엄격한 학술 기준의 연구 발표',
    icon: '🔬'
  },
  'MARKETING_STRATEGIST': {
    name: '마케팅 전략가',
    description: '감성적 연결과 브랜드 스토리 중심',
    icon: '🎨'
  },
  'EXECUTIVE_BOARDROOM': {
    name: '경영진 보고',
    description: '이사회 및 임원진 대상 전략적 보고',
    icon: '👔'
  },
  'TRAINING_FACILITATOR': {
    name: '교육 트레이너',
    description: '실무 중심의 학습 경험 설계',
    icon: '📚'
  },
  'PRODUCT_MANAGER': {
    name: '프로덕트 매니저',
    description: '제품 전략 및 로드맵 프레젠테이션',
    icon: '📱'
  },
  'CONSULTANT_ADVISOR': {
    name: '컨설턴트 어드바이저',
    description: '체계적 분석과 전략적 권고사항',
    icon: '💡'
  }
};

export const DEFAULT_PERSONA = 'EXPERT_DATA_STRATEGIST';

export const getPersonaList = () => Object.entries(PERSONAS).map(([key, config]) => ({
  id: key,
  ...config
}));
