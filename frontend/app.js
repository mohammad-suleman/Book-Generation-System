// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global State
let currentBook = null;
let allBooks = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    setupEventListeners();
    await loadBooks();
    showToast('Welcome to Book Generation System', 'info');
}

// Event Listeners
function setupEventListeners() {
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('upload-area');

    fileInput.addEventListener('change', handleFileSelect);
    uploadArea.addEventListener('click', (e) => {
        if (e.target === fileInput) return;
        fileInput.click();
    });
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.csv')) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect({ target: fileInput });
        } else {
            showToast('Please drop a CSV file', 'error');
        }
    });
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        document.getElementById('file-name').textContent = file.name;
        document.getElementById('file-info').style.display = 'flex';
        updateStatus('import-status', 'Ready', 'active');
    }
}

// Upload File
async function uploadFile() {
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    if (!file) { showToast('Please select a file', 'error'); return; }

    showLoading(true);

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/api/books/import`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error('Upload failed');

        const data = await response.json();
        currentBook = data;

        showToast('Book imported successfully!', 'success');
        updateStatus('import-status', 'Completed', 'success');

        document.getElementById('generate-outline-btn').disabled = false;
        updateStatus('outline-status', 'Ready', 'active');

        await loadBooks();
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Failed to upload file: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Generate Outline
async function generateOutline() {
    if (!currentBook) { showToast('Please import a book first', 'error'); return; }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/books/${currentBook.id}/outline/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ regenerate: false })
        });
        if (!response.ok) throw new Error('Outline generation failed');

        const outline = await response.json();

        document.getElementById('outline-display').textContent = outline.outline_content;
        document.getElementById('outline-initial').style.display = 'none';
        document.getElementById('outline-content').style.display = 'block';

        updateStatus('outline-status', 'Review Required', 'warning');
        showToast('Outline generated! Please review.', 'success');
    } catch (error) {
        console.error('Outline generation error:', error);
        showToast('Failed to generate outline: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Approve Outline
async function approveOutline() {
    if (!currentBook) return;

    showLoading(true);

    try {
        const notes = document.getElementById('outline-notes').value || '';

        const response = await fetch(`${API_BASE_URL}/api/books/${currentBook.id}/outline/notes`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes_after: notes, status: 'no_notes_needed' })
        });
        if (!response.ok) throw new Error('Approval failed');

        await response.json();

        updateStatus('outline-status', 'Approved', 'success');
        updateStatus('chapters-status', 'Ready', 'active');

        showToast('Outline approved! Starting chapter generation...', 'success');
        await generateAllChapters();
    } catch (error) {
        console.error('Approval error:', error);
        showToast('Failed to approve outline: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Regenerate Outline
async function regenerateOutline() {
    if (!currentBook) return;

    const notes = document.getElementById('outline-notes').value;
    if (!notes.trim()) {
        showToast('Please provide feedback notes for regeneration', 'error');
        return;
    }

    showLoading(true);

    try {
        const updateResponse = await fetch(`${API_BASE_URL}/api/books/${currentBook.id}/outline/notes`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes_after: notes })
        });
        if (!updateResponse.ok) throw new Error('Failed to update notes');

        const response = await fetch(`${API_BASE_URL}/api/books/${currentBook.id}/outline/regenerate`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Regeneration failed');

        const outline = await response.json();

        document.getElementById('outline-display').textContent = outline.outline_content;
        document.getElementById('outline-notes').value = '';

        showToast('Outline regenerated with your feedback!', 'success');
    } catch (error) {
        console.error('Regeneration error:', error);
        showToast('Failed to regenerate outline: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Generate All Chapters
async function generateAllChapters() {
    if (!currentBook) return;

    showLoading(true);
    document.getElementById('chapters-initial').style.display = 'none';
    document.getElementById('chapters-list').style.display = 'block';

    try {
        const outlineText = document.getElementById('outline-display').textContent || '';
        const chapterMatches = outlineText.match(/chapter\s+\d+/gi);
        const chapterCount = chapterMatches ? chapterMatches.length : 5;

        updateStatus('chapters-status', `Generating ${chapterCount} chapters...`, 'active');

        for (let i = 1; i <= chapterCount; i++) {
            await generateChapter(i);
        }

        updateStatus('chapters-status', 'All Completed', 'success');
        updateStatus('final-status', 'Ready', 'active');
        document.getElementById('compile-btn').disabled = false;

        showToast('All chapters generated successfully!', 'success');
    } catch (error) {
        console.error('Chapter generation error:', error);
        showToast('Failed to generate chapters: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Generate Single Chapter
async function generateChapter(chapterNumber) {
    const response = await fetch(`${API_BASE_URL}/api/books/${currentBook.id}/chapters/${chapterNumber}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ regenerate: false, notes: null })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `Chapter ${chapterNumber} generation failed`);
    }

    const chapter = await response.json();
    addChapterToUI(chapter);
    return chapter;
}

