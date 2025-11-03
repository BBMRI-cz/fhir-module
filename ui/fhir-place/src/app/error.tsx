"use client";

import { Button } from "@/components/ui/button";
import { Activity, Home, RefreshCw } from "lucide-react";
import Link from "next/link";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-8">
      <div className="text-center space-y-6 max-w-2xl">
        <div className="flex justify-center mb-8">
          <Activity className="h-20 w-20 text-destructive animate-pulse" />
        </div>

        <h1 className="text-6xl font-bold text-destructive">Oops!</h1>

        <h2 className="text-3xl font-semibold tracking-tight">
          Something Went Wrong
        </h2>

        <p className="text-lg text-muted-foreground max-w-md mx-auto">
          We encountered an unexpected error. Please notify the development /
          support team.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
          <Button size="lg" className="gap-2" onClick={() => reset()}>
            <RefreshCw className="h-4 w-4" />
            Try Again
          </Button>
          <Link href="/">
            <Button size="lg" variant="outline" className="gap-2">
              <Home className="h-4 w-4" />
              Go Home
            </Button>
          </Link>
        </div>

        {process.env.NODE_ENV === "development" && (
          <details className="mt-8 text-left">
            <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">
              Error Details (Development Only)
            </summary>
            <pre className="mt-4 p-4 bg-muted rounded-md overflow-auto text-xs">
              {error.message}
              {error.stack && `\n\n${error.stack}`}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}
