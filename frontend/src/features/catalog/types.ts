import type { components } from "@/shared/api/schema";

export type Product = components["schemas"]["ProductOut"];
export type Category = components["schemas"]["CategoryOut"];
export type ProductPage = { items: Product[]; total: number; limit: number; offset: number };
