const child_process = require('child_process');
const fs = require('fs');

const url = 'file:///D:/NIH_roorkee/FULL WORK FINAL_DIGITAL_NAYA_PANI/NAYA_PAANI/scratch/test_photoreal_twin.html';
const proc = child_process.spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', [
  '--headless',
  '--remote-debugging-port=9333',
  '--disable-gpu',
  '--allow-file-access-from-files',
  '--window-size=1280,820',
  url
]);

setTimeout(async () => {
  try {
    const res = await fetch('http://localhost:9333/json');
    const tabs = await res.json();
    const tab = tabs.find(t => t.url && t.url.includes('test_photoreal_twin.html'));
    if (!tab) {
      console.log('Tab not found, tabs:', tabs);
      proc.kill();
      process.exit(1);
    }
    console.log('Connecting to Edge:', tab.webSocketDebuggerUrl);

    const ws = new WebSocket(tab.webSocketDebuggerUrl);
    ws.onopen = () => {
      ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
      // Listen to console
      ws.send(JSON.stringify({ id: 2, method: 'Console.enable' }));

      // Wait 3.5 seconds for textures and Three.js scene to render
      setTimeout(() => {
        ws.send(JSON.stringify({ id: 3, method: 'Page.captureScreenshot' }));
      }, 3500);
    };

    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.method === 'Runtime.consoleAPICalled') {
        console.log('Console:', data.params.type, data.params.args.map(a => a.value).join(' '));
      }
      if (data.method === 'Runtime.exceptionThrown') {
        console.error('JS Exception:', data.params.exceptionDetails);
      }
      if (data.id === 3 && data.result && data.result.data) {
        fs.writeFileSync('D:/NIH_roorkee/FULL WORK FINAL_DIGITAL_NAYA_PANI/NAYA_PAANI/scratch/photoreal_screen.png', Buffer.from(data.result.data, 'base64'));
        console.log('Saved photoreal_screen.png!');
        proc.kill();
        process.exit(0);
      }
    };
  } catch (err) {
    console.error('Error:', err);
    proc.kill();
    process.exit(1);
  }
}, 2500);
