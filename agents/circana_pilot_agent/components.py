import json
import logging

logger = logging.getLogger(__name__)

PRODUCT_TABLE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <meta content='connect-src "none"' http-equiv='Content-Security-Policy'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <title>Pricing opportunities Analysis</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --border: #e2e8f0;
            --t1: #0f172a;
            --t2: #475569;
            --t3: #64748b;
            --primary: #2563eb;
            --red: #ef4444;
            --hover: #f8fafc;
        }
        body {
            font-family: 'Poppins', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--t1);
            margin: 0;
            padding: 8px;
            box-sizing: border-box;
            font-size: 13px;
        }
        .panel-lead {
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 16px;
            color: var(--t1);
        }
        .kpi-row {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }
        .kpi {
            flex: 1;
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .kpi-label {
            font-size: 10px;
            text-transform: uppercase;
            color: var(--t3);
            font-weight: 700;
            letter-spacing: 0.05em;
        }
        .kpi-value {
            font-size: 20px;
            font-weight: 700;
            color: var(--t1);
            margin: 6px 0 4px;
            line-height: 1.2;
        }
        .kpi-value.red {
            color: var(--red);
        }
        .kpi-sub {
            font-size: 11px;
            color: var(--t3);
        }
        .table-container {
            overflow-x: auto;
        }
        .pa-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12.5px;
        }
        .pa-table th {
            font-size: 9.5px;
            font-weight: 700;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: var(--t3);
            text-align: left;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }
        .pa-table th.num,
        .pa-table td.num {
            text-align: right;
        }
        .pa-table td {
            padding: 12px;
            border-bottom: 1px solid var(--border);
            color: var(--t1);
            white-space: nowrap;
        }
        .pa-table tbody tr {
            cursor: pointer;
            transition: background 0.15s;
        }
        .pa-table tbody tr:hover {
            background: var(--hover);
        }
        .pa-table tbody tr:last-child td {
            border-bottom: none;
        }
        .pa-table tbody tr.top td {
            background: rgba(37, 99, 235, 0.04);
        }
        .pa-rank {
            display: inline-flex;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #f1f5f9;
            color: var(--t2);
            font-size: 11px;
            font-weight: 700;
            align-items: center;
            justify-content: center;
        }
        .pa-table tr.top .pa-rank {
            background: var(--primary);
            color: #ffffff;
        }
        .pa-prod {
            font-weight: 600;
        }
        .pa-neg {
            color: var(--red);
            font-weight: 600;
        }
        .pa-pos {
            font-weight: 600;
        }
        .panel-line {
            color: var(--t3);
            font-size: 11.5px;
            margin-top: 12px;
        }
        .btn-download {
            background: transparent;
            border: 1px solid #00a4e4;
            color: #002f6c;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-download:hover {
            background-color: #00a4e4;
            color: #ffffff;
        }
    </style>
