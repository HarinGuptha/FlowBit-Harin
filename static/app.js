// Multi-Format Autonomous AI System - Frontend JavaScript
class AISystemInterface {
    constructor() {
        this.formatChart = null;
        this.intentChart = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSystemHealth();
        this.loadSystemStats();
        this.loadRecentSessions();
        this.initCharts();
    }

    setupEventListeners() {
        // File upload
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');

        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));

        // Drag and drop
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
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.showFileSelected(files[0]);
                this.processFile(files[0]);
            }
        });

        // Auto-refresh every 30 seconds
        setInterval(() => {
            this.loadSystemHealth();
            this.loadSystemStats();
        }, 30000);
    }

    async loadSystemHealth() {
        try {
            const response = await fetch('/api/health');
            const health = await response.json();
            this.updateHealthDisplay(health);
        } catch (error) {
            console.error('Failed to load system health:', error);
        }
    }

    updateHealthDisplay(health) {
        const healthStatus = document.getElementById('healthStatus');
        
        const agents = health.agents_status || {};
        const agentCards = Object.entries(agents).map(([name, status]) => {
            const statusClass = status === 'active' ? 'status-active' : 'status-inactive';
            return `
                <div class="col-md-3">
                    <div class="d-flex align-items-center">
                        <span class="status-indicator ${statusClass}"></span>
                        <span class="fw-bold">${name.charAt(0).toUpperCase() + name.slice(1)} Agent</span>
                    </div>
                </div>
            `;
        }).join('');

        const memoryStatus = health.memory_status === 'connected' ? 'status-active' : 'status-inactive';
        const routerStatus = health.action_router_status === 'active' ? 'status-active' : 'status-inactive';

        healthStatus.innerHTML = `
            ${agentCards}
            <div class="col-md-3">
                <div class="d-flex align-items-center">
                    <span class="status-indicator ${memoryStatus}"></span>
                    <span class="fw-bold">Memory Store</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="d-flex align-items-center">
                    <span class="status-indicator ${routerStatus}"></span>
                    <span class="fw-bold">Action Router</span>
                </div>
            </div>
            <div class="col-md-6">
                <small class="text-muted">
                    Sessions: ${health.processed_sessions || 0} | 
                    Errors: ${health.error_count || 0} |
                    Status: ${health.status}
                </small>
            </div>
        `;
    }

    async loadSystemStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            this.updateStatsDisplay(stats);
            this.updateCharts(stats);
        } catch (error) {
            console.error('Failed to load system stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        document.getElementById('totalSessions').textContent = stats.total_sessions || 0;
        document.getElementById('actionsExecuted').textContent = stats.actions_executed || 0;
        
        // Calculate anomalies and compliance flags from format data
        const formats = stats.classifications_by_format || {};
        const anomalies = Object.values(formats).reduce((sum, count) => sum + Math.floor(count * 0.1), 0);
        const compliance = Object.values(formats).reduce((sum, count) => sum + Math.floor(count * 0.05), 0);
        
        document.getElementById('anomaliesDetected').textContent = anomalies;
        document.getElementById('complianceFlags').textContent = compliance;
    }

    initCharts() {
        // Format distribution chart
        const formatCtx = document.getElementById('formatChart').getContext('2d');
        this.formatChart = new Chart(formatCtx, {
            type: 'doughnut',
            data: {
                labels: ['Email', 'JSON', 'PDF'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // Intent distribution chart
        const intentCtx = document.getElementById('intentChart').getContext('2d');
        this.intentChart = new Chart(intentCtx, {
            type: 'bar',
            data: {
                labels: ['RFQ', 'Complaint', 'Invoice', 'Regulation', 'Fraud Risk'],
                datasets: [{
                    label: 'Count',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: '#667eea',
                    borderColor: '#5a6fd8',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    updateCharts(stats) {
        // Update format chart
        const formats = stats.classifications_by_format || {};
        this.formatChart.data.datasets[0].data = [
            formats.email || 0,
            formats.json || 0,
            formats.pdf || 0
        ];
        this.formatChart.update();

        // Update intent chart
        const intents = stats.classifications_by_intent || {};
        this.intentChart.data.datasets[0].data = [
            intents.rfq || 0,
            intents.complaint || 0,
            intents.invoice || 0,
            intents.regulation || 0,
            intents.fraud_risk || 0
        ];
        this.intentChart.update();
    }

    async loadRecentSessions() {
        try {
            const response = await fetch('/api/sessions?limit=10');
            const sessions = await response.json();
            this.updateSessionsTable(sessions);
        } catch (error) {
            console.error('Failed to load recent sessions:', error);
        }
    }

    updateSessionsTable(sessions) {
        const tbody = document.getElementById('sessionsTable');
        
        if (!sessions || sessions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No sessions found</td></tr>';
            return;
        }

        tbody.innerHTML = sessions.map(session => {
            const formatBadge = this.getFormatBadge(session.classification.format_type);
            const intentBadge = this.getIntentBadge(session.classification.business_intent);
            const statusBadge = this.getStatusBadge(session.final_status);
            const actionsCount = session.actions_triggered ? session.actions_triggered.length : 0;
            const createdAt = new Date(session.created_at).toLocaleString();

            return `
                <tr>
                    <td><code>${session.session_id.substring(0, 8)}...</code></td>
                    <td>${formatBadge}</td>
                    <td>${intentBadge}</td>
                    <td><span class="badge bg-info">${actionsCount}</span></td>
                    <td>${statusBadge}</td>
                    <td><small>${createdAt}</small></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="aiSystem.viewSession('${session.session_id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    getFormatBadge(format) {
        const badges = {
            email: '<span class="badge bg-primary">Email</span>',
            json: '<span class="badge bg-success">JSON</span>',
            pdf: '<span class="badge bg-warning">PDF</span>'
        };
        return badges[format] || '<span class="badge bg-secondary">Unknown</span>';
    }

    getIntentBadge(intent) {
        const badges = {
            rfq: '<span class="badge bg-info">RFQ</span>',
            complaint: '<span class="badge bg-danger">Complaint</span>',
            invoice: '<span class="badge bg-success">Invoice</span>',
            regulation: '<span class="badge bg-warning">Regulation</span>',
            fraud_risk: '<span class="badge bg-dark">Fraud Risk</span>'
        };
        return badges[intent] || '<span class="badge bg-secondary">Unknown</span>';
    }

    getStatusBadge(status) {
        const badges = {
            completed: '<span class="badge bg-success">Completed</span>',
            failed: '<span class="badge bg-danger">Failed</span>',
            processing: '<span class="badge bg-warning">Processing</span>'
        };
        return badges[status] || '<span class="badge bg-secondary">Unknown</span>';
    }

    handleFileUpload(event) {
        const file = event.target.files[0];
        if (file) {
            this.showFileSelected(file);
            this.processFile(file);
        }
    }

    showFileSelected(file) {
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.innerHTML = `
            <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
            <h5 class="text-success">File Selected Successfully!</h5>
            <p class="text-muted">📁 ${file.name}</p>
            <p class="small text-muted">Size: ${(file.size / 1024).toFixed(1)} KB</p>
            <p class="small text-success">Processing...</p>
        `;
    }

    async processFile(file) {
        this.showProcessingSpinner();

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.showResults(result);
        } catch (error) {
            console.error('File processing failed:', error);
            this.showError('File processing failed: ' + error.message);
        } finally {
            this.hideProcessingSpinner();
        }
    }

    async processText() {
        const content = document.getElementById('textContent').value.trim();
        const contentType = document.getElementById('contentType').value;

        if (!content) {
            alert('Please enter some content to process');
            return;
        }

        this.showProcessingSpinner();

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    content_type: contentType === 'auto' ? null : contentType,
                    metadata: {
                        source: 'text_input',
                        input_length: content.length
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.showResults(result);
        } catch (error) {
            console.error('Text processing failed:', error);
            this.showError('Text processing failed: ' + error.message);
        } finally {
            this.hideProcessingSpinner();
        }
    }

    showProcessingSpinner() {
        document.getElementById('processingSpinner').style.display = 'block';
        document.getElementById('resultCard').style.display = 'none';
    }

    hideProcessingSpinner() {
        document.getElementById('processingSpinner').style.display = 'none';
    }

    showResults(result) {
        const resultContent = document.getElementById('resultContent');
        const classification = result.classification;
        const actions = result.actions_triggered || [];

        // Reset upload area to original state
        this.resetUploadArea();

        resultContent.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="fas fa-search me-2"></i>Classification Results</h6>
                    <div class="mb-3">
                        <strong>Format:</strong> ${this.getFormatBadge(classification.format_type)}
                        <br>
                        <strong>Intent:</strong> ${this.getIntentBadge(classification.business_intent)}
                        <br>
                        <strong>Confidence:</strong> 
                        <div class="progress mt-1" style="height: 20px;">
                            <div class="progress-bar" role="progressbar" 
                                 style="width: ${classification.confidence * 100}%">
                                ${(classification.confidence * 100).toFixed(1)}%
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-cogs me-2"></i>Processing Info</h6>
                    <div class="mb-3">
                        <strong>Session ID:</strong> <code>${result.session_id}</code><br>
                        <strong>Status:</strong> ${this.getStatusBadge(result.processing_status)}<br>
                        <strong>Processing Time:</strong> ${result.processing_time_ms.toFixed(2)}ms<br>
                        <strong>Actions Triggered:</strong> <span class="badge bg-info">${actions.length}</span>
                    </div>
                </div>
            </div>
            
            ${actions.length > 0 ? `
                <h6><i class="fas fa-bolt me-2"></i>Actions Triggered</h6>
                <div class="row">
                    ${actions.map(action => `
                        <div class="col-md-6 mb-3">
                            <div class="card border-start border-primary border-3">
                                <div class="card-body">
                                    <h6 class="card-title">${action.action_type.replace('_', ' ').toUpperCase()}</h6>
                                    <p class="card-text small">
                                        Status: ${this.getStatusBadge(action.status)}<br>
                                        Execution Time: ${action.execution_time_ms?.toFixed(2) || 'N/A'}ms
                                    </p>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        `;

        document.getElementById('resultCard').style.display = 'block';
        
        // Refresh stats and sessions
        this.loadSystemStats();
        this.loadRecentSessions();
    }

    showError(message) {
        const resultContent = document.getElementById('resultContent');

        // Reset upload area to original state
        this.resetUploadArea();

        resultContent.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Error:</strong> ${message}
            </div>
        `;
        document.getElementById('resultCard').style.display = 'block';
    }

    resetUploadArea() {
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.innerHTML = `
            <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
            <h5>Drag & Drop Files Here</h5>
            <p class="text-muted">Or click to select files</p>
            <p class="small text-muted">
                Supported formats: PDF, JSON, Email (.eml, .txt)
            </p>
            <input type="file" id="fileInput" class="d-none" accept=".pdf,.json,.eml,.txt">
            <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                Select Files
            </button>
        `;

        // Re-attach event listeners
        const fileInput = document.getElementById('fileInput');
        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    }

    async viewSession(sessionId) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}`);
            const session = await response.json();
            
            // Create modal or detailed view
            alert(`Session Details:\n\nID: ${session.session_id}\nFormat: ${session.classification.format_type}\nIntent: ${session.classification.business_intent}\nStatus: ${session.final_status}`);
        } catch (error) {
            console.error('Failed to load session details:', error);
            alert('Failed to load session details');
        }
    }
}

// Utility functions
function scrollToProcessor() {
    document.getElementById('processor').scrollIntoView({ behavior: 'smooth' });
}

function showSystemHealth() {
    document.getElementById('dashboard').scrollIntoView({ behavior: 'smooth' });
}

function refreshHealth() {
    aiSystem.loadSystemHealth();
}

function refreshSessions() {
    aiSystem.loadRecentSessions();
}

function processText() {
    aiSystem.processText();
}

// Initialize the system
const aiSystem = new AISystemInterface();
