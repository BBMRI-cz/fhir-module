import { seedUsers } from "@/lib/db/seed";
import { db } from "@/lib/db/db";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";

if (require.main === module) {
  (async () => {
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
  })();
}
