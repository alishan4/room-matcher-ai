import { useState } from "react";

export interface RoomMatcherWidgetProps {
  apiBase?: string;
  apiKey?: string;
  showRooms?: boolean;
}

export default function RoomMatcherWidget({
  apiBase = "http://127.0.0.1:8082",
  apiKey,
  showRooms = true,
}: RoomMatcherWidgetProps) {
  // form state
  const [city, setCity] = useState("Lahore");
  const [budget, setBudget] = useState(18000);
  const [sleep, setSleep] = useState("");
  const [cleanliness, setCleanliness] = useState("");
  const [noise, setNoise] = useState("");
  const [guests, setGuests] = useState("");
  const [smoking, setSmoking] = useState("");
  const [adText, setAdText] = useState("");

  // result state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matches, setMatches] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);

  async function callApi(path: string, body: any) {
    const res = await fetch(`${apiBase}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
    return await res.json();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMatches([]);
    setRooms([]);

    try {
      // profile object
      let profile: any = {
        city,
        budget_pkr: budget,
        sleep_schedule: sleep || null,
        cleanliness: cleanliness || null,
        noise_tolerance: noise || null,
        guests_freq: guests || null,
        smoking: smoking || null,
        raw_text: adText || null,
      };

      // optional parse (like streamlit)
      if (adText.trim()) {
        try {
          const parsed = await callApi("/profiles/parse", {
            text: adText,
            mode: "degraded",
          });
          const prof2 = parsed?.profile || {};
          for (const [k, v] of Object.entries(prof2)) {
            if (profile[k] == null && v) profile[k] = v;
          }
        } catch (err) {
          console.warn("Parse failed:", err);
        }
      }

      // call /match/top
      const resp = await callApi("/match/top", {
        profile,
        k: 10,
        mode: "degraded",
      });
      setMatches(resp?.matches || []);

      // call /rooms/suggest
      if (showRooms) {
        try {
          const r = await callApi("/rooms/suggest", {
            city,
            per_person_budget: budget,
            needed_amenities: [],
            mode: "degraded",
          });
          setRooms(r?.listings || []);
        } catch (err) {
          console.warn("Rooms suggest failed:", err);
        }
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // helpers for UI
  function scoreStripe(score: number) {
    if (score >= 70) return "border-l-4 border-green-500";
    if (score >= 50) return "border-l-4 border-amber-500";
    return "border-l-4 border-rose-500";
  }

  function rentStripe(fit: string) {
    if (fit === "good") return "border-l-4 border-green-500";
    if (fit === "mid") return "border-l-4 border-amber-500";
    return "border-l-4 border-rose-500";
  }

  return (
    <div className="max-w-3xl mx-auto bg-neutral-900 text-neutral-100 rounded-2xl p-6 shadow-xl space-y-6 font-sans">
      <header>
        <h2 className="text-2xl font-semibold">Room Matcher 🧭</h2>
        <p className="text-sm text-neutral-400">
          Smarter roommate matching — explainable, fast, and user-friendly
        </p>
      </header>

      {/* form */}
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm">City</label>
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="w-full rounded-xl bg-neutral-800 border border-neutral-700 px-3 py-2"
          >
            <option value="">—</option>
            <option value="Lahore">Lahore</option>
            <option value="Karachi">Karachi</option>
            <option value="Islamabad">Islamabad</option>
            <option value="Peshawar">Peshawar</option>
            <option value="Quetta">Quetta</option>
          </select>
        </div>
        <div>
          <label className="block text-sm">Budget (PKR)</label>
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            className="w-full rounded-xl bg-neutral-800 border border-neutral-700 px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm">Sleep Schedule</label>
          <select
            value={sleep}
            onChange={(e) => setSleep(e.target.value)}
            className="w-full rounded-xl bg-neutral-800 border border-neutral-700 px-3 py-2"
          >
            <option value="">—</option>
            <option value="early_bird">Early Bird</option>
            <option value="night_owl">Night Owl</option>
            <option value="flex">Flexible</option>
          </select>
        </div>
        <div>
          <label className="block text-sm">Cleanliness</label>
          <select
            value={cleanliness}
            onChange={(e) => setCleanliness(e.target.value)}
            className="w-full rounded-xl bg-neutral-800 border border-neutral-700 px-3 py-2"
          >
            <option value="">—</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        <div>
          <label className="block text-sm">Noise Tolerance</label>
          <select
            value={noise}
            onChange={(e) => setNoise(e.target.value)}
            className="w-full rounded-xl bg-neutral-800 border border-neutral-700 px-3 py-2"
          >
            <option value="">—</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        <div>
          <label className="block text-sm">Guests</label>
          <select
            value={guests}
            onChange={(e) => setGuests(e.target.value)}
            className="w-full rounded-xl bg-neutral-800 border border-neutral-700 px-3 py-2"
          >
            <option value="">—</option>
            <option value="rare">Rare</option>
            <option value="sometimes">Sometimes</option>
            <option value="often">Often</option>
            <option value="daily">Daily</option>
          </select>
        </div>
        <div>
          <label className="block text-sm">Smoking</label>
          <select
            value={smoking}
            onChange={(e) => setSmoking(e.target.value)}
            className="w-full rounded-xl bg-neutral-800 border border-neutral-700 px-3 py-2"
          >
            <option value="">—</option>
            <option value="no">No</option>
            <option value="yes">Yes</option>
          </select>
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm">Ad Text (optional)</label>
          <textarea
            value={adText}
            onChange={(e) => setAdText(e.target.value)}
            className="w-full rounded-xl bg-neutral-800 border border-neutral-700 px-3 py-2"
            rows={3}
            placeholder="Mixed Urdu/English ad..."
          />
        </div>
        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-500 transition px-4 py-3 font-medium text-white"
          >
            {loading ? "Finding matches…" : "Find Matches"}
          </button>
        </div>
      </form>

      {error && <div className="p-3 rounded-xl bg-red-900/30 border border-red-700">{error}</div>}

      {/* matches */}
      {matches.length > 0 && (
        <section className="space-y-3">
          <h3 className="text-lg font-medium">Top Matches</h3>
          {matches.slice(0, 5).map((m, i) => (
            <div key={i} className={`rounded-xl bg-white text-neutral-900 p-4 shadow ${scoreStripe(m.score)}`}>
              <div className="flex justify-between items-center">
                <span className="font-semibold">Profile {m.other_profile_id || "-"}</span>
                <span className="text-sm font-bold bg-neutral-100 px-2 py-0.5 rounded-full">{m.score}</span>
              </div>
              <p className="text-sm text-neutral-600 mt-1">
                {m.reasons?.slice(0, 3).join(" • ") || "Good overlap"}
              </p>
              {m.conflicts?.length > 0 && (
                <p className="text-sm text-red-600 mt-2">⚠ Conflicts: {m.conflicts.join(", ")}</p>
              )}
              {m.tips?.length > 0 && (
                <p className="text-sm text-amber-700 mt-2">💡 {m.tips.slice(0, 2).join(" • ")}</p>
              )}
            </div>
          ))}
        </section>
      )}

      {/* rooms */}
      {showRooms && rooms.length > 0 && (
        <section className="space-y-3">
          <h3 className="text-lg font-medium">Suggested Rooms</h3>
          {rooms.map((r, i) => (
            <div key={i} className={`rounded-xl bg-white text-neutral-900 p-4 shadow ${rentStripe(r.rent_fit || "mid")}`}>
              <div className="flex justify-between">
                <div>
                  <div className="font-semibold">{r.city}, {r.area}</div>
                  <div className="text-sm text-neutral-600">PKR {r.monthly_rent_PKR?.toLocaleString()}</div>
                </div>
                <span className="text-xs bg-neutral-100 px-2 py-0.5 rounded-full">Listing {r.id || "-"}</span>
              </div>
              <p className="text-sm text-neutral-600 mt-1">{(r.amenities || []).join(" • ")}</p>
              {r.why && <p className="text-sm text-indigo-600 mt-1">{r.why}</p>}
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