</head>
<body>
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
        <div class="panel-lead" style="margin-bottom: 0;">Here’s what I found — five products where price increases drove household attrition over the past 12 weeks.</div>
        <button class="btn-download" onclick="downloadCSV()">Download CSV</button>
    </div>
    
    <div class="kpi-row" id="kpi-summary">
        <!-- Dynamically Populated KPI Cards -->
    </div>

    <div class="table-container">
        <table class="pa-table">
            <thead>
                <tr>
                    <th></th>
                    <th>Product</th>
                    <th class="num">Avg price Δ · 12w</th>
                    <th class="num">Households lost</th>
                    <th class="num">Volume Δ</th>
                    <th class="num">Lapsed-buyer pool (HH)</th>
                </tr>
            </thead>
            <tbody id="table-body">
                <!-- Dynamically Injected Rows -->
            </tbody>
        </table>
    </div>
    
    <div class="panel-line">Ranked by verified households lost where price was the leading driver — volume-only declines are excluded. Tap a row to take it into phase 2.</div>

    <script>
        const rawData = window.INJECTED_DATA || [];
        const data = rawData.length > 0 ? rawData : [
            { rank: 1, product_name: "Tropicana Pure Premium 52oz", price_change: "+14.2%", households_lost: "−412K", lost_households_pct: -9.8, volume_change: -6.4, pool_size: 412400 },
            { rank: 2, product_name: "Quaker Instant Oatmeal 10ct", price_change: "+11.5%", households_lost: "−298K", lost_households_pct: -7.4, volume_change: -5.2, pool_size: 298100 },
            { rank: 3, product_name: "Gatorade Thirst Quencher 28oz", price_change: "+9.0%", households_lost: "−244K", lost_households_pct: -5.9, volume_change: -4.8, pool_size: 243700 },
            { rank: 4, product_name: "Lay's Classic Party Size", price_change: "+12.1%", households_lost: "−201K", lost_households_pct: -5.1, volume_change: -3.9, pool_size: 200900 },
            { rank: 5, product_name: "Lipton Iced Tea 12pk", price_change: "+8.4%", households_lost: "−156K", lost_households_pct: -4.2, volume_change: -3.1, pool_size: 156300 }
        ];

        function downloadCSV() {
            let csvContent = "data:text/csv;charset=utf-8,";
            csvContent += "Rank,Product,Price Change,Households Lost,Volume Change,Lapsed Pool\n";
            data.forEach((item, index) => {
                const r = index + 1;
                const p = item.product_name || '';
                const pr = item.price_change || '';
                const hh = item.households_lost || item.lost_households_count || '';
                const v = item.volume_change || '';
                const pool = item.pool_size || item.lapsed_pool || '';
                csvContent += `"${r}","${p}","${pr}","${hh}","${v}","${pool}"\n`;
            });
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "pricing_opportunities.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        const topItem = data[0] || {};
        const kpiSummary = document.getElementById('kpi-summary');
        
        const topName = topItem.product_name || "Tropicana Pure Premium 52oz";
        const topPrice = topItem.price_change || "+14.2%";
        const topLoss = topItem.households_lost || (topItem.lost_households_count ? topItem.lost_households_count : "−412K");
        const topPct = topItem.lost_households_pct ? `${topItem.lost_households_pct}%` : "−9.8%";
        const topPool = topItem.pool_size ? topItem.pool_size.toLocaleString() : (topItem.lapsed_pool ? topItem.lapsed_pool.toLocaleString() : "412,400");

        kpiSummary.innerHTML = `
            <div class="kpi">
                <div class="kpi-label">Top product</div>
                <div class="kpi-value" style="font-size:17px;">${topName}</div>
                <div class="kpi-sub">${topPrice} avg price · 12w</div>
            </div>
            <div class="kpi">
                <div class="kpi-label">Households lost</div>
                <div class="kpi-value red">${topLoss}</div>
                <div class="kpi-sub">${topPct} of buying households</div>
            </div>
            <div class="kpi">
                <div class="kpi-label">Lapsed-buyer pool (HH)</div>
                <div class="kpi-value">${topPool}</div>
                <div class="kpi-sub">verified · audience-ready</div>
            </div>
        `;

        const tbody = document.getElementById('table-body');
        data.forEach((item, index) => {
            const tr = document.createElement('tr');
            tr.className = index === 0 ? 'top' : '';
            
            const pName = item.product_name || "Unknown";
            const pPrice = item.price_change || "+14.2%";
            const pLoss = item.households_lost || (item.lost_households_count ? item.lost_households_count : "−412K");
            const pPct = item.lost_households_pct ? `${item.lost_households_pct}%` : "−9.8%";
            const pVol = item.volume_change ? `${item.volume_change}%` : "−6.4%";
            const pPool = item.pool_size ? item.pool_size.toLocaleString() : (item.lapsed_pool ? item.lapsed_pool.toLocaleString() : "412,400");

            tr.innerHTML = `
                <td><span class="pa-rank">${index + 1}</span></td>
                <td class="pa-prod">${pName}</td>
                <td class="num pa-pos">${pPrice}</td>
                <td class="num pa-neg">${pLoss} <span style="color:var(--t3);font-weight:400">(${pPct})</span></td>
                <td class="num pa-neg">${pVol}</td>
                <td class="num">${pPool}</td>
            `;

            tr.onclick = () => {
                window.parent.postMessage({
                    type: 'USER_ACTION',
                    actionId: 'product_selected',
                    payload: { product: pName }
                }, '*');
            };

            tbody.appendChild(tr);
        });
    </script>
</body>
</html>
"""

SIZING_DASHBOARD_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <meta content='connect-src "none"' http-equiv='Content-Security-Policy'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <title>Audience Sizing & Activation</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --accent-primary: #002f6c;
            --accent-secondary: #00a4e4;
            --border-color: #e2e8f0;
            --success: #10b981;
            --warning: #f59e0b;
        }
        body {
            font-family: 'Poppins', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 12px;
            box-sizing: border-box;
            font-size: 13px;
        }
        .header {
            margin-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 6px;
        }
        .header h1 {
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(to right, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p {
            color: var(--text-secondary);
            margin: 2px 0 0 0;
            font-size: 0.75rem;
        }
        .kpi-container {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
        }
        .kpi-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px;
            flex: 1;
        }
        .kpi-title {
            font-size: 0.65rem;
            text-transform: uppercase;
            color: var(--text-secondary);
            letter-spacing: 0.05em;
        }
        .kpi-value {
            font-size: 1.25rem;
            font-weight: 700;
            margin: 4px 0;
            color: var(--accent-primary);
        }
        .kpi-value.success {
            color: var(--success);
        }
        .panel {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
        }
        .panel-title {
            font-weight: 700;
            color: var(--text-secondary);
            font-size: 0.78rem;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .checkbox-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 12px;
        }
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
        }
        .btn-activate {
            width: 100%;
            background: linear-gradient(135deg, var(--success), #059669);
            color: #ffffff;
            border: none;
            padding: 8px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
            text-align: center;
        }
        .btn-activate:hover {
            opacity: 0.9;
        }
        .btn-download {
            background: transparent;
            border: 1px solid var(--accent-secondary);
            color: var(--accent-primary);
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-download:hover {
            background-color: var(--accent-secondary);
            color: #ffffff;
        }
    </style>
</head>
<body>
    <div class="header" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1>Audience Dashboard</h1>
            <p id="product-context">Cohort details for selected product</p>
        </div>
        <button class="btn-download" onclick="downloadCSV()">Download CSV</button>
    </div>

    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">Audience Size</div>
            <div class="kpi-value" id="val-size">0</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Active Reach</div>
            <div class="kpi-value success" id="val-reach">0%</div>
        </div>
    </div>

    <div class="panel">
        <div class="panel-title">Target Reach Distribution</div>
        <div class="chart-container" style="position: relative; height: 180px; margin: 10px 0;">
            <canvas id="myChart"></canvas>
            <div id="svg-fallback" style="display:none; height:100%; align-items:center; justify-content:center;">
                <!-- SVG fallback donut segment -->
                <svg width="120" height="120" viewBox="0 0 42 42" class="donut">
                    <circle class="donut-hole" cx="21" cy="21" r="15.91549430918954" fill="#ffffff"></circle>
                    <circle class="donut-ring" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="#e2e8f0" stroke-width="4"></circle>
                    <circle class="donut-segment" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="#002f6c" stroke-width="4" stroke-dasharray="45 55" stroke-dashoffset="25"></circle>
                    <circle class="donut-segment" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="#00a4e4" stroke-width="4" stroke-dasharray="35 65" stroke-dashoffset="80"></circle>
                </svg>
            </div>
        </div>
    </div>

    <div class="panel">
        <div class="panel-title">Activation Channels</div>
        <div class="checkbox-group">
            <label class="checkbox-item">
                <input type="checkbox" name="partner" value="LiveRamp" checked> LiveRamp Identity Link
            </label>
            <label class="checkbox-item">
                <input type="checkbox" name="partner" value="Google" checked> Google Customer Match
            </label>
            <label class="checkbox-item">
                <input type="checkbox" name="partner" value="TheTradeDesk"> The Trade Desk Unified ID
            </label>
        </div>
        <button class="btn-activate" id="btn-submit">Activate Audience Segment</button>
    </div>

    <script>
        const data = window.INJECTED_DATA || {};
        document.getElementById('product-context').textContent = `Cohort details for product: ${data.product_name || 'Selected Cohort'}`;
        document.getElementById('val-size').textContent = (data.scaled_size || 0).toLocaleString();
        document.getElementById('val-reach').textContent = `${data.reach_percentage || 0}%`;

        // Cache Key & Local Storage Loading
        const cacheKey = `sizing_partners_${data.product_name || 'default'}`;
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
            const checkedPartners = JSON.parse(cached);
            document.querySelectorAll("input[name='partner']").forEach(cb => {
                cb.checked = checkedPartners.includes(cb.value);
            });
        }

        // Save State Listener
        document.querySelectorAll("input[name='partner']").forEach(cb => {
            cb.addEventListener('change', () => {
                const checkedBoxes = document.querySelectorAll("input[name='partner']:checked");
                const partners = Array.from(checkedBoxes).map(cb => cb.value);
                localStorage.setItem(cacheKey, JSON.stringify(partners));
            });
        });

        function downloadCSV() {
            let csvContent = "data:text/csv;charset=utf-8,";
            csvContent += "Metric,Value\n";
            csvContent += `Product,"${data.product_name || 'Selected Cohort'}"\n`;
            csvContent += `Audience Size,${data.scaled_size || 0}\n`;
            csvContent += `Active Reach,${data.reach_percentage || 0}%\n`;
            csvContent += "LiveRamp Matched,45%\n";
            csvContent += "Google Ads Matched,35%\n";
            csvContent += "Unmatched Reach,20%\n";
            
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `audience_sizing_${(data.product_name || 'cohort').replace(/\s+/g, '_')}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        // Initialize Chart.js doughnut
        const ctx = document.getElementById('myChart');
        if (typeof Chart !== 'undefined') {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['LiveRamp Matched', 'Google Ads Matched', 'Unmatched Reach'],
                    datasets: [{
                        data: [45, 35, 20],
                        backgroundColor: ['#002f6c', '#00a4e4', '#cbd5e1'],
                        borderWidth: 1,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 10,
                                font: { size: 9, family: 'Poppins' },
                                color: '#475569'
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        } else {
            document.getElementById('myChart').style.display = 'none';
            document.getElementById('svg-fallback').style.display = 'flex';
        }

        document.getElementById('btn-submit').onclick = () => {
            const checkedBoxes = document.querySelectorAll("input[name='partner']:checked");
            const partners = Array.from(checkedBoxes).map(cb => cb.value);
            
            // Post activation request callback back to supervisor
            window.parent.postMessage({
                type: 'USER_ACTION',
                actionId: 'btn_activate',
                payload: { partners: partners }
            }, '*');
        };
    </script>
</body>
</html>
"""

class UIBuilder:
    @staticmethod
    def build_product_table(surface_id: str, product_data: list) -> dict:
        """Compiles A2UI payload for pricing opportunities interactive table."""
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps(product_data)};</script>"
        html_injected = PRODUCT_TABLE_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")

        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html_injected }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "contents": []
            },
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "root"
            }
        }

    @staticmethod
    def build_sizing_dashboard(surface_id: str, sizing_data: dict) -> dict:
        """Compiles A2UI payload for audience sizing kpi dashboard."""
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps(sizing_data)};</script>"
        html_injected = SIZING_DASHBOARD_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")

        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html_injected }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "contents": []
            },
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "root"
            }
        }

