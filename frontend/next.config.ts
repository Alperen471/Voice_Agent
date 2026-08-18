import type { NextConfig } from "next";
import { existsSync, readFileSync } from "fs";
import { join } from "path";

/** Proje kökündeki tek .env dosyasından bir değeri okur (frontend kendi .env dosyasını tutmaz). */
function readRootEnvValue(key: string): string | undefined {
  const envPath = join(__dirname, "..", ".env");
  if (!existsSync(envPath)) return undefined;
  const line = readFileSync(envPath, "utf-8")
    .split("\n")
    .find((l) => l.trim().startsWith(`${key}=`));
  return line?.slice(line.indexOf("=") + 1).trim();
}

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: readRootEnvValue("NEXT_PUBLIC_API_URL") || "http://localhost:5000",
  },
};

export default nextConfig;
