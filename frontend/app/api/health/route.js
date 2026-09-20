import { NextResponse } from "next/server";

// Simple frontend health check route.
// Useful for platform/uptime checks on the Next.js server itself.
export async function GET() {
  return NextResponse.json({ status: "ok", service: "frontend" });
}
