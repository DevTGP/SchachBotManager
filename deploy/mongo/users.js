// Creates or updates one database user per service; runs with the root user on every deploy,
// so changed passwords and privileges take effect. Passwords come from the environment
// (deploy/.env).
const dbName = process.env.SBM_MONGO_DB || "sbm";
const appDb = db.getSiblingDB(dbName);

// The api reads everything but writes only what accounts, the admin pages, uploads and
// interactive games need (E85, E92, E115, E116); the uploaded files go to the GridFS bucket
// bot_files (E82). Deleting a bot removes it with its matches, their jobs and its report (E105).
// Disciplines are created and archived, never deleted (E100).
const writeAll = ["insert", "update", "remove"];
const apiWrites = {
  users: writeAll,
  sessions: writeAll,
  invites: writeAll,
  password_resets: writeAll,
  rate_limits: writeAll,
  audit_log: ["insert"],
  matches: ["insert", "remove"],
  jobs: ["insert", "remove"],
  bots: writeAll,
  verification_reports: ["remove"],
  "bot_files.files": ["insert", "remove"],
  "bot_files.chunks": ["insert", "remove"],
  settings: ["insert", "update"],
  disciplines: ["insert", "update"],
  // Coders make and revoke their API tokens; using one marks it used (E116).
  api_tokens: ["insert", "update"],
};
const roles = [
  {
    role: "sbm_api_writes",
    privileges: Object.entries(apiWrites).map(([collection, actions]) => ({
      resource: { db: dbName, collection },
      actions,
    })),
    roles: [],
  },
];

for (const { role, privileges, roles: inherited } of roles) {
  if (appDb.getRole(role)) {
    appDb.updateRole(role, { privileges, roles: inherited });
  } else {
    appDb.createRole({ role, privileges, roles: inherited });
  }
  print(`role ${role}: ${privileges.map((p) => p.resource.collection).join(", ")}`);
}

const users = [
  { user: "sbm_api", password: "MONGO_API_PASSWORD", roles: ["read", "sbm_api_writes"] },
  { user: "sbm_runner", password: "MONGO_RUNNER_PASSWORD", roles: ["readWrite"] },
  { user: "sbm_migrate", password: "MONGO_MIGRATE_PASSWORD", roles: ["readWrite", "dbAdmin"] },
];

for (const { user, password, roles } of users) {
  const pwd = process.env[password];
  if (!pwd) throw new Error(`${password} is not set`);
  const grants = roles.map((role) => ({ role, db: dbName }));
  if (appDb.getUser(user)) {
    appDb.updateUser(user, { pwd, roles: grants });
  } else {
    appDb.createUser({ user, pwd, roles: grants });
  }
  print(`user ${user}: ${roles.join(", ")} on ${dbName}`);
}
