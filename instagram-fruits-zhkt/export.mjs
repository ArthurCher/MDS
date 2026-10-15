import { chromium } from "playwright-core";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const slides = [
  ["slide-01-title.html", "01-title.png"],
  ["slide-02-kiwi.html", "02-kiwi.png"],
];

const browser = await chromium.launch({
  executablePath: "/usr/bin/google-chrome-stable",
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});

const page = await browser.newPage({
  viewport: { width: 1080, height: 1350 },
  deviceScaleFactor: 1,
});

for (const [html, out] of slides) {
  const filePath = path.join(__dirname, html);
  await page.goto(`file://${filePath}`, { waitUntil: "networkidle" });
  // wait for fonts
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
  await page.waitForTimeout(400);
  const outPath = path.join(__dirname, "export", out);
  await page.screenshot({ path: outPath, type: "png", clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  console.log("saved", outPath);
}

await browser.close();
