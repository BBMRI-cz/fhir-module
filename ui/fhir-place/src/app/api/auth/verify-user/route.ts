import { NextRequest, NextResponse } from "next/server";
import { userExistsById } from "@/lib/db/user-queries";

export async function POST(req: NextRequest) {
  try {
    const { userId } = await req.json();

    if (!userId || typeof userId !== "string") {
      return NextResponse.json({ exists: false }, { status: 400 });
    }

    const exists = await userExistsById(userId);
    return NextResponse.json({ exists });
  } catch {
    return NextResponse.json({ exists: false }, { status: 500 });
  }
}
