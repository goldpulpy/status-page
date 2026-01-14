import esbuild from "esbuild";

const isProd = process.env.ENVIRONMENT === "production";

await esbuild.build({
  entryPoints: ["src/app/frontend/assets/global.js"],
  bundle: true,
  format: "esm",
  platform: "browser",
  outfile: "src/app/frontend/static/main.min.js",
  minify: isProd,
  treeShaking: true,
  drop: isProd ? ["console", "debugger"] : [],
  logLevel: isProd ? "error" : "info",
});

console.log("JS build complete");
process.exit(0);
