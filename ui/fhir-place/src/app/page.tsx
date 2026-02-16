import { Button } from "@/components/ui/button";
import Image from "next/image";
import Link from "next/link";

export default function Home() {
  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 font-[family-name:var(--font-roboto)]">
      <main className="flex flex-col gap-[32px] row-start-2 items-center">
        <div className="flex items-baseline">
          <Image
            src="/fhir-flame.png"
            alt="Next.js logo"
            width={90}
            height={20}
            priority
            className="w-auto h-12 md:h-20"
          />
          <h1 className="md:text-8xl text-5xl font-bold ml-1">
            FHIR<span className="md:text-4xl text-xl align-top">©</span> Place
          </h1>
        </div>
        <div className="flex flex-col sm:flex-row gap-4">
          <Link href="/login">
            <Button className="py-6 rounded-2xl">
              <p className="text-md md:text-xl">Sign In</p>
            </Button>
          </Link>
          <Link href="/register">
            <Button variant="outline" className="py-6 rounded-2xl">
              <p className="text-md md:text-xl">Register</p>
            </Button>
          </Link>
        </div>
      </main>
    </div>
  );
}