// Add Chapter to UI
function addChapterToUI(chapter) {
    const chaptersList = document.getElementById('chapters-list');

    const chapterDiv = document.createElement('div');
    chapterDiv.className = 'chapter-item';
    chapterDiv.id = `chapter-${chapter.chapter_number}`;

    chapterDiv.innerHTML = `
        <div class="chapter-header">
            <h3 class="chapter-title"><strong>Chapter ${chapter.chapter_number}${chapter.title ? ': ' + chapter.title : ''}</strong></h3>
            <span class="status-badge ${chapter.notes_status === 'no_notes_needed' ? 'success' : 'warning'}">
                ${chapter.notes_status === 'no_notes_needed' ? 'Approved' : 'Review Required'}
            </span>
        </div>
        <div class="chapter-content" style="display: none;">
            ${formatChapterContent(chapter.content) || 'Generating...'}
        </div>
        <div class="chapter-actions">
            <button class="btn btn-secondary" onclick="toggleChapterContent(${chapter.chapter_number})">
                👁️ View
            </button>
            <button class="btn btn-success" onclick="approveChapter(${chapter.chapter_number})">
                ✅ Approve
            </button>
        </div>
    `;

    chaptersList.appendChild(chapterDiv);
}

// Format Chapter Content (markdown headings → bold HTML)
function formatChapterContent(content) {
    if (!content) return '';
    return content
        .replace(/^### (.+)$/gm, '<h5 class="ch-subtitle">$1</h5>')
        .replace(/^## (.+)$/gm, '<h4 class="ch-subtitle">$1</h4>')
        .replace(/^# (.+)$/gm, '<h3 class="ch-heading">$1</h3>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

// Toggle Chapter Content
function toggleChapterContent(chapterNumber) {
    const content = document.querySelector(`#chapter-${chapterNumber} .chapter-content`);
    content.style.display = content.style.display === 'none' ? 'block' : 'none';
}

// Approve Chapter
async function approveChapter(chapterNumber) {
    if (!currentBook) return;

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/books/${currentBook.id}/chapters/${chapterNumber}/notes`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: '', notes_status: 'no_notes_needed' })
        });
        if (!response.ok) throw new Error('Approval failed');

        await response.json();

        const badge = document.querySelector(`#chapter-${chapterNumber} .status-badge`);
        badge.textContent = 'Approved';
        badge.className = 'status-badge success';

        showToast(`Chapter ${chapterNumber} approved!`, 'success');
    } catch (error) {
        console.error('Chapter approval error:', error);
        showToast('Failed to approve chapter: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Compile Final Draft
async function compileFinalDraft() {
    if (!currentBook) return;

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/books/${currentBook.id}/compile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force: false })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || 'Compilation failed');
        }

        await response.json();

        document.getElementById('final-initial').style.display = 'none';
        document.getElementById('final-content').style.display = 'block';

        updateStatus('final-status', 'Ready', 'success');

        showToast('Final draft compiled successfully!', 'success');
    } catch (error) {
        console.error('Compilation error:', error);
        showToast('Failed to compile final draft: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Download Book
async function downloadBook(format = 'docx') {
    if (!currentBook) return;

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/books/${currentBook.id}/final-draft/download?format=${encodeURIComponent(format)}`);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || 'Download failed');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentBook.title || 'book'}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showToast(`Book downloaded as .${format} successfully!`, 'success');
    } catch (error) {
        console.error('Download error:', error);
        showToast('Failed to download book: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Submit Final Review
async function submitFinalReview() {
    if (!currentBook) return;

    const notes = document.getElementById('final-notes').value;

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/books/${currentBook.id}/final-draft/review`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ final_notes: notes, review_notes_status: 'no_notes_needed' })
        });
        if (!response.ok) throw new Error('Review submission failed');

        await response.json();

        showToast('Final review submitted!', 'success');
        document.getElementById('final-notes').value = '';
    } catch (error) {
        console.error('Review submission error:', error);
        showToast('Failed to submit review: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Load All Books
async function loadBooks() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/books/`);
        if (!response.ok) throw new Error('Failed to load books');

        allBooks = await response.json();
        displayBooks(allBooks);
    } catch (error) {
        console.error('Load books error:', error);
        const booksList = document.getElementById('books-list');
        booksList.innerHTML = '<p class="info-text">Failed to load books. Make sure the backend is running.</p>';
    }
}

// Display Books
function displayBooks(books) {
    const booksList = document.getElementById('books-list');

    if (books.length === 0) {
        booksList.innerHTML = '<p class="info-text">No books yet. Import a CSV to get started!</p>';
        return;
    }

    booksList.innerHTML = books.map(book => `
        <div class="book-item" onclick="selectBook(${book.id})">
            <div class="book-info">
                <h4>${book.title || 'Untitled Book'}</h4>
                <p>Stage: ${book.current_stage}</p>
            </div>
            <span class="status-badge ${getStateClass(book.current_stage)}">${book.current_stage}</span>
        </div>
    `).join('');
}

// Select Book
function selectBook(bookId) {
    const book = allBooks.find(b => b.id === bookId);
    if (book) {
        currentBook = book;
        showToast(`Selected: ${book.title}`, 'info');
    }
}

// Get State Class
function getStateClass(stage) {
    const stageMap = {
        'input': 'pending',
        'outline': 'active',
        'chapters': 'active',
        'compilation': 'warning',
        'completed': 'success'
    };
    return stageMap[stage] || 'pending';
}

// Update Status
function updateStatus(elementId, text, type) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
        element.className = `status-badge ${type}`;
    }
}

// Show Loading
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = show ? 'flex' : 'none';
}

// Show Toast
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';

    toast.innerHTML = `
        <span style="font-size: 1.2rem;">${icon}</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
