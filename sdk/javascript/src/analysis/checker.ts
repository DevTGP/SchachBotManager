// The rules a single file must follow (statische-analyse.md, E228).
//
// Every .js file is an ES module: Node runs one without import or export as CommonJS in sloppy
// mode, where this in a function is the global object. Imports name the SDK or a source file of
// the upload; there is no import() and import.meta only as import.meta.main. Forbidden globals
// may not appear as names, forbidden properties neither as property names nor as strings.
// Strings built at runtime pass this check; for them the flags of Node and the sandbox are the
// defense (E227).
import path from "node:path";

import type { AnyNode, Identifier, Program } from "acorn";

import {
  DYNAMIC_IMPORT,
  FORBIDDEN_NAME,
  FORBIDDEN_PROPERTY,
  IMPORT_META,
  IMPORT_NOT_ALLOWED,
  NOT_MODULE,
  type Finding,
} from "./report.ts";
import type { Rules } from "./rules.ts";
import { walk, type Visit } from "./walk.ts";

export class FileChecker {
  readonly #file: string;
  readonly #sources: ReadonlySet<string>;
  readonly #rules: Rules;
  readonly #findings: Finding[] = [];

  /** sources holds the paths of all source files of the upload, for relative imports. */
  constructor(file: string, sources: ReadonlySet<string>, rules: Rules) {
    this.#file = file;
    this.#sources = sources;
    this.#rules = rules;
  }

  check(program: Program): Finding[] {
    if (this.#file.endsWith(".js") && !program.body.some(isModuleDeclaration)) {
      this.#add(
        program,
        NOT_MODULE,
        "a .js file needs import or export, or Node runs it as CommonJS; or name it .mjs",
      );
    }
    for (const visit of walk(program)) {
      this.#visit(visit);
    }
    return this.#findings;
  }

  #visit({ node, parent, key }: Visit): void {
    switch (node.type) {
      case "ImportDeclaration":
      case "ExportNamedDeclaration":
      case "ExportAllDeclaration":
        if (node.source) {
          this.#import(node, String(node.source.value));
        }
        break;
      case "ImportExpression":
        this.#add(node, DYNAMIC_IMPORT, "import() is not allowed; use import declarations");
        break;
      case "MetaProperty":
        this.#metaProperty(node, parent);
        break;
      case "Identifier":
        this.#identifier(node, parent, key);
        break;
      case "Literal":
        if (typeof node.value === "string" && key !== "source") {
          this.#text(node, node.value);
        }
        break;
      case "TemplateElement":
        this.#text(node, node.value.cooked ?? node.value.raw);
        break;
    }
  }

  #import(node: AnyNode, specifier: string): void {
    if (this.#rules.modules.has(specifier)) {
      return;
    }
    if (specifier.startsWith("./") || specifier.startsWith("../")) {
      const target = path.posix.normalize(
        path.posix.join(path.posix.dirname(this.#file), specifier),
      );
      if (!this.#sources.has(target)) {
        this.#add(node, IMPORT_NOT_ALLOWED, `${specifier} is not a .js or .mjs file of the bot`);
      }
      return;
    }
    const allowed = [...this.#rules.modules].join(", ");
    this.#add(
      node,
      IMPORT_NOT_ALLOWED,
      `${specifier} may not be imported; only own files and ${allowed}`,
    );
  }

  #metaProperty(node: AnyNode & { type: "MetaProperty" }, parent: AnyNode | null): void {
    if (node.meta.name !== "import") {
      return;
    }
    const property =
      parent?.type === "MemberExpression" &&
      parent.object === node &&
      !parent.computed &&
      parent.property.type === "Identifier"
        ? parent.property.name
        : null;
    if (property === null || !this.#rules.importMeta.has(property)) {
      const allowed = [...this.#rules.importMeta].map((name) => `import.meta.${name}`).join(", ");
      this.#add(node, IMPORT_META, `import.meta may only be used as ${allowed}`);
    }
  }

  #identifier(node: Identifier, parent: AnyNode | null, key: string | null): void {
    if (isPropertyName(parent, key)) {
      if (this.#rules.forbiddenProperties.has(node.name) && !isConstructor(parent)) {
        this.#add(node, FORBIDDEN_PROPERTY, `the property ${node.name} is not allowed`);
      }
    } else if (isReference(parent, key) && this.#rules.forbiddenGlobals.has(node.name)) {
      this.#add(node, FORBIDDEN_NAME, `the name ${node.name} is not allowed`);
    }
  }

  #text(node: AnyNode, text: string): void {
    if (this.#rules.forbiddenProperties.has(text)) {
      this.#add(
        node,
        FORBIDDEN_PROPERTY,
        `the property ${text} is not allowed, also not as a string`,
      );
    }
  }

  #add(node: AnyNode, rule: string, message: string): void {
    this.#findings.push({ file: this.#file, line: node.loc?.start.line ?? null, rule, message });
  }
}

function isModuleDeclaration(node: AnyNode): boolean {
  return node.type.startsWith("Import") || node.type.startsWith("Export");
}

/** obj.name, { name: … }, class { name() {} } and class { name = … }, each not computed. */
function isPropertyName(parent: AnyNode | null, key: string | null): boolean {
  switch (parent?.type) {
    case "MemberExpression":
      return key === "property" && !parent.computed;
    case "Property":
    case "MethodDefinition":
    case "PropertyDefinition":
      return key === "key" && !parent.computed;
    default:
      return false;
  }
}

function isConstructor(parent: AnyNode | null): boolean {
  return parent?.type === "MethodDefinition" && parent.kind === "constructor";
}

/** False for labels, the parts of import.meta and new.target, and names of other modules. */
function isReference(parent: AnyNode | null, key: string | null): boolean {
  switch (parent?.type) {
    case "LabeledStatement":
    case "BreakStatement":
    case "ContinueStatement":
      return key !== "label";
    case "MetaProperty":
      return false;
    case "ImportSpecifier":
      return key !== "imported";
    case "ExportSpecifier":
      return key !== "exported";
    case "ExportAllDeclaration":
      return key !== "exported";
    default:
      return true;
  }
}
