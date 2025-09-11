// TinyMCE Editor for Slide Editing
// 1) 편집 대상으로 삼을 요소(화이트리스트)
const EDITABLE_SELECTOR = [
  'h1','h2','h3','h4','h5','h6',
  'p','li','blockquote','figcaption','small',
  'td','th','caption',
  // 필요 시 span에 .inline-edit 클래스로 opt-in
  'span.inline-edit'
].join(',');

// 2) 텍스트가 실제로 있는 노드만 data-editable 부여
function markEditable(root=document) {
  root.querySelectorAll(EDITABLE_SELECTOR).forEach(el => {
    const text = (el.textContent || '').trim();
    if (!text) return;
    if (el.closest('[data-noedit]')) return; // 상위에 noedit 달리면 제외
    el.setAttribute('data-editable', 'true');
    el.classList.add('editable'); // 스타일로 표시하고 싶으면 활용
  });
}

// 3) TinyMCE 인라인 에디터 초기화
function initTiny() {
  tinymce.init({
    selector: '[data-editable]',
    inline: true,
    menubar: false,
    plugins: 'lists link quickbars',
    toolbar: 'undo redo | bold italic underline | fontsize | forecolor | alignleft aligncenter alignright | bullist numlist | link removeformat',
    quickbars_selection_toolbar: 'bold italic underline | h2 h3 | forecolor',
    forced_root_block: false,

    // Enhanced undo/redo configuration
    custom_undo_redo_levels: 50,  // Keep 50 undo levels (micro versions)

    // Keyboard shortcuts (TinyMCE handles these automatically)
    // Ctrl+Z = undo, Ctrl+Y or Ctrl+Shift+Z = redo

    // Auto-save undo levels more frequently for better granularity
    setup: function(editor) {
      let saveTimer;

      // Add undo level after each significant change
      editor.on('input', function() {
        clearTimeout(saveTimer);
        saveTimer = setTimeout(function() {
          if (editor.undoManager && editor.undoManager.add) {
            editor.undoManager.add();
          }
        }, 1000); // Save undo level every 1 second of inactivity
      });

      // Add undo level when focus is lost (switching between elements)
      editor.on('blur', function() {
        if (editor.undoManager && editor.undoManager.add) {
          editor.undoManager.add();
        }
      });

      // Global keyboard shortcuts for undo/redo even outside editor focus
      document.addEventListener('keydown', function(e) {
        // Only handle if we're in the slide editing context
        if (document.querySelector('[data-editable]')) {
          if (e.ctrlKey || e.metaKey) { // Ctrl on Windows/Linux, Cmd on Mac
            if (e.key === 'z' && !e.shiftKey) {
              e.preventDefault();
              editor.undoManager.undo();
            } else if ((e.key === 'z' && e.shiftKey) || e.key === 'y') {
              e.preventDefault();
              editor.undoManager.redo();
            }
          }
        }
      });
    },

    // Tailwind/기존 클래스/속성 보존
    valid_elements: '*[*]',
    valid_styles: { '*': 'color,font-size,text-decoration' }
  });
}

// 4) 저장 함수 (수동 호출용)
window.saveEditedHtml = async function() {
  try {
    console.log('Starting save process...');

    // TinyMCE 편집 내용 적용 (안전한 방식)
    if (window.tinymce && window.tinymce.editors) {
      console.log('TinyMCE editors found:', window.tinymce.editors.length);
      for (let i = 0; i < window.tinymce.editors.length; i++) {
        const ed = window.tinymce.editors[i];
        if (ed && ed.undoManager && ed.undoManager.add) {
          ed.undoManager.add();
        }
      }
    } else {
      console.log('TinyMCE not available or no editors found');
    }

    // 페이지 전체 HTML 직렬화
    let html;
    try {
      html = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
    } catch (htmlError) {
      console.error('HTML serialization failed:', htmlError);
      html = document.body.innerHTML; // fallback
    }

    // Extract deck_id and slide_order from URL or passed parameters
    const deckId = window.location.pathname.split('/')[2]; // Extract from /decks/{id}/preview
    const slideOrder = window.__currentSlideOrder || 1; // Set by frontend

    console.log('Saving with deckId:', deckId, 'slideOrder:', slideOrder);

    const response = await fetch(`/api/save?deck_id=${deckId}&slide_order=${slideOrder}`, {
      method: 'POST',
      headers: {'Content-Type': 'text/html;charset=utf-8'},
      body: html
    });

    if (response.ok) {
      console.log('Save successful');
      return { success: true, message: '저장 완료!' };
    } else {
      console.error('Save failed with status:', response.status);
      throw new Error('서버 저장 실패');
    }
  } catch (error) {
    console.error('Save error:', error);
    throw error;
  }
};

// 전역에서 호출할 수 있게 (호환성을 위한 alias)
window.__saveEditedHtml = window.saveEditedHtml;

// 5) TinyMCE가 로드된 후 초기화 실행
if (typeof tinymce !== 'undefined') {
  // TinyMCE 이미 로드됨
  markEditable(document);
  initTiny();
} else {
  // TinyMCE 로드 대기
  document.addEventListener('DOMContentLoaded', function() {
    // TinyMCE CDN이 로드될 때까지 대기
    const checkTinyMCE = setInterval(function() {
      if (typeof tinymce !== 'undefined') {
        clearInterval(checkTinyMCE);
        markEditable(document);
        initTiny();
      }
    }, 100);
  });
}