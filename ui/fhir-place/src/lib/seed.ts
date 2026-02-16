import { createUser, getUserByUsername } from "./auth";

export async function seedUsers() {
  try {
    try {
      await getUserByUsername("admin");
      console.log("Admin user already exists");
      return;
    } catch {}

    // TODO move the password for admin to env, remove the testing user for production
    await createUser({
      username: "admin",
      password: "Admin123!", // NOSONAR
      firstName: "Admin",
      lastName: "User",
      email: "admin@example.com",
    });

    await createUser({
      username: "testuser",
      password: "Test123!", // NOSONAR
      firstName: "Test",
      lastName: "User",
      email: "test@example.com",
    });

    console.log("Seed users created successfully");
  } catch (error) {
    console.error("Error seeding users:", error);
    throw error;
  }
}
