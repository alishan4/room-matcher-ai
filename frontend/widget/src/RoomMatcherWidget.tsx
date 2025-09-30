// frontend/widget/src/RoomMatcherWidget.tsx
import React, { useState } from "react";

// 👇 Props match backend inputs
export interface RoomMatcherWidgetProps {
  apiBase?: string;
  apiKey?: string;
  defaultCity?: string;
  defaultBudget?: number;
  defaultRole?: "student" | "professional";
  defaultAnchor?: string;
  defaultGeo?: { lat: number; lng: number };
}

export default function RoomMatcherWidget({
  apiBase = "http://127.0.0.1:8082",
  apiKey,
  defaultCity = "Lahore",
  defaultBudget = 18000,
  defaultRole = "student",
  defaultAnchor = "",
  defaultGeo
}: RoomMatcherWidgetProps) {
  // ---------------- State ----------------
  const [city, setCity] = useState(defaultCity);
  const [budget, setBudget] = useState(defaultBudget);
  const [role, setRole] = useState(defaultRole);
  const [anchor, setAnchor] = useState(defaultAnchor);
  const [lat, setLat] = useState<number | undefined>(defaultGeo?.lat);
  const [lng, setLng] = useState<number | undefined>(defaultGeo?.lng);
  const [result, setResult] = useState<any>(null);

  // ---------------- API Call ----------------
  async function handleMatch() {
    const profile: any = {
      city,
      budget_pkr: budget,
      role,
      anchor_location: anchor ? { name: anchor } : null,
      geo: lat && lng ? { lat, lng } : null
    };

    const res = await fetch(`${apiBase}/match/top`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {})
      },
      body: JSON.stringify({ profile, k: 5, mode: "online" })
    });
    const data = await res.json();
    setResult(data);
  }

  // ---------------- UI ----------------
  return (
    <div
      style={{
        padding: "1rem",
        background: "#111",
        color: "#eee",
        borderRadius: "1rem",
        fontFamily: "sans-serif"
      }}
    >
      <h3 style={{ marginBottom: "0.5rem" }}>Room Matcher 🧭</h3>
      <p style={{ fontSize: "0.9rem", color: "#aaa" }}>
        Smarter roommate matching — explainable, fast, and user-friendly
      </p>

      {/* Inputs */}
      <div style={{ display: "grid", gap: "0.5rem", marginTop: "1rem" }}>
        <label>
          City
          <input value={city} onChange={(e) => setCity(e.target.value)} />
        </label>
        <label>
          Budget (PKR)
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
          />
        </label>
        <label>
          Role
          <select value={role} onChange={(e) => setRole(e.target.value as any)}>
            <option value="student">Student</option>
            <option value="professional">Professional</option>
          </select>
        </label>
        <label>
          Anchor Location
          <input
            value={anchor}
            onChange={(e) => setAnchor(e.target.value)}
            placeholder="e.g. FAST NUCES, HBL Tower"
          />
        </label>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <input
            type="number"
            placeholder="Latitude"
            value={lat ?? ""}
            onChange={(e) => setLat(parseFloat(e.target.value))}
          />
          <input
            type="number"
            placeholder="Longitude"
            value={lng ?? ""}
            onChange={(e) => setLng(parseFloat(e.target.value))}
          />
        </div>
        <button
          onClick={handleMatch}
          style={{
            padding: "0.5rem",
            borderRadius: "0.5rem",
            background: "#22c55e",
            color: "white",
            fontWeight: "bold"
          }}
        >
          Find Matches
        </button>
      </div>

      {/* Results */}
      {result && (
        <div style={{ marginTop: "1rem" }}>
          <h4>Top Matches</h4>
          {result.matches?.map((m: any) => (
            <div
              key={m.other_profile_id}
              style={{
                background: "white",
                color: "#111",
                borderRadius: "0.5rem",
                padding: "0.5rem",
                marginBottom: "0.5rem"
              }}
            >
              <b>Profile {m.other_profile_id}</b> — Score {m.score}
              <div style={{ fontSize: "0.8rem", color: "#555" }}>
                {m.reasons?.join(" • ")}
              </div>
              {m.conflicts?.length > 0 && (
                <div style={{ fontSize: "0.8rem", color: "red" }}>
                  ⚠ Conflicts:{" "}
                  {m.conflicts.map((f: any) => f.details || f.type).join(", ")}
                </div>
              )}
              {m.tips?.map((t: string, idx: number) => (
                <div key={idx} style={{ fontSize: "0.75rem" }}>
                  💡 {t}
                </div>
              ))}
            </div>
          ))}

          <h4 style={{ marginTop: "1rem" }}>Suggested Rooms</h4>
          {result.rooms?.map((r: any) => (
            <div
              key={r.listing_id}
              style={{
                background: "white",
                color: "#111",
                borderRadius: "0.5rem",
                padding: "0.5rem",
                marginBottom: "0.5rem"
              }}
            >
              <b>
                {r.city}, {r.area}
              </b>{" "}
              — PKR {r.monthly_rent_PKR}
              <div style={{ fontSize: "0.8rem", color: "#555" }}>
                {r.amenities?.join(", ")}
              </div>
              {r.distance_km && r.eta_minutes && (
                <div style={{ fontSize: "0.8rem", marginTop: "0.25rem" }}>
                  📍 {r.distance_km} km away (~{r.eta_minutes} min)
                </div>
              )}
              {r.rooms_available && (
                <div style={{ fontSize: "0.8rem", color: "#444" }}>
                  🛏️ {r.rooms_available} spaces left
                </div>
              )}
              <div style={{ fontSize: "0.75rem", color: "#666" }}>
                {r.why_match}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
