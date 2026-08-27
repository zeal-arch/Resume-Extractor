document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const uploadCard = document.getElementById('upload-card');
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const resultsArea = document.getElementById('results-area');
    const errorMessage = document.getElementById('error-message');
    const tryAgainBtn = document.getElementById('try-again-btn');
    const resetBtn = document.getElementById('reset-btn');

    // Drag and Drop Handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', handleDrop, false);

    // File Input Handlers
    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFiles(this.files);
        }
    });

    tryAgainBtn.addEventListener('click', resetUI);
    resetBtn.addEventListener('click', resetUI);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length === 0) return;
        const file = files[0];
        
        // Basic validation
        const validExtensions = ['.pdf', '.docx'];
        const fileName = file.name.toLowerCase();
        if (!validExtensions.some(ext => fileName.endsWith(ext))) {
            showError("Invalid file type. Please upload a PDF or DOCX file.");
            return;
        }

        uploadFile(file);
    }

    async function uploadFile(file) {
        showLoading();

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/extract', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to extract data');
            }

            renderResults(data);
        } catch (error) {
            showError(error.message);
        }
    }

    function renderResults(data) {
        hideAll();
        resultsArea.classList.remove('hidden');

        // Name
        document.getElementById('res-name').textContent = data.name || 'Unknown Candidate';

        // Contact Tags
        updateTag('res-email', data.email, `mailto:${data.email}`, data.email);
        updateTag('res-phone', data.phone, `tel:${data.phone}`, data.phone);
        updateTag('res-linkedin', data.linkedin, data.linkedin, 'LinkedIn');
        updateTag('res-github', data.github, data.github, 'GitHub');

        // Skills
        const skillsContainer = document.getElementById('res-skills');
        skillsContainer.innerHTML = '';
        if (data.skills && data.skills.length > 0) {
            data.skills.forEach(skill => {
                const badge = document.createElement('span');
                badge.className = 'skill-badge';
                badge.textContent = skill;
                skillsContainer.appendChild(badge);
            });
        } else {
            skillsContainer.innerHTML = '<p class="empty-state">No skills detected.</p>';
        }

        // Experience
        const expContainer = document.getElementById('res-experience');
        expContainer.innerHTML = '';
        if (data.experience && data.experience.length > 0) {
            data.experience.forEach(exp => {
                const li = document.createElement('li');
                li.innerHTML = `<div class="item-title">${escapeHTML(exp)}</div>`;
                expContainer.appendChild(li);
            });
        } else {
            expContainer.innerHTML = '<p class="empty-state">No experience entries detected.</p>';
        }

        // Education
        const eduContainer = document.getElementById('res-education');
        eduContainer.innerHTML = '';
        if (data.education && data.education.length > 0) {
            data.education.forEach(edu => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <div class="item-title">${escapeHTML(edu.degree || 'Degree not specified')}</div>
                    ${edu.institution ? `<div class="item-subtitle">${escapeHTML(edu.institution)}</div>` : ''}
                `;
                eduContainer.appendChild(li);
            });
        } else {
            eduContainer.innerHTML = '<p class="empty-state">No education entries detected.</p>';
        }

        // Raw JSON
        document.getElementById('res-json').textContent = JSON.stringify(data, null, 2);
    }

    function updateTag(id, value, href, textContent) {
        const el = document.getElementById(id);
        if (value) {
            el.href = href;
            el.querySelector('span').textContent = textContent;
            el.classList.remove('hidden');
        } else {
            el.classList.add('hidden');
        }
    }

    function showLoading() {
        hideAll();
        loadingState.classList.remove('hidden');
    }

    function showError(msg) {
        hideAll();
        errorMessage.textContent = msg;
        errorState.classList.remove('hidden');
    }

    function resetUI() {
        hideAll();
        fileInput.value = '';
        uploadCard.classList.remove('hidden');
    }

    function hideAll() {
        uploadCard.classList.add('hidden');
        loadingState.classList.add('hidden');
        errorState.classList.add('hidden');
        resultsArea.classList.add('hidden');
    }

    // Simple HTML escape to prevent XSS from extracted text
    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }
});
