"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/features/auth/auth-context";
import { PaymentDialog } from "@/features/payments/payment-dialog";
import { useBuy } from "@/features/payments/use-buy";
import { uz } from "@/messages/uz";
import { apiRequest } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { useApi } from "@/shared/api/use-api";
import { formatSom } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";
import { FormAlert } from "@/shared/ui/form-field";
import type { Product } from "./types";

const t = uz.catalog;

/**
 * Narx, "Sotib olish" va yuklab olish. Egalik kirgan foydalanuvchi uchun GET /v1/catalog/owned dan;
 * zaxira sifatida to'lov yaratishdagi `409 already_owned` ham hisobga olinadi.
 */
export function BuyBox({ product }: { product: Product }) {
  const { status } = useAuth();
  const buy = useBuy();
  const ownedList = useApi<{ product_ids: string[] }>(status === "authenticated" ? "/v1/catalog/owned" : null);
  const [ownedByError, setOwned] = useState(false);
  const owned = ownedByError || (ownedList.data?.product_ids.includes(product.id) ?? false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Ko'rishlar sonini oshirish: javob kutilmaydi, xato e'tiborsiz
    void fetch(`${process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "")}/v1/catalog/products/${encodeURIComponent(product.id)}/view`, {
      method: "POST",
      keepalive: true,
    }).catch(() => undefined);
  }, [product.id]);

  const download = async () => {
    setBusy(true);
    setError(null);
    try {
      const { url } = await apiRequest<{ url: string }>(`/v1/catalog/products/${encodeURIComponent(product.id)}/download`);
      setOwned(true);
      window.location.href = url;
    } catch (e) {
      if (e instanceof ApiError && e.code === "not_purchased") setOwned(false);
      setError(e instanceof ApiError && e.message ? e.message : uz.authForms.genericError);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 rounded-card border border-border bg-white p-5 shadow-soft sm:p-6">
      <p className="font-[var(--font-outfit)] text-3xl font-bold tabular-nums text-ink">{formatSom(product.price_som)}</p>
      {error ? <FormAlert>{error}</FormAlert> : null}
      {owned ? (
        <>
          <FormAlert tone="success">{t.owned}</FormAlert>
          <Button size="lg" onClick={() => void download()} disabled={busy}>{busy ? t.downloading : t.download}</Button>
        </>
      ) : (
        <>
          <Button size="lg" onClick={buy.start} disabled={!buy.ready || (status === "authenticated" && ownedList.loading)}>
            {status === "guest" ? t.loginToBuy : t.buy}
          </Button>
        </>
      )}
      <PaymentDialog
        open={buy.open}
        onClose={buy.close}
        kind="catalog"
        targetId={product.id}
        title={product.title}
        onError={(e) => {
          if (e.code !== "already_owned") return false;
          setOwned(true);
          return true;
        }}
      />
    </div>
  );
}
