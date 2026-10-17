// Lints the plain JavaScript of templates/javascript with the recommended rules. ESLint only
// lints files below the folder of its config file, so this runs it with the template as base.
import js from "@eslint/js";
import { ESLint } from "eslint";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const template = path.resolve(root, "..", "..", "templates", "javascript");

const eslint = new ESLint({
    cwd: template,
    overrideConfigFile: true,
    overrideConfig: [
        js.configs.recommended,
        {
            files: ["**/*.js"],
            languageOptions: {
                globals: { process: "readonly", console: "readonly", TextDecoder: "readonly" },
            },
        },
    ],
});
const results = await eslint.lintFiles(["**/*.js"]);
const formatter = await eslint.loadFormatter("stylish");
const output = await formatter.format(results);
if (output) {
    console.log(output);
}
if (results.length === 0) {
    console.error(`no JavaScript files in ${template}`);
    process.exitCode = 1;
} else if (results.some((result) => result.errorCount > 0 || result.warningCount > 0)) {
    process.exitCode = 1;
}
