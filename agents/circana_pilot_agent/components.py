import json
import logging

logger = logging.getLogger(__name__)

PRODUCT_TABLE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <meta content='connect-src "none"' http-equiv='Content-Security-Policy'>
    <title>Pricing opportunities Analysis</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-primary: #38bdf8;
            --accent-secondary: #818cf8;
            --border-color: #334155;
            --success: #10b981;
            --warning: #f59e0b;
        }
        body {
            font-family: system-ui, -apple-system, sans-serif;
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
        .table-container {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }
        th {
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 2px solid var(--border-color);
            font-size: 0.72rem;
            text-transform: uppercase;
            padding: 8px;
        }
        td {
            padding: 8px;
            border-bottom: 1px solid var(--border-color);
        }
        tr:last-child td {
            border-bottom: none;
        }
        tr:hover {
            background-color: rgba(255, 255, 255, 0.02);
        }
        .btn-select {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: #ffffff;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .btn-select:hover {
            opacity: 0.9;
        }
        .loss-badge {
            color: var(--warning);
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Buyer Attrition & Pricing Analysis</h1>
        <p>Identify products with lost households due to 52-week price changes. Select a product to initiate the activation pipeline.</p>
    </div>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Lost Households %</th>
                    <th>Volume Change</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody id="table-body">
                <!-- Dynamically Injected Rows -->
            </tbody>
        </table>
    </div>

    <script>
        const data = window.INJECTED_DATA || [];
        const tbody = document.getElementById('table-body');
        
        data.forEach(item => {
            const tr = document.createElement('tr');
            
            const nameTd = document.createElement('td');
            nameTd.textContent = item.product_name;
            tr.appendChild(nameTd);
            
            const lossTd = document.createElement('td');
            lossTd.className = 'loss-badge';
            lossTd.textContent = `${item.lost_households_pct}%`;
            tr.appendChild(lossTd);
            
            const volTd = document.createElement('td');
            volTd.textContent = `${item.volume_change}%`;
            tr.appendChild(volTd);
            
            const actionTd = document.createElement('td');
            const btn = document.createElement('button');
            btn.className = 'btn-select';
            btn.textContent = 'Select Cohort';
            btn.onclick = () => {
                // Post callback action back to supervisor agent context
                window.parent.postMessage({
                    type: 'USER_ACTION',
                    actionId: 'product_selected',
                    payload: { product: item.product_name }
                }, '*');
            };
            actionTd.appendChild(btn);
            tr.appendChild(actionTd);
            
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
    <title>Audience Sizing & Activation</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-primary: #38bdf8;
            --accent-secondary: #818cf8;
            --border-color: #334155;
            --success: #10b981;
            --warning: #f59e0b;
        }
        body {
            font-family: system-ui, -apple-system, sans-serif;
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
    </style>
</head>
<body>
    <div class="header">
        <h1>Audience Dashboard</h1>
        <p id="product-context">Cohort details for selected product</p>
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
    <title>Loyalty Campaign Activation</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-primary: #ec4899;
            --accent-secondary: #f43f5e;
            --border-color: #334155;
            --success: #10b981;
        }
        body {
            font-family: system-ui, -apple-system, sans-serif;
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

