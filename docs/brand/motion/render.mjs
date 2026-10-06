// Rend faso-resultats-motion.html en vidéo MP4 (H.264, 1920×1080), image par image :
// l'horloge de la page est avancée à la main (window.seek), donc le rendu est
// parfaitement fluide quelle que soit la vitesse de la machine.
//
// Prérequis : Node 18+, Playwright (avec Chromium) et ffmpeg.
//   npm i -D playwright && npx playwright install chromium
//   node render.mjs [entrée.html] [sortie.mp4] [images/s] [segments]
//
// `segments` (facultatif) monte des extraits de la timeline bout à bout, en
// secondes : "13.4-22.4,57.6-61.5" = la section 01 puis la signature. Sans lui,
// toute la vidéo est rendue. Les versions courtes par service sont listées dans
// le README.
import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const PLAYWRIGHT = process.env.PLAYWRIGHT_MODULE || "playwright";
const { chromium } = await import(PLAYWRIGHT);

const [entree = "faso-resultats-motion.html", sortie = "faso-resultats-motion.mp4", fpsArg = "30", segmentsArg] =
  process.argv.slice(2);
const fps = Number(fpsArg);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(pathToFileURL(resolve(entree)).href + "?render");
await page.evaluate(() => document.fonts.ready);
const duree = await page.evaluate(() => window.DUREE);

const segments = segmentsArg
  ? segmentsArg.split(",").map((s) => s.split("-").map(Number))
  : [[0, duree]];
const instants = segments.flatMap(([debut, fin]) =>
  Array.from({ length: Math.round((fin - debut) * fps) }, (_, i) => debut + i / fps));

const ffmpeg = spawn("ffmpeg", [
  "-loglevel", "error", "-y",
  "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
  "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
  "-movflags", "+faststart", sortie,
], { stdio: ["pipe", "inherit", "inherit"] });

for (const [i, t] of instants.entries()) {
  await page.evaluate((t) => window.seek(t), t);
  const image = await page.screenshot({ type: "png" });
  if (!ffmpeg.stdin.write(image)) await new Promise((ok) => ffmpeg.stdin.once("drain", ok));
  if (i % fps === 0) process.stdout.write(`\r${Math.round((i / instants.length) * 100)} %`);
}
ffmpeg.stdin.end();
await new Promise((ok, ko) => ffmpeg.on("close", (code) => (code === 0 ? ok() : ko(new Error(`ffmpeg ${code}`)))));
await browser.close();
console.log(`\r${sortie} : ${instants.length} images, ${(instants.length / fps).toFixed(1)} s à ${fps} i/s`);
