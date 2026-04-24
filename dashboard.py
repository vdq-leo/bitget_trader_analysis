import os
import json
from jinja2 import Template

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bitget Trader Analysis Dashboard</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.7.0.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f1f5f9;
            --accent-color: #38bdf8;
            --border-color: #334155;
            --success: #4ade80;
            --error: #fb7185;
            --warning: #facc15;
        }
        body { background-color: var(--bg-color); color: var(--text-color); font-family: 'Inter', sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        header { margin-bottom: 30px; text-align: center; }
        
        .table-container { background-color: var(--card-bg); border-radius: 12px; padding: 20px; border: 1px solid var(--border-color); }
        table.dataTable { background-color: transparent !important; color: var(--text-color) !important; }
        table.dataTable thead th { color: var(--accent-color) !important; }
        table.dataTable tbody tr { cursor: pointer; }
        table.dataTable tbody tr:hover { background-color: #334155 !important; }

        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .modal-content { background: var(--card-bg); width: 95%; max-width: 1100px; max-height: 90vh; border-radius: 16px; padding: 30px; overflow-y: auto; border: 1px solid var(--border-color); position: relative; }
        .close-btn { position: absolute; top: 20px; right: 20px; font-size: 28px; cursor: pointer; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px; }
        .stat-card { background: var(--bg-color); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid var(--border-color); }
        .stat-val { font-size: 1.4rem; font-weight: bold; color: var(--accent-color); }
        .stat-label { font-size: 0.85rem; color: #94a3b8; margin-top: 5px; }
        
        .chart-container { background: var(--bg-color); padding: 20px; border-radius: 12px; height: 350px; border: 1px solid var(--border-color); margin-bottom: 30px; }
        
        .btn-link { background-color: var(--accent-color); color: var(--bg-color); padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-bottom: 25px; transition: opacity 0.2s; display: inline-block; }
        .btn-link:hover { opacity: 0.9; }

        .tag { background: #334155; color: #cbd5e1; padding: 4px 10px; border-radius: 6px; font-size: 0.9rem; margin-right: 8px; margin-bottom: 8px; display: inline-block; }
        .pos { color: var(--success); }
        .neg { color: var(--error); }
        .warn { color: var(--warning); }
    </style>
</head>
<body x-data="{ 
    selectedTrader: null, 
    showModal: false, 
    renderDetail() {
        $nextTick(() => {
            const t = traders[this.selectedTrader];
            if (!t) return;
            const ctx = document.getElementById('detailChart').getContext('2d');
            if (window.myDetailChart) window.myDetailChart.destroy();
            
            const history = [...t.roiHistory].sort((a,b) => parseInt(a.cTime) - parseInt(b.cTime));
            const startValue = parseFloat(history[0].rate);
            const data = history.map(h => parseFloat(h.rate) - startValue);
            
            window.myDetailChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: history.map(h => new Date(parseInt(h.cTime)).toLocaleDateString()),
                    datasets: [{
                        label: 'Relative ROI (30D) %',
                        data: data,
                        borderColor: '#38bdf8',
                        backgroundColor: 'rgba(56, 189, 248, 0.1)',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: { 
                    responsive: true, maintainAspectRatio: false,
                    scales: { 
                        y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                        x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    }
                }
            });
        });
    }
}">
    <div class="container">
        <header>
            <h1>Bitget Elite Trader Dashboard</h1>
            <p>Evaluating Profitability and Long-Term Consistency</p>
        </header>

        <div class="table-container">
            <table id="mainTable" class="display nowrap" style="width:100%">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Trader</th>
                        <th>Sharpe (30D)</th>
                        <th>ROI (30D)</th>
                        <th>ROI (Life)</th>
                        <th>Total Profit</th>
                        <th>MDD (Life)</th>
                        <th>Days</th>
                        <th>Copiers</th>
                    </tr>
                </thead>
                <tbody>
                    {% for t in traders %}
                    <tr @click="selectedTrader = {{ loop.index0 }}; showModal = true; renderDetail()">
                        <td>{{ loop.index }}</td>
                        <td style="font-weight:bold;">{{ t.traderName }}</td>
                        <td class="{{ 'pos' if t.sharpeRatio > 1.5 else 'neg' if t.sharpeRatio < 0.5 else 'warn' }}">
                            {{ t.sharpeRatio | round(3) }}
                        </td>
                        <td class="{{ 'pos' if t.roi_30d > 0 else 'neg' }}">{{ t.roi_30d | round(2) }}%</td>
                        <td class="{{ 'pos' if t.roi > 0 else 'neg' }}" style="font-weight:bold;">{{ t.roi | round(2) }}%</td>
                        <td style="color: var(--warning)">{{ t.totalProfit }}</td>
                        <td class="neg">{{ t.mdd_life | round(2) }}%</td>
                        <td>{{ t.tradeDays }}</td>
                        <td>{{ t.followCount }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Drill-down Modal -->
    <template x-if="showModal">
        <div class="modal-overlay" @click.self="showModal = false">
            <div class="modal-content">
                <span class="close-btn" @click="showModal = false">&times;</span>
                <h2 x-text="traders[selectedTrader].traderName"></h2>
                
                <a :href="'https://www.bitget.com/copy-trading/futures-trader-v1/' + traders[selectedTrader].traderId + '/chart'" 
                   target="_blank" 
                   class="btn-link">
                    ↗️ View Full Profile & 90D History on Bitget
                </a>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-val" style="color: var(--warning)" x-text="traders[selectedTrader].totalProfit"></div>
                        <div class="stat-label">Total Profit (Life)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val" :class="traders[selectedTrader].roi >= 0 ? 'pos' : 'neg'" x-text="traders[selectedTrader].roi.toFixed(2) + '%'"></div>
                        <div class="stat-label">ROI (Life)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val" :class="traders[selectedTrader].roi_30d >= 0 ? 'pos' : 'neg'" x-text="traders[selectedTrader].roi_30d.toFixed(2) + '%'"></div>
                        <div class="stat-label">ROI (30D)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val" x-text="traders[selectedTrader].sharpeRatio.toFixed(3)"></div>
                        <div class="stat-label">Sharpe (30D)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val" style="color: #94a3b8" x-text="traders[selectedTrader].tradeDays"></div>
                        <div class="stat-label">Active Days</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val" style="color: var(--accent-color)" x-text="traders[selectedTrader].followCount"></div>
                        <div class="stat-label">Total Copiers</div>
                    </div>
                </div>

                <div class="chart-container">
                    <canvas id="detailChart"></canvas>
                </div>

                <div style="margin-top: 20px;">
                    <h3>Open Positions (Active Traces)</h3>
                    <div style="padding: 10px 0;">
                        <template x-for="symbol in traders[selectedTrader].openPositions">
                            <span class="tag" x-text="symbol"></span>
                        </template>
                        <template x-if="traders[selectedTrader].openPositions.length === 0">
                            <div style="color: #64748b;">No active traces.</div>
                        </template>
                    </div>
                </div>
            </div>
        </div>
    </template>

    <script>
        const traders = {{ traders_json }};
        $(document).ready(function() {
            $('#mainTable').DataTable({ 
                pageLength: 25, 
                order: [[2, 'desc']],
                columnDefs: [
                    { targets: [2,3,4,5,6,7,8], className: 'dt-right' }
                ]
            });
        });
    </script>
</body>
</html>
"""

def generate_dashboard(results, output_path="dashboard.html"):
    template = Template(DASHBOARD_TEMPLATE)
    html_content = template.render(traders=results, traders_json=json.dumps(results))
    with open(output_path, "w") as f: f.write(html_content)
    print(f"Dashboard generated: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)
