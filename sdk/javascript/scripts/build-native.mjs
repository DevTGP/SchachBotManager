// Builds the addon sbm.node into prebuilds/<platform>-<arch>/ (E221). Options:
//   --debug          build type Debug instead of Release
//   --build-dir DIR  CMake build directory (default build/ in this package)
// The environment variable CMAKE_GENERATOR picks the generator as for any CMake build; on Windows
// the addon needs MSVC, e.g. CMAKE_GENERATOR="Visual Studio 17 2022".
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const require = createRequire(import.meta.url);

const { values } = parseArgs({
    options: {
        debug: { type: "boolean", default: false },
        "build-dir": { type: "string", default: path.join(root, "build") },
    },
});
const config = values.debug ? "Debug" : "Release";
const buildDir = path.resolve(values["build-dir"]);
const outputDir = path.join(root, "prebuilds", `${process.platform}-${process.arch}`);

const headers = require("node-api-headers");
// include_dir is relative to the working directory.
const addonApi = require("node-addon-api");

function run(args) {
    console.log(`> cmake ${args.join(" ")}`);
    const result = spawnSync("cmake", args, { stdio: "inherit" });
    if (result.error) {
        throw result.error;
    }
    if (result.status !== 0) {
        process.exit(result.status ?? 1);
    }
}

const configure = [
    "-S",
    root,
    "-B",
    buildDir,
    `-DCMAKE_BUILD_TYPE=${config}`,
    `-DNODE_API_HEADERS_DIR=${headers.include_dir}`,
    `-DNODE_ADDON_API_DIR=${path.resolve(addonApi.include_dir)}`,
    `-DSBM_JS_OUTPUT_DIR=${outputDir}`,
];
if (process.platform === "win32") {
    configure.push(`-DNODE_API_DEF=${headers.def_paths.node_api_def}`);
}

run(configure);
run(["--build", buildDir, "--config", config, "--target", "sbm_node", "--parallel"]);
console.log(`sbm.node in ${outputDir}`);
