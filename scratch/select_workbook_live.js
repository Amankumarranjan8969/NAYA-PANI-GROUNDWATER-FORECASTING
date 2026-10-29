const proc = require('child_process').spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', [
  '--headless',
  '--remote-debugging-port=9222',
  '--disable-gpu',
  '--window-size=1400,1000',
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

      // Step 1: Click "Continue as guest" if on login page
      setTimeout(() => {
        ws.send(JSON.stringify({
          id: 2,
          method: 'Runtime.evaluate',
          params: {
            expression: `
              const guestBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Continue as guest'));
              if (guestBtn) guestBtn.click();
            `
          }
        }));
      }, 1500);

      // Step 2: Select the preset workbook dropdown
      setTimeout(() => {
        ws.send(JSON.stringify({
          id: 3,
          method: 'Runtime.evaluate',
          params: {
            expression: `
              const selectbox = document.querySelector('[data-testid="stSelectbox"]');
              if (selectbox) {
                const input = selectbox.querySelector('input');
                if (input) {
                  input.focus();
                  input.click();
                }
              }
            `
          }
        }));
      }, 3500);

      // Step 3: Capture screenshot after 6 seconds
      setTimeout(() => {
        ws.send(JSON.stringify({ id: 4, method: 'Page.captureScreenshot' }));
      }, 7000);
    };

    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.id === 4 && data.result && data.result.data) {
        require('fs').writeFileSync('D:/NIH_roorkee/FULL WORK FINAL_DIGITAL_NAYA_PANI/NAYA_PAANI/scratch/live_workbook_screen.png', Buffer.from(data.result.data, 'base64'));
        console.log('Live workbook screenshot saved!');
        proc.kill();
        process.exit(0);
      }
    };
  } catch (err) {
    console.error(err);
    proc.kill();
  }
}, 3000);
