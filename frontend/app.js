document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const analyzeBtn = document.getElementById('analyzeBtn');
    const tickerInput = document.getElementById('tickerInput');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const dashboardArea = document.getElementById('dashboardArea');
    const emptyState = document.getElementById('emptyState');
    const analysisLayers = document.getElementById('analysisLayers');
    const processTerminal = document.getElementById('processTerminal');
    const terminalBody = document.getElementById('terminalBody');

    // Header Metrics
    const tickerSymbol = document.getElementById('tickerSymbol');
    const currentPrice = document.getElementById('currentPrice');
    const priceChange = document.getElementById('priceChange');
    const trendBadge = document.getElementById('trendBadge');

    // Chart
    const chartArea = document.getElementById('mainChart');
    let chart;
    let candleSeries;
    let volumeSeries;

    // Beginner Report
    const beginnerContent = document.getElementById('beginnerContent');

    // --- Tab Switching Logic ---
    const navLinks = document.querySelectorAll('.nav-links li');
    const tabContents = document.querySelectorAll('.tab-content');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTabId = link.getAttribute('data-tab');

            // Toggle active state on links
            navLinks.forEach(nl => nl.classList.remove('active'));
            link.classList.add('active');

            // Toggle active state on pages
            tabContents.forEach(content => {
                if (content.id === targetTabId) {
                    content.classList.remove('hidden');
                    content.classList.add('active');
                    if (targetTabId === 'scannerPage') renderScanner();
                } else {
                    content.classList.add('hidden');
                    content.classList.remove('active');
                }
            });
        });
    });

    // --- Chart Initialization ---
    function initChart() {
        if (chart) return;
        chart = LightweightCharts.createChart(chartArea, {
            width: chartArea.clientWidth,
            height: 400,
            layout: { background: { color: 'transparent' }, textColor: '#ccc' },
            grid: { vertLines: { color: 'rgba(255,255,255,0.05)' }, horzLines: { color: 'rgba(255,255,255,0.05)' } },
            timeScale: { borderColor: 'rgba(255,255,255,0.1)' }
        });
        candleSeries = chart.addCandlestickSeries({ upColor: '#00ff9d', downColor: '#ff0055' });
        volumeSeries = chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: { type: 'volume' },
            priceScaleId: ''
        });
        volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    }

    // --- Terminal Logic ---
    function logToTerminal(text, isBold = false) {
        const div = document.createElement('div');
        div.className = `log-entry ${isBold ? 'active' : ''}`;
        div.textContent = text;
        terminalBody.appendChild(div);
        terminalBody.scrollTop = terminalBody.scrollHeight;
    }

    let simulationInterval;
    function startSimulation(ticker) {
        terminalBody.innerHTML = '';
        processTerminal.classList.remove('hidden');
        logToTerminal(`INITIATING ĐỘC GIÁ PROTOCOL FOR [${ticker}]...`, true);

        const mainSteps = [
            "Connecting to Market Data Exchange...",
            "Fetching Real-time OHLCV Data...",
            "Scanning Market Structure (Wyckoff Logic)...",
            "Analyzing Volume Profiles & Order Flow...",
            "Calculating Key Support/Resistance Levels..."
        ];

        let i = 0;
        simulationInterval = setInterval(() => {
            if (Math.random() > 0.4 && i < mainSteps.length) {
                logToTerminal(mainSteps[i], true);
                i++;
            } else {
                const hex = Math.random().toString(16).substr(2, 6).toUpperCase();
                logToTerminal(`[SCAN] ADDR_0x${hex} ... OK`, false);
            }
        }, 300);
    }

    function stopSimulation() {
        clearInterval(simulationInterval);
    }

    // --- Scanner Implementation ---
    function renderScanner() {
        const scannerGrid = document.getElementById('scannerGrid');
        const mocks = [
            { t: 'HPG', p: 28500, c: '+2.1%', r: 'Dòng tiền đột biến tại hỗ trợ cứng.' },
            { t: 'SSI', p: 35200, c: '+1.5%', r: 'Cấu trúc tích lũy hướng lên (Ascending Triangle).' },
            { t: 'VNM', p: 67800, c: '-0.2%', r: 'Đang kiểm định lại kênh giảm giá dài hạn.' },
            { t: 'FPT', p: 112000, c: '+3.4%', r: 'Vượt đỉnh mọi thời đại với volume xác nhận.' }
        ];

        scannerGrid.innerHTML = mocks.map(m => `
            <div class="scan-card" onclick="quickSearch('${m.t}')">
                <div class="scan-head">
                    <span class="scan-ticker">${m.t}</span>
                    <span class="scan-price">${m.p.toLocaleString()}</span>
                </div>
                <p class="scan-reason">${m.r}</p>
                <div class="scan-footer">
                    <span>BIẾN ĐỘNG: <span style="color:${m.c.includes('+') ? '#00ff9d' : '#ff0055'}">${m.c}</span></span>
                    <span style="color:var(--primary)">CHI TIẾT <i class="fa-solid fa-arrow-right"></i></span>
                </div>
            </div>
        `).join('');
    }

    window.quickSearch = (ticker) => {
        tickerInput.value = ticker;
        document.querySelector('[data-tab="analysisPage"]').click();
        analyzeBtn.click();
    };

    // --- Analysis Execution ---
    analyzeBtn.addEventListener('click', async () => {
        const ticker = tickerInput.value.trim().toUpperCase();
        if (!ticker) return alert('Vui lòng nhập mã cổ phiếu');

        analyzeBtn.disabled = true;
        emptyState.style.display = 'none';
        dashboardArea.classList.add('hidden');
        startSimulation(ticker);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker, apiKey: apiKeyInput.value })
            });
            const data = await response.json();
            stopSimulation();

            if (data.error) {
                logToTerminal(`ERROR: ${data.error}`, true);
                setTimeout(() => processTerminal.classList.add('hidden'), 2000);
                return;
            }

            // Real data reveal
            if (data.technicals) {
                logToTerminal("--- REAL-TIME DATA SCAN ---", true);
                logToTerminal(`PRICE: ${data.current_price.toLocaleString()}`);
                logToTerminal(`RSI: ${data.technicals.rsi_14}`);
                logToTerminal(`TREND: ${data.technicals.trend}`);
            }

            if (data.process_steps) {
                logToTerminal("--- ĐỘC GIÁ STRATEGY ---", true);
                for (let s of data.process_steps) {
                    logToTerminal(s);
                    await new Promise(r => setTimeout(r, 600));
                }
            }

            logToTerminal("ANALYSIS COMPLETE. RENDERING...", true);
            await new Promise(r => setTimeout(r, 800));
            processTerminal.classList.add('hidden');

            renderDashboard(data);
        } catch (e) {
            logToTerminal(`SYSTEM ERROR: ${e.message}`, true);
        } finally {
            analyzeBtn.disabled = false;
        }
    });

    function renderDashboard(data) {
        dashboardArea.classList.remove('hidden');
        initChart();

        // Header Metrics
        tickerSymbol.textContent = data.ticker;
        currentPrice.textContent = data.current_price.toLocaleString();
        priceChange.textContent = data.percent_change;
        const isUp = !data.percent_change.includes('-');
        currentPrice.style.color = isUp ? '#00ff9d' : '#ff0055';
        priceChange.style.color = isUp ? '#00ff9d' : '#ff0055';

        // Fast Metrics
        const fin = data.financials || {};
        document.getElementById('mMarketCap').textContent = fin.VonHoa || 'N/A';
        document.getElementById('mPE').textContent = fin.PE || 'N/A';
        document.getElementById('mEPS').textContent = fin.EPS || 'N/A';
        document.getElementById('mRSI').textContent = data.technicals?.rsi_14 || 'N/A';

        // Trend Badge
        const trend = data.technicals?.trend || 'UNKNOWN';
        trendBadge.textContent = trend;
        trendBadge.className = 'trend-badge ' + (trend.includes('TĂNG') ? 'trend-bullish' : 'trend-bearish');

        // Chart
        if (data.chart_data) {
            const candles = data.chart_data.map(d => ({
                time: formatDate(d.date),
                open: d.open || d.close, high: d.high || d.close, low: d.low || d.close, close: d.close
            })).sort((a, b) => a.time.localeCompare(b.time));
            candleSeries.setData(candles);
            chart.timeScale().fitContent();
        }

        // Beginner Report
        const b = data.beginner_report || {};
        beginnerContent.innerHTML = `
            <p><strong>Tóm tắt:</strong> ${b.summary || 'N/A'}</p>
            <ul>
                <li><strong>Hành động:</strong> ${b.action_plan || 'N/A'}</li>
                <li><strong>Rủi ro:</strong> <span style="color:${b.risk_level === 'Cao' ? '#ff0055' : '#00ff9d'}">${b.risk_level}</span></li>
            </ul>
        `;

        // Strategy Hub
        document.getElementById('adviceText').textContent = data.friendly_advice;
        document.getElementById('actionBadge').textContent = data.strategy?.decision || '---';
        document.getElementById('valEntry').textContent = data.strategy?.entry || '---';
        document.getElementById('valSL').textContent = data.strategy?.stop_loss || '---';
        document.getElementById('valTarget').textContent = data.strategy?.target || '---';
        document.getElementById('valRR').textContent = data.strategy?.rr_ratio || '---';

        // Layers
        analysisLayers.innerHTML = (data.layers || []).map((l, i) => `
            <div class="layer-item glass-card tech-card">
                <div class="layer-head"><span class="layer-num">0${i + 1}</span> ${l.layer}</div>
                <div class="layer-content">${l.analysis}</div>
            </div>
        `).join('');
    }

    function formatDate(str) {
        const [d, m, y] = str.split('/');
        return `${y}-${m}-${d}`;
    }
});
