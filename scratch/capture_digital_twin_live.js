const proc = require('child_process').spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', [
  '--headless',
  '--remote-debugging-port=9222',
  '--disable-gpu',
  '--window-size=1360,980',
  'http://localhost:8501'
]);

setTimeout(async () => {
  try {
    const res = await fetch('http://localhost:9222/json');
    const tabs = await res.json();
    const pageTab = tabs.find(t => t.url && t.url.includes('8501'));
    if (!pageTab) {
      console.log('No tab found');
      proc.kill();
      process.exit(1);
    }
    console.log('Connecting to Streamlit:', pageTab.webSocketDebuggerUrl);

    const ws = new WebSocket(pageTab.webSocketDebuggerUrl);
    ws.onopen = () => {
      ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
      // Click "Continue as guest"
      setTimeout(() => {
        ws.send(JSON.stringify({
          id: 2,
          method: 'Runtime.evaluate',
          params: {
            expression: `
              const btns = Array.from(document.querySelectorAll('button'));
              const guestBtn = btns.find(b => b.innerText.includes('Continue as guest'));
              if (guestBtn) {
                guestBtn.click();
                console.log('Clicked continue as guest');
              } else {
                console.log('Button not found, btns:', btns.map(b => b.innerText));
              }
            `
          }
        }));
      }, 2000);

      // Wait 5 seconds for dashboard to load and then capture screenshot
      setTimeout(() => {
        ws.send(JSON.stringify({ id: 3, method: 'Page.captureScreenshot' }));
      }, 7000);
    };

    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.id === 3 && data.result && data.result.data) {
        require('fs').writeFileSync('D:/NIH_roorkee/FULL WORK FINAL_DIGITAL_NAYA_PANI/NAYA_PAANI/scratch/live_twin_dashboard.png', Buffer.from(data.result.data, 'base64'));
        console.log('Live twin dashboard screenshot saved!');
        proc.kill();
        process.exit(0);
      }
    };
  } catch (err) {
    console.error(err);
    proc.kill();
  }
}, 3000);
