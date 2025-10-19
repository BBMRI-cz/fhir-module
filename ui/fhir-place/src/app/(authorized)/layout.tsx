import { logout } from "@/actions/auth-management/logout";
import { getCurrentUser } from "@/lib/auth/auth-utils";
import { redirect } from "next/navigation";
import { PasswordChangeWrapper } from "@/components/auth/PasswordChangeWrapper";
import { getMode } from "@/actions/backend/get-mode";
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
    redirect("/login");
  }

  const { isMiabisMode } = await getMode();

  return (
    <PasswordChangeWrapper>
      <AuthorizedLayoutClient
        user={user}
        onLogout={handleLogout}
        isMiabisMode={isMiabisMode}
      >
        {children}
      </AuthorizedLayoutClient>
    </PasswordChangeWrapper>
  );
}
