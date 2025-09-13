const puppeteer = require('puppeteer');
const path = require('path');

async function captureScreenshot() {
  let browser;
  try {
    console.log('Launching browser...');
    browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--single-process',
        '--disable-gpu'
      ]
    });
    
    console.log('Opening new page...');
    const page = await browser.newPage();
    
    // Set viewport size for desktop screenshot
    await page.setViewport({ width: 1920, height: 1080 });
    
    console.log('Navigating to admin panel...');
    await page.goto('http://localhost:3005', { 
      waitUntil: 'networkidle0',
      timeout: 30000 
    });
    
    // Wait for the interface to load completely
    console.log('Waiting for interface to load...');
    await page.waitForSelector('h1', { timeout: 10000 });
    
    // Take full page screenshot
    const screenshotPath = path.join(__dirname, 'admin-panel-screenshot.png');
    console.log(`Taking screenshot: ${screenshotPath}`);
    await page.screenshot({ 
      path: screenshotPath,
      fullPage: true,
      type: 'png'
    });
    
    console.log('Screenshot saved successfully!');
    return screenshotPath;
    
  } catch (error) {
    console.error('Error capturing screenshot:', error);
    throw error;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

captureScreenshot()
  .then(path => console.log(`Screenshot saved to: ${path}`))
  .catch(err => {
    console.error('Failed to capture screenshot:', err);
    process.exit(1);
  });