import { seedUsers } from "@/lib/db/seed";
import { db } from "@/lib/db/db";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";

let initialized = false;

export async function initializeDatabase() {
  if (initialized) {
    console.log("Database already initialized, skipping...");
    return;
  }

  try {
    console.log("Running migrations...");
    migrate(db, { migrationsFolder: "drizzle" });
    console.log("Migrations completed");

    await seedUsers();

    initialized = true;
    console.log("Database initialization completed successfully!");
  } catch (error) {
    console.error("Failed to initialize database:", error);
    throw error;
  }
}

// CLI script mode - run if executed directly
if (require.main === module) {
  (async () => {
    try {
      await initializeDatabase();
      process.exit(0);
    } catch (error) {
      console.error("Failed to initialize database:", error);
      process.exit(1);
    }
  })();
}
