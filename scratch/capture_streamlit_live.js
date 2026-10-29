const proc = require('child_process').spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', [
  '--headless',
  '--remote-debugging-port=9222',
  '--disable-gpu',
  '--window-size=1280,960',
  'http://localhost:8501'
]);

setTimeout(async () => {
  try {
    const res = await fetch('http://localhost:9222/json');
    const tabs = await res.json();
    const pageTab = tabs.find(t => t.url && t.url.includes('8501'));
    if (!pageTab) {
      console.log('Tabs:', tabs.map(t => t.url));
      proc.kill();
      process.exit(1);
    }
    console.log('Connecting to Streamlit tab:', pageTab.webSocketDebuggerUrl);

    const ws = new WebSocket(pageTab.webSocketDebuggerUrl);
    ws.onopen = () => {
      ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
      // Give Streamlit 4 seconds to execute Python rerun and render Three.js
      setTimeout(() => {
        ws.send(JSON.stringify({ id: 2, method: 'Page.captureScreenshot' }));
      }, 4500);
    };

    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.id === 2 && data.result && data.result.data) {
        require('fs').writeFileSync('D:/NIH_roorkee/FULL WORK FINAL_DIGITAL_NAYA_PANI/NAYA_PAANI/scratch/live_streamlit.png', Buffer.from(data.result.data, 'base64'));
        console.log('Live Streamlit screenshot saved!');
        proc.kill();
        process.exit(0);
      }
    };
  } catch (err) {
    console.error(err);
    proc.kill();
  }
}, 3000);
