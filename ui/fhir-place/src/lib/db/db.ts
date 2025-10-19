import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "@/lib/db/schema";
import path from "node:path";
import fs from "node:fs";

const dbPath = path.join(process.cwd(), "data", "database.sqlite");
const dbDir = path.dirname(dbPath);

if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

const sqlite = new Database(dbPath);
const db = drizzle(sqlite, { schema });

sqlite.pragma("foreign_keys = ON");

export { db };
export default db;
