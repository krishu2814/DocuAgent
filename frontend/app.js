/**
 * DocuAgent — Frontend Client Logic
 * 
 * Supports both unified deployment (relative URLs) and decoupled deployment 
 * (Vercel frontend + Render backend via window.DOCUAGENT_API_URL).
 */

document.addEventListener("DOMContentLoaded", () => {
    // Determine API Base URL
    const API_BASE = (window.DOCUAGENT_API_URL || "").replace(/\/+$/, "");

    // State
    let conversationId = null;
    let isSubmitting = false;

    // DOM Elements
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const uploadStatus = document.getElementById("upload-status");
    const documentsContainer = document.getElementById("documents-container");
    const docCountBadge = document.getElementById("doc-count-badge");
    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const newChatBtn = document.getElementById("new-chat-btn");
    const welcomeCard = document.getElementById("welcome-card");
    const systemStatus = document.getElementById("system-status");

    // ==========================================
    // 1. Initial Setup & Health Check
    // ==========================================
    async function checkHealth() {
        try {
            const res = await fetch(`${API_BASE}/health`);
            if (res.ok) {
                systemStatus.innerHTML = `<span class="status-dot"></span><span class="status-text">Connected</span>`;
            } else {
                throw new Error("Service degraded");
            }
        } catch {
            systemStatus.innerHTML = `<span class="status-dot" style="background:#ef4444"></span><span class="status-text" style="color:#ef4444">Offline</span>`;
        }
    }

    // Load initial documents and check backend health
    checkHealth();
    loadDocuments();

    // ==========================================
    // 2. Document Upload Handling
    // ==========================================
    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    async function handleFileUpload(file) {
        const formData = new FormData();
        formData.append("file", file);

        showUploadStatus(`Ingesting "${file.name}" into pgvector...`, "loading");

        try {
            const res = await fetch(`${API_BASE}/documents/upload`, {
                method: "POST",
                body: formData,
            });

            let data;
            const contentType = res.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                data = await res.json();
            } else {
                const text = await res.text();
                data = { detail: text || `Upload failed (status ${res.status})` };
            }

            if (!res.ok) {
                throw new Error(data.detail || `Upload failed with status ${res.status}`);
            }

            showUploadStatus(`✓ "${file.name}" ingested successfully!`, "success");
            setTimeout(() => hideUploadStatus(), 3500);

            // Refresh documents list
            loadDocuments();
        } catch (err) {
            showUploadStatus(`Upload Error: ${err.message}`, "error");
            setTimeout(() => hideUploadStatus(), 6000);
        } finally {
            fileInput.value = "";
        }
    }

    function showUploadStatus(msg, type) {
        uploadStatus.className = `upload-status ${type}`;
        uploadStatus.textContent = msg;
    }

    function hideUploadStatus() {
        uploadStatus.className = "upload-status hidden";
    }

    // ==========================================
    // 3. Document List & Deletion
    // ==========================================
    async function loadDocuments() {
        try {
            const res = await fetch(`${API_BASE}/documents`);
            if (!res.ok) return;

            const docs = await res.json();
            docCountBadge.textContent = `${docs.length} Doc${docs.length === 1 ? "" : "s"}`;

            if (docs.length === 0) {
                documentsContainer.innerHTML = `
                    <div class="empty-state">
                        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                        <p>No documents uploaded yet</p>
                        <span>Upload a PDF, TXT or MD to begin querying</span>
                    </div>
                `;
                return;
            }

            documentsContainer.innerHTML = docs.map(doc => {
                const ext = (doc.filename.split('.').pop() || 'doc').toLowerCase();
                const typeClass = ext === 'pdf' ? 'type-pdf' : ext === 'md' ? 'type-md' : 'type-txt';
                
                return `
                    <div class="doc-card" id="doc-${doc.id}">
                        <div class="doc-info">
                            <div class="doc-type-icon ${typeClass}">${ext}</div>
                            <div class="doc-text">
                                <span class="doc-filename" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</span>
                                <span class="doc-meta">Stored in pgvector</span>
                            </div>
                        </div>
                        <button class="delete-doc-btn" onclick="deleteDocument('${doc.id}', '${escapeHtml(doc.filename)}')" title="Delete document">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                    </div>
                `;
            }).join("");

        } catch (err) {
            console.error("Failed to load documents:", err);
        }
    }

    window.deleteDocument = async function(id, filename) {
        if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

        try {
            const res = await fetch(`${API_BASE}/documents/${id}`, { method: "DELETE" });
            if (res.ok) {
                loadDocuments();
            }
        } catch (err) {
            alert(`Could not delete document: ${err.message}`);
        }
    };

    // ==========================================
    // 4. Chat & Message Stream Handling
    // ==========================================
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const query = userInput.value.trim();
        if (!query || isSubmitting) return;

        submitQuestion(query);
    });

    // Auto-resize textarea & enter-key submit
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    userInput.addEventListener("input", () => {
        userInput.style.height = "auto";
        userInput.style.height = `${Math.min(userInput.scrollHeight, 140)}px`;
    });

    // Quick prompt buttons
    document.addEventListener("click", (e) => {
        const chip = e.target.closest(".prompt-chip");
        if (chip) {
            const prompt = chip.getAttribute("data-prompt");
            if (prompt) {
                userInput.value = prompt;
                submitQuestion(prompt);
            }
        }
    });

    newChatBtn.addEventListener("click", () => {
        conversationId = null;
        chatMessages.innerHTML = `
            <div class="welcome-card" id="welcome-card">
                <div class="welcome-icon">✨</div>
                <h3>Welcome to DocuAgent</h3>
                <p>Upload your documents on the left panel, and ask questions. DocuAgent analyzes question complexity, retrieves relevant chunks from pgvector, and generates answers with page-level citations.</p>
                <div class="quick-prompts">
                    <p class="quick-prompts-label">Try asking:</p>
                    <div class="prompts-grid">
                        <button class="prompt-chip" data-prompt="What are the key topics covered in the uploaded documents?">
                            📑 What are the key topics covered?
                        </button>
                        <button class="prompt-chip" data-prompt="Compare the main concepts and their tradeoffs.">
                            ⚖️ Compare main concepts & tradeoffs
                        </button>
                        <button class="prompt-chip" data-prompt="Summarize the core takeaways in bullet points.">
                            📝 Summarize the core takeaways
                        </button>
                    </div>
                </div>
            </div>
        `;
        userInput.value = "";
        userInput.focus();
    });

    async function submitQuestion(question) {
        if (isSubmitting) return;
        isSubmitting = true;
        sendBtn.disabled = true;

        // Hide welcome card once chat starts
        const welcome = document.getElementById("welcome-card");
        if (welcome) welcome.remove();

        // 1. Render User Message
        appendMessageRow("user", question);
        userInput.value = "";
        userInput.style.height = "auto";

        // 2. Render Agent Loading Bubble
        const loadingRow = appendLoadingRow();
        scrollToBottom();

        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: question,
                    conversation_id: conversationId,
                }),
            });

            let data;
            const contentType = res.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                data = await res.json();
            } else {
                const text = await res.text();
                data = { detail: text || `Request failed (status ${res.status})` };
            }

            loadingRow.remove();

            if (!res.ok) {
                throw new Error(data.detail || `Server error (status ${res.status})`);
            }

            conversationId = data.conversation_id;

            // 3. Render Agent Response with citations & routing badge
            appendAgentResponseRow(data);

        } catch (err) {
            loadingRow.remove();
            appendMessageRow("agent", `⚠️ ${err.message}`);
        } finally {
            isSubmitting = false;
            sendBtn.disabled = false;
            userInput.focus();
            scrollToBottom();
        }
    }

    function appendMessageRow(role, text) {
        const row = document.createElement("div");
        row.className = `message-row ${role === "user" ? "user-row" : "agent-row"}`;

        if (role === "user") {
            row.innerHTML = `
                <div class="message-bubble user-bubble">${escapeHtml(text)}</div>
                <div class="message-avatar user-avatar">U</div>
            `;
        } else {
            row.innerHTML = `
                <div class="message-avatar agent-avatar">AI</div>
                <div class="message-bubble agent-bubble">${escapeHtml(text)}</div>
            `;
        }

        chatMessages.appendChild(row);
        scrollToBottom();
        return row;
    }

    function appendLoadingRow() {
        const row = document.createElement("div");
        row.className = "message-row agent-row";
        row.innerHTML = `
            <div class="message-avatar agent-avatar">AI</div>
            <div class="message-bubble agent-bubble">
                <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(row);
        return row;
    }

    function appendAgentResponseRow(data) {
        const row = document.createElement("div");
        row.className = "message-row agent-row";

        // Determine complexity routing badge (simple query vs complex decomposition)
        const isComplex = data.question.toLowerCase().includes("compare") || 
                          data.question.toLowerCase().includes("vs") || 
                          data.question.toLowerCase().includes("difference") ||
                          (data.sources && data.sources.length > 2);

        const badgeHtml = isComplex 
            ? `<span class="routing-badge badge-complex">🧠 Complex Decomposition</span>`
            : `<span class="routing-badge badge-simple">⚡ Direct Retrieval</span>`;

        // Format body text and extract sources if appended
        let answerText = data.answer || "";
        let sourcesSectionHtml = "";

        // Build sources pill list
        if (data.sources && data.sources.length > 0) {
            const uniqueSources = [];
            const seen = new Set();

            data.sources.forEach(s => {
                const name = s.source || "Document";
                const page = s.page_number;
                const label = page ? `${name} (P.${page})` : name;
                if (!seen.has(label)) {
                    seen.add(label);
                    uniqueSources.push({ name, page });
                }
            });

            sourcesSectionHtml = `
                <div class="citations-box">
                    <div class="citations-title">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                        Grounded Sources
                    </div>
                    <div class="citations-list">
                        ${uniqueSources.map(s => `
                            <span class="citation-pill">
                                <span>${escapeHtml(s.name)}</span>
                                ${s.page ? `<span class="citation-page">Page ${s.page}</span>` : ''}
                            </span>
                        `).join("")}
                    </div>
                </div>
            `;
        }

        // Clean out duplicate "Sources:" text from answer string if present to avoid repetition
        if (answerText.includes("\n\nSources:\n")) {
            answerText = answerText.split("\n\nSources:\n")[0];
        }

        row.innerHTML = `
            <div class="message-avatar agent-avatar">AI</div>
            <div class="message-bubble agent-bubble">
                <div class="agent-header">
                    <span class="agent-name">DocuAgent</span>
                    ${badgeHtml}
                </div>
                <div class="agent-content">${formatAnswerText(answerText)}</div>
                ${sourcesSectionHtml}
            </div>
        `;

        chatMessages.appendChild(row);
        scrollToBottom();
    }

    function formatAnswerText(text) {
        return escapeHtml(text)
            .replace(/\n\n/g, "<br><br>")
            .replace(/\n/g, "<br>")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>");
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
