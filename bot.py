import os, time, random, threading
from flask import Flask, render_template_string, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)
bot_running = False
status_text = "Ready to start..."

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>FB Marketplace Bot (Custom)</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; padding: 20px; }
        .container { max-width: 900px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 10px; }
        h2 { text-align: center; color: #f5b041; }
        label { display: block; margin-top: 12px; font-weight: bold; color: #ccc; }
        textarea, input { width: 100%; padding: 10px; margin-top: 5px; background: #2c2c2c; color: #fff; border: 1px solid #444; border-radius: 5px; box-sizing: border-box; }
        .btns { text-align: center; margin: 20px 0; }
        button { padding: 12px 25px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin: 0 10px; }
        .start { background: #28a745; color: white; }
        .stop { background: #dc3545; color: white; }
        .status { text-align: center; padding: 10px; background: #262626; border-radius: 5px; color: #00ffcc; font-weight: bold; }
    </style>
</head>
<body>
<div style="text-align: center; margin-bottom: 15px;">
<img src="{{ url_for('static', filename='pic.png') }}" alt="Profile" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 2px solid #f5b041;">
</div>
<div class="container">
    <h2>CHODRY RAHEEM</h2>
    <label>Paste Multiple Cookies (1 Account = 1 Line):</label>
    <textarea id="cookies" rows="3" placeholder="c_user=1000...; xs=..."></textarea>

    <label>Locations / US Cities (1 City Per Line):</label>
    <textarea id="locations" rows="4" placeholder="Dallas, Texas&#10;Houston, Texas&#10;Austin, Texas"></textarea>

    <label>Ad Title:</label>
    <input type="text" id="title" placeholder="HVAC & Furnace Repair Service - Fast Same Day">

    <label>Price ($):</label>
    <input type="text" id="price" value="85">

    <label>Description:</label>
    <textarea id="desc" rows="4" placeholder="24/7 Heating & AC Repair. Call Now: (877) 798-6456"></textarea>

    <div class="btns">
        <button class="start" onclick="startBot()">Start Automation</button>
        <button class="stop" onclick="stopBot()">Stop All</button>
    </div>
    <div class="status" id="status">Status: Ready</div>
</div>

<script>
function startBot() {
    fetch('/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            cookies: document.getElementById('cookies').value,
            locations: document.getElementById('locations').value,
            title: document.getElementById('title').value,
            price: document.getElementById('price').value,
            desc: document.getElementById('desc').value
        })
    });
}
function stopBot() { fetch('/stop', {method: 'POST'}); }
setInterval(() => {
    fetch('/status').then(r => r.json()).then(d => {
        document.getElementById('status').innerText = "Status: " + d.status;
    });
}, 2000);
</script>
</body>
</html>
"""

def parse_cookies(cookie_str):
    cookies = []
    for item in cookie_str.split(';'):
        if '=' in item:
            k, v = item.strip().split('=', 1)
            cookies.append({'name': k, 'value': v, 'domain': '.facebook.com', 'path': '/'})
    return cookies

def run_automation(data):
    global bot_running, status_text
    cookie_lines = [c.strip() for c in data['cookies'].split('\n') if c.strip()]
    cities = [l.strip() for l in data['locations'].split('\n') if l.strip()]
    photo_files = [os.path.abspath(os.path.join('photos', f)) for f in os.listdir('photos') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    with sync_playwright() as p:
        for idx, c_line in enumerate(cookie_lines):
            if not bot_running: break
            status_text = f"[Account {idx+1}/{len(cookie_lines)}] Opening Browser..."
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            context.add_cookies(parse_cookies(c_line))

            for c_idx, city in enumerate(cities):
                if not bot_running: break
                status_text = f"[Acc {idx+1}] Opening Tab {c_idx+1} for {city}..."
                page = context.new_page()
                page.goto("https://www.facebook.com/marketplace/create/item", timeout=60000)
                time.sleep(random.uniform(4, 7))

                if photo_files:
                    page.set_input_files('input[type="file"]', photo_files[:5])
                    time.sleep(3)

                inputs = page.locator('input[type="text"]')
                if inputs.count() >= 2:
                    inputs.nth(0).fill(data['title'])
                    time.sleep(1)
                    inputs.nth(1).fill(data['price'])
                
                desc_box = page.locator('textarea').first
                if desc_box.count() > 0:
                    desc_box.fill(data['desc'])

                status_text = f"[Acc {idx+1}] Filled {city}! Ready to review/publish."
                time.sleep(random.uniform(3, 5))

            status_text = f"[Acc {idx+1}] Done! Waiting before closing..."
            time.sleep(10)
            browser.close()

    bot_running = False
    status_text = "Completed!"

@app.route('/')
def home(): return render_template_string(HTML_PAGE)

@app.route('/start', methods=['POST'])
def start():
    global bot_running
    if not bot_running:
        bot_running = True
        threading.Thread(target=run_automation, args=(request.json,), daemon=True).start()
    return jsonify(ok=True)

@app.route('/stop', methods=['POST'])
def stop():
    global bot_running, status_text
    bot_running = False
    status_text = "Stopped by user."
    return jsonify(ok=True)

@app.route('/status')
def status(): return jsonify(status=status_text)

if __name__ == '__main__':
    print("Dashboard open karein: http://127.0.0.1:5000")
    app.run(port=5000)