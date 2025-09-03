import { seedUsers } from "../lib/seed";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";
import { db } from "../lib/db";

async function initializeDatabase() {
  try {
    console.log("Running migrations...");
    migrate(db, { migrationsFolder: "drizzle" });
    console.log("Migrations completed");

    await seedUsers();

    console.log("Database initialization completed successfully!");
  } catch (error) {
    console.error("Failed to initialize database:", error);
    process.exit(1);
  }
}

if (require.main === module) {
  initializeDatabase();
}

export { initializeDatabase };
