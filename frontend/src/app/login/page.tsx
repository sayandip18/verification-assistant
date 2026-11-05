"use client";

import { FormEvent, useState } from "react";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("officer@bllro.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
    } catch {
      setError("Invalid email or password.");
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-4 rounded-lg border border-ink/10 bg-white p-6">
        <div>
          <h1 className="text-xl font-semibold">Officer sign in</h1>
          <p className="mt-1 text-sm text-ink/60">Use your BLLRO account. There is no self-registration.</p>
        </div>
        {error && <p className="rounded bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p>}
        <label className="block text-sm">
          Email
          <input
            type="email"
            required
            className="mt-1 w-full rounded border border-ink/20 px-3 py-2"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label className="block text-sm">
          Password
          <input
            type="password"
            required
            className="mt-1 w-full rounded border border-ink/20 px-3 py-2"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded bg-forest px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          Sign in
        </button>
      </form>
    </div>
  );
}
