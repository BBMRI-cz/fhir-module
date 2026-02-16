import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { UserDetailsCard } from "./(components)/UserDetailsCard";
import { ProfileOverview } from "./(components)/ProfileOverview";
import { PasswordChangeCard } from "./(components)/PasswordChangeCard";
import { ThemeToggle } from "@/components/custom/ThemeToggle";
import { FontSizeToggle } from "@/components/custom/FontSizeToggle";

export default function Settings() {
  return (
    <main className="flex-1 p-6">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
            <p className="text-muted-foreground">
              Manage your account settings and preferences
            </p>
          </div>
        </div>
        <Tabs defaultValue="account" className="w-full">
          <TabsList className="w-full justify-start">
            <TabsTrigger value="account">Account</TabsTrigger>
            <TabsTrigger value="general">General</TabsTrigger>
          </TabsList>
          <TabsContent value="account" className="mt-6">
            <div className="space-y-6">
              <ProfileOverview />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
                <UserDetailsCard />
                <PasswordChangeCard />
              </div>
            </div>
          </TabsContent>
          <TabsContent value="general" className="mt-6">
            <div className="max-w-2xl space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Appearance</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ThemeToggle />
                  <FontSizeToggle />
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}
