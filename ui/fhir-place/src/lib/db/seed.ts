import { createUser, getUserByUsername } from "@/lib/auth/auth";

export async function seedUsers() {
  try {
    try {
      await getUserByUsername("admin");
      console.log("Admin user already exists");
      return;
    } catch {}

    await createUser({
      username: "admin",
      password: "Admin123!", // NOSONAR
      firstName: "Admin",
      lastName: "User",
      email: "admin@example.com",
      mustChangePassword: true,
    }, true);

    console.log("Seed users created successfully");
  } catch (error) {
    console.error("Error seeding users:", error);
    throw error;
  }
}
