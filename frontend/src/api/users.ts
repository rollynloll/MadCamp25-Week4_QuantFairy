import { buildApiUrl } from "./base";

export type EnsureUserPayload = {
  userId: string;
  email?: string | null;
  displayName?: string | null;
};

export async function ensureUserProfile(payload: EnsureUserPayload) {
  const body: Record<string, string> = {
    user_id: payload.userId,
  };
  if (payload.email) body.email = payload.email;
  if (payload.displayName) body.display_name = payload.displayName;

  const res = await fetch(buildApiUrl("/users/ensure"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to save user");
  }

  return res.json() as Promise<{ user: { id: string } }>;
}
