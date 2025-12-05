import { logout } from "@/actions/auth-management/logout";
import { getCurrentUser } from "@/lib/auth/auth-utils";
import { redirect } from "next/navigation";
import { PasswordChangeWrapper } from "@/components/auth/PasswordChangeWrapper";
import { getConfigurationInfo } from "@/actions/configuration/configuration-info";
import { AuthorizedLayoutClient } from "@/app/(authorized)/AuthorizedLayoutClient";

async function handleLogout() {
  "use server";
  await logout();
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = await getCurrentUser();

  if (!user) {
    // User is not found or inactive - redirect to force-logout route to clear session
    redirect("/api/auth/force-logout");
  }

  const { miabisOnFhir } = await getConfigurationInfo();

  return (
    <PasswordChangeWrapper>
      <AuthorizedLayoutClient
        user={user}
        onLogout={handleLogout}
        isMiabisMode={miabisOnFhir}
      >
        {children}
      </AuthorizedLayoutClient>
    </PasswordChangeWrapper>
  );
}
