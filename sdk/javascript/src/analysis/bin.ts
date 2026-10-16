#!/usr/bin/env node
// The command sbm-check of the npm package; the runner calls it in the sandbox (E208).
import { main } from "./cli.ts";

process.exitCode = main(process.argv.slice(2));
