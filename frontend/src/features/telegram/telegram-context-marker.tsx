"use client";

import { useEffect } from "react";
import { markTelegramContext } from "@/shared/lib/download";

/** Sayt Telegram Mini App ichida ochilganini eslab qoladi (yuklash usuli shunga qarab tanlanadi). */
export function TelegramContextMarker() {
  useEffect(() => markTelegramContext(), []);
  return null;
}
