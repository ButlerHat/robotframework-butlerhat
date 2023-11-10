// Create a playwright server to expose wsendpoint.

const { chromium } = require('playwright');  // Or 'webkit' or 'firefox'.

(async () => {
  const wsPathArg = process.argv[2];

  const browserServer = await chromium.launchServer(
    {
      headless: false,
      port: 4445,
      wsPath: wsPathArg || 'ws'
    }
  );
  const wsEndpoint = browserServer.wsEndpoint();
  
  console.log(wsEndpoint);
})();