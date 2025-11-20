export async function register() {
  // This function runs once when the Next.js server starts
  // It's the proper entrypoint for initialization code in Next.js
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { initializeDatabase } = await import("@/scripts/init-db");
    await initializeDatabase();
  }
}
