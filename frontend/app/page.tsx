"use client";
import { useEffect, useState } from "react";

export default function Home() {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Panggil API FastAPI kita
        // Panggil API FastAPI kita
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/matches/today`)
      .then((res) => res.json())
      .then((data) => {
        setMatches(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Gagal konek ke backend", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-10 text-center text-xl">⏳ Memuat data dari AI...</div>;

  return (
    <main className="min-h-screen bg-slate-900 text-white p-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-4xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
          ⚽ AI Football Analyst
        </h1>
        <p className="text-slate-400 mb-8">Prediksi & Value Bet berbasis AI untuk match hari ini.</p>

        {matches.length === 0 ? (
          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
            Belum ada jadwal pertandingan untuk hari ini.
          </div>
        ) : (
          <div className="grid gap-6">
            {matches.map((match) => (
              <div key={match.id} className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
                <div className="flex justify-between items-center mb-4 border-b border-slate-700 pb-4">
                  <span className="text-sm font-semibold text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-full">
                    {match.competition_slug}
                  </span>
                  <span className="text-sm text-slate-400">
                    {new Date(match.kickoff_at).toLocaleString("id-ID")} WIB
                  </span>
                </div>

                <div className="flex justify-between items-center mb-6">
                  <div className="text-2xl font-bold text-center w-5/12">{match.home}</div>
                  <div className="text-xl font-black text-slate-500 w-2/12 text-center">VS</div>
                  <div className="text-2xl font-bold text-center w-5/12">{match.away}</div>
                </div>

                {match.confidence ? (
                  <div className="bg-slate-900 rounded-lg p-4">
                    <div className="grid grid-cols-3 gap-4 text-center mb-4">
                      <div>
                        <div className="text-xs text-slate-400 mb-1">Home Win</div>
                        <div className="text-lg font-bold text-blue-400">{(match.home_win_prob * 100).toFixed(1)}%</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 mb-1">Draw</div>
                        <div className="text-lg font-bold text-yellow-400">{(match.draw_prob * 100).toFixed(1)}%</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 mb-1">Away Win</div>
                        <div className="text-lg font-bold text-red-400">{(match.away_win_prob * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                    <div className="text-center text-sm">
                      Prediksi Skor: <span className="font-bold text-emerald-400 text-lg">{match.predicted_score}</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-slate-500 italic py-4">AI belum menganalisa match ini.</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}