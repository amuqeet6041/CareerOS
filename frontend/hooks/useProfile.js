"use client";

import { useState, useCallback } from "react";
import {
  getProfile,
  updateProfile,
  getPreferences,
  updatePreferences,
} from "@/services/profileService";

/**
 * useProfile — manages profile + preferences data fetching and saving.
 *
 * Usage:
 *   const { profile, preferences, loading, error, saving, saved,
 *           loadProfile, saveProfile, loadPreferences, savePreferences } = useProfile();
 */
export function useProfile() {
  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saved, setSaved] = useState(false);

  // -------------------------------------------------------------------------
  // Profile
  // -------------------------------------------------------------------------

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProfile();
      setProfile(data);
    } catch (err) {
      setError(err.message || "Failed to load profile");
    } finally {
      setLoading(false);
    }
  }, []);

  const saveProfile = useCallback(async (data) => {
    setSaving(true);
    setSaveError(null);
    setSaved(false);
    try {
      const updated = await updateProfile(data);
      setProfile(updated);
      setSaved(true);
      // Reset the "saved" indicator after 3 seconds
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setSaveError(err.message || "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }, []);

  // -------------------------------------------------------------------------
  // Preferences
  // -------------------------------------------------------------------------

  const loadPreferences = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPreferences();
      setPreferences(data);
    } catch (err) {
      setError(err.message || "Failed to load preferences");
    } finally {
      setLoading(false);
    }
  }, []);

  const savePreferences = useCallback(async (data) => {
    setSaving(true);
    setSaveError(null);
    setSaved(false);
    try {
      const updated = await updatePreferences(data);
      setPreferences(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setSaveError(err.message || "Failed to save preferences");
    } finally {
      setSaving(false);
    }
  }, []);

  return {
    profile,
    preferences,
    loading,
    error,
    saving,
    saveError,
    saved,
    loadProfile,
    saveProfile,
    loadPreferences,
    savePreferences,
  };
}
