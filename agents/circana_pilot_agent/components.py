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
    <style>
        :root {
            --bg-color: #ffffff;
            --border: #e2e8f0;
            --t1: #0f172a;
            --t2: #475569;
            --t3: #64748b;
            --primary: #2563eb;
            --green: #10b981;
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
        .panel {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .panel-lead {
            font-size: 13.5px;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--t1);
        }
        .kpi-row {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
        }
        .kpi {
            flex: 1;
            background: #f8fafc;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
        }
        .kpi-label {
            font-size: 10px;
            text-transform: uppercase;
            color: var(--t3);
            font-weight: 700;
            letter-spacing: 0.05em;
        }
        .kpi-value {
            font-size: 22px;
            font-weight: 700;
            color: var(--t1);
            margin: 6px 0 4px;
        }
        .kpi-value.det { color: #002f6c; }
        .kpi-value.prob { color: #ff6f00; }
        .kpi-value.total { color: var(--green); }
        .kpi-sub {
            font-size: 11px;
            color: var(--t3);
        }
        .panel-line {
            color: var(--t2);
            font-size: 12px;
            line-height: 1.5;
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
        .chip-row {
            display: flex;
            gap: 8px;
            margin-top: 16px;
        }
        .btn-activate {
            background: linear-gradient(135deg, var(--primary), #1d4ed8);
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 11.5px;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .btn-activate:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="panel">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div class="panel-lead">All set — your audience is built, scaled, and sized.</div>
            <button class="btn-download" onclick="downloadCSV()">Download CSV</button>
        </div>
        <div class="kpi-row cols-3" id="kpis">
            <!-- Dynamically populated sizing cards -->
        </div>
        <div class="panel-line" id="panel-desc">
            From one question to an audience that’s ready to go: verified lapsed households expanded with ProScore lookalikes.
        </div>
        <div class="chip-row">
            <button class="btn-activate" onclick="activatePartner('LiveRamp')">Activate LiveRamp</button>
            <button class="btn-activate" onclick="activatePartner('Google Ads')">Activate Google DV360</button>
            <button class="btn-activate" onclick="activatePartner('Meta Ads')">Activate Meta Ads</button>
        </div>
    </div>

    <script>
        const data = window.INJECTED_DATA || {};
        const pName = data.product_name || "Tropicana Pure Premium 52oz";
        const seedCount = data.seed_count || 412400;
        const scaledCount = data.scaled_size || "3.1M";
        const reachCount = data.reach_count || "2.86M";

        document.getElementById('kpis').innerHTML = `
            <div class="kpi"><div class="kpi-label">Built · verified seed</div><div class="kpi-value det">${(seedCount/1000).toFixed(1)}<small>K</small></div><div class="kpi-sub">lapsed ${pName} HH</div></div>
            <div class="kpi"><div class="kpi-label">Scaled · Complete</div><div class="kpi-value prob">${scaledCount}</div><div class="kpi-sub">ProScore lookalikes</div></div>
            <div class="kpi"><div class="kpi-label">Sized · addressable reach</div><div class="kpi-value total">${reachCount}</div><div class="kpi-sub">ready to activate</div></div>
        `;

        document.getElementById('panel-desc').innerHTML = `From one question to an audience that’s ready to go: <b>${seedCount.toLocaleString()}</b> verified lapsed ${pName} households, expanded to <b>${scaledCount}</b> with ProScore, with <b>${reachCount}</b> reachable for activation. Pick a destination and we’re off.`;

        function downloadCSV() {
            let csvContent = "data:text/csv;charset=utf-8,";
            csvContent += "Metric,Value\n";
            csvContent += `Product,"${pName}"\n`;
            csvContent += `Verified Seed,${seedCount}\n`;
            csvContent += `Scaled Audience,${scaledCount}\n`;
            csvContent += `Addressable Reach,${reachCount}\n`;
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `audience_reach_${pName.replace(/\s+/g, '_')}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        function activatePartner(partner) {
            window.parent.postMessage({
                type: 'USER_ACTION',
                actionId: 'btn_activate',
                payload: { partners: [partner] }
            }, '*');
        }
    </script>
</body>
</html>
"""

EXECUTION_CHAIN_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <title>Execution Pipeline</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --border: #e2e8f0;
            --t1: #0f172a;
            --t3: #64748b;
            --primary: #2563eb;
            --green: #10b981;
        }
        body {
            font-family: 'Poppins', system-ui, sans-serif;
            margin: 0; padding: 12px;
        }
        .chain-box {
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            background: #f8fafc;
        }
        .chain-lead {
            font-size: 13px; font-weight: 700; color: var(--t1);
            margin-bottom: 16px;
        }
        .chain-row {
            display: flex; align-items: center; gap: 12px;
        }
        .chain-step {
            flex: 1; background: #fff;
            border: 2px solid var(--border);
            border-radius: 8px; padding: 12px;
            text-align: center;
        }
        .chain-step.ok { border-color: var(--green); }
        .chain-step.on { border-color: var(--primary); }
        .chain-name { font-weight: 700; font-size: 12px; color: var(--t1); }
        .chain-sub { font-size: 10.5px; color: var(--t3); margin-top: 4px; }
    </style>
</head>
<body>
    <div class="chain-box">
        <div class="chain-lead">Here’s how I’ll get this done — three steps handing results straight to the next.</div>
        <div class="chain-row">
            <div class="chain-step ok">
                <div class="chain-name">1 · Build</div>
                <div class="chain-sub">verified lapsed-buyer audience</div>
            </div>
            <div style="color:var(--t3);font-weight:700">→</div>
            <div class="chain-step ok">
                <div class="chain-name">2 · Scale</div>
                <div class="chain-sub">ProScore expansion</div>
            </div>
            <div style="color:var(--t3);font-weight:700">→</div>
            <div class="chain-step on">
                <div class="chain-name">3 · Size</div>
                <div class="chain-sub">addressable reach</div>
            </div>
        </div>
    </div>
</body>
</html>
"""

DEMOGRAPHIC_PROFILE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <title>Demographic Profile</title>
    <style>
        body {
            font-family: 'Poppins', system-ui, sans-serif;
            margin: 0; padding: 12px;
            color: #0f172a; background: #ffffff;
            font-size: 12.5px;
        }
        .panel {
            border: 1px solid #e2e8f0;
            border-radius: 10px; padding: 16px;
        }
        .dp-title { font-weight: 700; font-size: 14px; margin-bottom: 12px; }
        .stat-strip {
            display: flex; gap: 12px; margin-bottom: 20px;
        }
        .stat-card {
            flex: 1; background: #f8fafc; border: 1px solid #e2e8f0;
            border-radius: 8px; padding: 12px;
        }
        .stat-label { font-size: 10px; text-transform: uppercase; color: #64748b; font-weight: 700; }
        .stat-num { font-size: 22px; font-weight: 700; margin: 4px 0; color: #0f172a; }
        .dp-bar-row {
            display: flex; align-items: center; gap: 12px; margin-bottom: 8px;
        }
        .dp-lbl { width: 100px; font-weight: 500; font-size: 11.5px; }
        .dp-track { flex: 1; background: #f1f5f9; height: 16px; border-radius: 8px; overflow: hidden; }
        .dp-fill { background: #ff6f00; height: 100%; }
        .dp-pct { width: 40px; text-align: right; font-weight: 600; }
    </style>
</head>
<body>
    <div class="panel">
        <div class="dp-title">Audience Profile · 3.1M Households</div>
        <div class="stat-strip">
            <div class="stat-card"><div class="stat-label">Median Age</div><div class="stat-num">47 yrs</div></div>
            <div class="stat-card"><div class="stat-label">Median Income</div><div class="stat-num">$78K</div></div>
            <div class="stat-card"><div class="stat-label">Avg HH Size</div><div class="stat-num">3.1</div></div>
            <div class="stat-card"><div class="stat-label">Kids in HH</div><div class="stat-num">52%</div></div>
        </div>
        <div class="dp-title" style="margin-top:16px;">Household Income Distribution</div>
        <div class="dp-bar-row"><div class="dp-lbl">&lt; $50K</div><div class="dp-track"><div class="dp-fill" style="width:18%;background:#94a3b8"></div></div><div class="dp-pct">18%</div></div>
        <div class="dp-bar-row"><div class="dp-lbl">$50 – 75K</div><div class="dp-track"><div class="dp-fill" style="width:38%"></div></div><div class="dp-pct">24%</div></div>
        <div class="dp-bar-row"><div class="dp-lbl">$75 – 100K</div><div class="dp-track"><div class="dp-fill" style="width:30%"></div></div><div class="dp-pct">22%</div></div>
        <div class="dp-bar-row"><div class="dp-lbl">$100 – 150K</div><div class="dp-track"><div class="dp-fill" style="width:28%"></div></div><div class="dp-pct">21%</div></div>
        <div class="dp-bar-row"><div class="dp-lbl">$150K+</div><div class="dp-track"><div class="dp-fill" style="width:15%;background:#94a3b8"></div></div><div class="dp-pct">15%</div></div>
    </div>
</body>
</html>
"""
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

