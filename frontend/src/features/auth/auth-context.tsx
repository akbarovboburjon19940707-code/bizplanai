"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { components } from "@/shared/api/schema";
import { clearAuth, refreshAccessToken, signOut, subscribeAuth } from "@/shared/api/client";

type UserOut = components["schemas"]["UserOut"];
type AuthContextValue = {
  status: "loading" | "guest" | "authenticated";
  user: UserOut | null;
  /** Foydalanuvchi o'zi "Chiqish" ni bosgan (himoyalangan sahifa uni kirishga emas, bosh sahifaga yuboradi). */
  signedOutByUser: boolean;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");
  const [user, setUser] = useState<UserOut | null>(null);
  const [signedOutByUser, setSignedOutByUser] = useState(false);

  useEffect(() => {
    let mounted = true;
    const unsubscribe = subscribeAuth((snapshot) => {
      if (!mounted) return;
      setUser(snapshot.accessToken ? snapshot.user : null);
      setStatus(snapshot.accessToken ? "authenticated" : "guest");
      if (snapshot.accessToken) setSignedOutByUser(false);
    });

    void refreshAccessToken().then((token) => {
      if (!mounted) return;
      setUser(token?.user ?? null);
      setStatus(token ? "authenticated" : "guest");
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, []);

  const handleSignOut = useCallback(async () => {
    setSignedOutByUser(true);
    await signOut();
  }, []);

  const value = useMemo(
    () => ({ status, user, signedOutByUser, signOut: handleSignOut }),
    [status, user, signedOutByUser, handleSignOut],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

export function expireSession() {
  clearAuth();
}
