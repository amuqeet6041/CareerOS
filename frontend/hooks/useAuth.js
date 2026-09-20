"use client";

import { useState, useEffect, useCallback } from "react";
import { getToken, saveToken, clearToken, getStoredUser, saveUser, clearUser } from "@/lib/auth";
import { login as loginRequest, getMe } from "@/services/authService";

export function useAuth() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = getToken();
    const storedUser = getStoredUser();

    if (!storedToken) {
      setIsLoading(false);
      return;
    }

    setToken(storedToken);
    if (storedUser) setUser(storedUser);

    getMe()
      .then((me) => {
        setUser(me);
        saveUser(me);
      })
      .catch((err) => {
        // Only a 401 means the session is genuinely dead (expired/invalid token);
        // network errors leave the stored session intact for a retry.
        if (err.status === 401) {
          clearToken();
          clearUser();
          setToken(null);
          setUser(null);
        }
      })
      .finally(() => setIsLoading(false));
  }, []);

  const signIn = useCallback(async (credentials) => {
    const data = await loginRequest(credentials);
    saveToken(data.access_token);
    const me = await getMe();
    saveUser(me);
    setToken(data.access_token);
    setUser(me);
    return me;
  }, []);

  const signOut = useCallback(() => {
    clearToken();
    clearUser();
    setToken(null);
    setUser(null);
  }, []);

  return {
    token,
    user,
    isAuthenticated: Boolean(token),
    isLoading,
    signIn,
    signOut,
  };
}