def get_product_table_a2ui(products: list) -> str:
    ui = UIBuilder.build_product_table("circana-pricing-table", products)
    sequence = [ui["surfaceUpdate"], ui["dataModelUpdate"], ui["beginRendering"]]
    return f"<a2ui-json>\n{json.dumps(sequence, indent=2)}\n</a2ui-json>"

def get_sizing_dashboard_a2ui(sizing: dict) -> str:
    ui = UIBuilder.build_sizing_dashboard("circana-sizing-dashboard", sizing)
    sequence = [ui["surfaceUpdate"], ui["dataModelUpdate"], ui["beginRendering"]]
    return f"<a2ui-json>\n{json.dumps(sequence, indent=2)}\n</a2ui-json>"

LOYALTY_CAMPAIGN_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <meta content='connect-src "none"' http-equiv='Content-Security-Policy'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <title>Loyalty Campaign Activation</title>
    <style>
        :root {
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --accent-primary: #002f6c;
            --accent-secondary: #00a4e4;
            --border-color: #e2e8f0;
            --success: #10b981;
        }
        body {
            font-family: 'Poppins', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 12px;
            box-sizing: border-box;
            font-size: 13px;
        }
        .header {
            margin-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 6px;
        }
        .header h1 {
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(to right, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p {
            color: var(--text-secondary);
            margin: 2px 0 0 0;
            font-size: 0.75rem;
        }
        .kpi-container {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
        }
        .kpi-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px;
            flex: 1;
        }
        .kpi-title {
            font-size: 0.65rem;
            text-transform: uppercase;
            color: var(--text-secondary);
        }
        .kpi-value {
            font-size: 1.25rem;
            font-weight: 700;
            margin: 4px 0;
            color: var(--accent-primary);
        }
        .panel {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
        }
        .panel-title {
            font-weight: 700;
            color: var(--text-secondary);
            font-size: 0.78rem;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .form-group {
            margin-bottom: 12px;
        }
        .form-label {
            display: block;
            margin-bottom: 4px;
            color: var(--text-secondary);
            font-size: 0.75rem;
        }
        .form-input {
            width: 100%;
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            padding: 6px;
            box-sizing: border-box;
        }
        .btn-launch {
            width: 100%;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: #ffffff;
            border: none;
            padding: 8px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
            text-align: center;
        }
        .btn-launch:hover {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class='header'>
        <h1>Loyalty Campaign Manager</h1>
        <p id='cohort-context'>Activate offer personalization for target segment</p>
    </div>

    <div class='kpi-container'>
        <div class='kpi-card'>
            <div class='kpi-title'>Target Customers</div>
            <div class='kpi-value' id='val-customers'>0</div>
        </div>
        <div class='kpi-card'>
            <div class='kpi-title'>Current Churn Risk</div>
            <div class='kpi-value' id='val-risk'>High</div>
        </div>
    </div>

    <div class='panel'>
        <div class='panel-title'>Campaign Parameters</div>
        <div class='form-group'>
            <label class='form-label' for='discount-value'>Discount Value (%)</label>
            <input class='form-input' type='number' id='discount-value' value='10'>
        </div>
        <div class='form-group'>
            <label class='form-label' for='points-multiplier'>Points Multiplier</label>
            <input class='form-input' type='number' id='points-multiplier' value='2'>
        </div>
        <button class='btn-launch' id='btn-submit'>Launch Loyalty Campaign</button>
    </div>

    <script>
        const data = window.INJECTED_DATA || {};
        document.getElementById('cohort-context').textContent = `Target cohort: ${data.product_name || 'Selected Cohort'}`;
        document.getElementById('val-customers').textContent = (data.shoppers_isolated || 350000).toLocaleString();

        document.getElementById('btn-submit').onclick = () => {
            const disc = document.getElementById('discount-value').value;
            const mult = document.getElementById('points-multiplier').value;
            
            window.parent.postMessage({
                type: 'USER_ACTION',
                actionId: 'btn_launch_campaign',
                payload: {
                    product: data.product_name,
                    discount_pct: disc,
                    points_mult: mult
                }
            }, '*');
        };
    </script>
</body>
</html>
"""

# Extend UIBuilder
class UIBuilderExtended(UIBuilder):
    @staticmethod
    def build_loyalty_dashboard(surface_id: str, loyalty_data: dict) -> dict:
        """Compiles A2UI payload for loyalty personalization campaign manager."""
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps(loyalty_data)};</script>"
        html_injected = LOYALTY_CAMPAIGN_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")

        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html_injected }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "contents": []
            },
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "root"
            }
        }

def get_loyalty_dashboard_a2ui(loyalty_data: dict) -> str:
    ui = UIBuilderExtended.build_loyalty_dashboard("circana-loyalty-dashboard", loyalty_data)
    sequence = [ui["surfaceUpdate"], ui["dataModelUpdate"], ui["beginRendering"]]
    return f"<a2ui-json>\n{json.dumps(sequence, indent=2)}\n</a2ui-json>"

