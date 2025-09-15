export interface SlideVersion {
  version_id: string;
  content: string;
  timestamp: string;
  is_current: boolean;
  created_by: string;
}

export interface Slide {
  order: number;
  plan: {
    slide_title: string;
    key_points?: string[];
    data_points?: string[];
    expert_insights?: string[];
  };
  content: {
    html_content: string;
    current_version_id?: string;
  };
  versions?: SlideVersion[];
}

export interface DeckData {
  id: string;
  deck_title: string;
  status: string;
  slides: Slide[];
  progress: number;
  step: string;
  created_at: string;
  updated_at?: string;
}

export interface DeckStatus {
  deck_id: string;
  status: 'starting' | 'planning' | 'writing' | 'rendering' | 'modifying' | 'completed' | 'failed' | 'cancelled';
  slide_count: number;
  progress?: number;
  step?: string;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}
