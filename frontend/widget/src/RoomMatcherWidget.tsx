// frontend/widget/src/RoomMatcherWidget.tsx
import React, { useMemo, useState } from "react";

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
    const geo =
      lat !== undefined && lng !== undefined && !Number.isNaN(lat) && !Number.isNaN(lng)
        ? { lat, lng }
        : null;

    const profile: any = {
      city,
      budget_pkr: budget,
      role,
      anchor_location: anchor ? { name: anchor } : null,
      geo
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

  const severityPill = useMemo(
    () =>
      ({
        high: { bg: "#7f1d1d", text: "#fecaca", label: "High" },
        medium: { bg: "#78350f", text: "#fde68a", label: "Medium" },
        low: { bg: "#1f2937", text: "#fef3c7", label: "Low" }
      } as const),
    []
  );

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
            onChange={(e) => {
              const value = e.target.value;
              const parsed = Number(value);
              setLat(value === "" || Number.isNaN(parsed) ? undefined : parsed);
            }}
          />
          <input
            type="number"
            placeholder="Longitude"
            value={lng ?? ""}
            onChange={(e) => {
              const value = e.target.value;
              const parsed = Number(value);
              setLng(value === "" || Number.isNaN(parsed) ? undefined : parsed);
            }}
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
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <b>Profile {m.other_profile_id}</b>
                <span style={{ fontSize: "0.8rem", color: "#0f172a", fontWeight: 600 }}>
                  Score {m.score}
                </span>
              </div>
              <div style={{ fontSize: "0.8rem", color: "#555", marginTop: "0.25rem" }}>
                {m.reasons?.join(" • ")}
              </div>
              {m.conflicts?.length > 0 && (
                <div style={{ marginTop: "0.5rem", display: "grid", gap: "0.35rem" }}>
                  {m.conflicts.map((f: any, idx: number) => {
                    const sev = severityPill[(f.severity || "low").toLowerCase() as keyof typeof severityPill];
                    return (
                      <div
                        key={`${f.type}-${idx}`}
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.25rem",
                          borderLeft: `4px solid ${sev?.bg ?? "#1f2937"}`,
                          paddingLeft: "0.5rem"
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                          <span
                            style={{
                              background: sev?.bg ?? "#1f2937",
                              color: sev?.text ?? "#fff7ed",
                              borderRadius: "999px",
                              fontSize: "0.65rem",
                              padding: "0.15rem 0.5rem",
                              textTransform: "uppercase",
                              letterSpacing: "0.05em"
                            }}
                          >
                            {sev?.label ?? (f.severity || "Low")}
                          </span>
                          <strong style={{ fontSize: "0.75rem", color: "#7f1d1d" }}>
                            {f.type?.replace(/_/g, " ")}
                          </strong>
                        </div>
                        <span style={{ fontSize: "0.75rem", color: "#374151" }}>
                          {f.details || "Needs attention"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
              {m.tips?.length > 0 && (
                <div style={{ marginTop: "0.5rem", display: "grid", gap: "0.25rem" }}>
                  {m.tips.map((t: string, idx: number) => (
                    <div
                      key={idx}
                      style={{
                        fontSize: "0.75rem",
                        background: "#f8fafc",
                        borderRadius: "0.35rem",
                        padding: "0.35rem",
                        color: "#0f172a"
                      }}
                    >
                      💡 {t}
                    </div>
                  ))}
                </div>
              )}
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
