// Creates or updates one database user per service; runs with the root user on every deploy,
// so changed passwords take effect. Passwords come from the environment (deploy/.env).
const dbName = process.env.SBM_MONGO_DB || "sbm";
const appDb = db.getSiblingDB(dbName);

const users = [
  { user: "sbm_api", password: "MONGO_API_PASSWORD", roles: ["read"] },
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
