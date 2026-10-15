import { chromium } from "playwright-core";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const slides = [
  { html: "slide-01-title.html", out: "01-title.png", w: 1080, h: 1350 },
  { html: "slide-02-kiwi.html", out: "02-kiwi.png", w: 1080, h: 1350 },
  { html: "slide-03-papaya.html", out: "03-papaya.png", w: 1080, h: 1350 },
  { html: "slide-04-pineapple.html", out: "04-pineapple.png", w: 1080, h: 1350 },
];

const browser = await chromium.launch({
  executablePath: "/usr/bin/google-chrome-stable",
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});

for (const slide of slides) {
  const page = await browser.newPage({
    viewport: { width: slide.w, height: slide.h },
    deviceScaleFactor: 1,
  });
  const filePath = path.join(__dirname, slide.html);
  await page.goto(`file://${filePath}`, { waitUntil: "networkidle" });
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
  await page.waitForTimeout(500);
  const outPath = path.join(__dirname, "export", slide.out);
  await page.screenshot({
    path: outPath,
    type: "png",
    clip: { x: 0, y: 0, width: slide.w, height: slide.h },
  });
  console.log("saved", outPath);
  await page.close();
}

await browser.close();
