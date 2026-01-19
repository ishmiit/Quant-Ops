"use client";
import { useState } from 'react';

export default function AlphaTerminalV10() {
  const [ticker, setTicker] = useState("");
  const [data, setData] = useState<any>(null);
  const [mode, setMode] = useState("SHORT");
  const [loading, setLoading] = useState(false);

  const startAudit = async () => {
    if (!ticker) return;
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/audit/${ticker}`);
      const result = await res.json();
      setData(result);
    } catch (err) { alert("API BRIDGE OFFLINE"); }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#020202] text-zinc-100 font-sans p-6 md:p-12">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* TOP BAR */}
        <div className="flex justify-between items-center bg-zinc-900/30 p-6 rounded-3xl border border-zinc-800">
          <h1 className="text-3xl font-black italic tracking-tighter">QUANT <span className="text-blue-600">OPS</span></h1>
          <div className="flex gap-3">
            <input className="bg-black border border-zinc-700 px-6 py-3 rounded-2xl w-64 uppercase font-black outline-none focus:border-blue-600 text-xl" 
                   placeholder="SYMBOL" value={ticker} onChange={e => setTicker(e.target.value)} onKeyDown={e => e.key === 'Enter' && startAudit()} />
            <button onClick={startAudit} className="bg-white text-black px-10 py-3 rounded-2xl font-black uppercase hover:bg-blue-600 hover:text-white transition-all">
              {loading ? "..." : "Execute"}
            </button>
          </div>
        </div>

        {data?.status === "success" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-700">
            
            {/* PRICE PANEL */}
            <div className="lg:col-span-2 bg-zinc-900 p-12 rounded-[3rem] text-white shadow-2xl flex flex-col justify-between">
              <div>
                <p className="text-[15px] font-white opacity-40 uppercase tracking-[0.4em] mb-4">Institutional Price LTP</p>
                <div className="flex justify-between items-end">
                    <h2 className="text-9xl font-black tracking-tighter italic leading-none">₹{data.price}</h2>
                    <div className="text-right pb-2">
                        <p className="text-[10px] font-white opacity-30 uppercase mb-1">Sector Industry</p>
                        <p className="text-2xl font-black text-blue-600 uppercase italic leading-none">{data.sector}</p>
                    </div>
                </div>
              </div>
              <div className="flex gap-4 mt-12">
                <Badge label={`VOL: ${data.volume}`} />
                <Badge label={`MCAP: ${data.mcap}`} />
                <Badge label={`F-SCORE: ${data.f_score}/9`} />
              </div>
            </div>

            {/* VALUATION PANEL */}
            <div className="bg-zinc-900 border border-zinc-800 p-10 rounded-[3rem] flex flex-col justify-between">
              <div className="space-y-8">
                <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">Valuation Matrix</p>
                <div><p className="text-xs text-zinc-400 font-bold uppercase mb-1">Stock P/E</p><p className="text-7xl font-black">{data.pe}</p></div>
                <div><p className="text-xs text-zinc-400 font-bold uppercase mb-1">Sector Avg P/E</p><p className="text-4xl font-black text-zinc-400 italic">{data.sec_pe}</p></div>
              </div>
              <div className={`mt-8 p-5 rounded-2xl text-center font-black text-xl uppercase italic ${data.pe < data.sec_pe ? 'bg-green-500 text-black' : 'bg-red-500 text-white'}`}>
                {data.pe < data.sec_pe ? '▲ Under-Valued' : '▼ Over-Valued'}
              </div>
            </div>

            {/* PIVOT ZONES */}
            <div className="lg:col-span-3 bg-zinc-950 border border-zinc-800 p-10 rounded-[3rem]">
              <div className="flex justify-between items-center mb-10">
                <p className="text-xs font-black text-blue-600 uppercase tracking-[0.5em]">Strategic Trade Zones</p>
                <div className="flex bg-black border border-zinc-800 p-1 rounded-xl">
                  <button onClick={() => setMode("SHORT")} className={`px-10 py-2 rounded-lg text-xs font-black ${mode==='SHORT' ? 'bg-blue-600':'text-zinc-600'}`}>DAILY</button>
                  <button onClick={() => setMode("LONG")} className={`px-10 py-2 rounded-lg text-xs font-black ${mode==='LONG' ? 'bg-blue-600':'text-zinc-600'}`}>MONTHLY</button>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <ZoneCard label="Resistance" val={mode==='SHORT' ? data.short_res : data.long_res} color="text-red-500" />
                <ZoneCard label="Pivot Point" val={mode==='SHORT' ? data.short_piv : data.long_piv} color="text-zinc-500" />
                <ZoneCard label="Support Floor" val={mode==='SHORT' ? data.short_sup : data.long_sup} color="text-green-500" />
              </div>
            </div>

            {/* VERDICT & NEWS */}
            <div className={`p-10 rounded-[3rem] border-4 flex flex-col justify-center items-center text-center ${data.verdict === 'PRIME_VALUE' ? 'border-green-500 bg-green-500/5' : 'border-red-500 bg-red-500/5'}`}>
              <p className="text-[10px] font-black uppercase text-zinc-600 mb-4 tracking-widest">Final Verdict</p>
              <h4 className="text-4xl font-black italic uppercase tracking-tighter mb-4">{data.verdict}</h4>
              <p className="text-xs font-bold text-zinc-250 px-6 leading-relaxed uppercase">{data.advice}</p>
            </div>

            

          </div>
        )}
      </div>
    </div>
  );
}

function Badge({label}: any) {
    return <span className="px-5 py-2 bg-zinc-600 rounded-full text-[10px] font-white uppercase tracking-tighter">{label}</span>
}

function ZoneCard({label, val, color}:any) {
  return (
    <div className="bg-black border border-zinc-900 p-10 rounded-[2rem]">
      <p className="text-[10px] font-black text-zinc-700 uppercase mb-4 tracking-widest">{label}</p>
      <p className={`text-6xl font-black ${color} tracking-tighter italic`}>₹{val}</p>
    </div>
  );
}