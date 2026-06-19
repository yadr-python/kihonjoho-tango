"use client";

import {
  createContext, useCallback, useContext, useEffect, useMemo, useRef, useState,
} from "react";

// 読み上げステップ: 文を読む / 無音で待つ
export type SpeechStep = { say?: string; pause?: number };

type Active = { id: string; mode: "once" | "repeat" } | null;

type SpeechState = {
  supported: boolean;
  voices: SpeechSynthesisVoice[];
  voiceURI: string;
  setVoiceURI: (v: string) => void;
  rate: number;
  setRate: (r: number) => void;
  active: Active;
  play: (id: string, steps: SpeechStep[], opts?: { repeat?: boolean }) => void;
  stop: () => void;
};

const Ctx = createContext<SpeechState | null>(null);

export function useSpeech(): SpeechState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useSpeech must be used inside SpeechProvider");
  return ctx;
}

const LS_RATE = "tts_rate";
const LS_VOICE = "tts_voice";

export function SpeechProvider({ children }: { children: React.ReactNode }) {
  const supported = typeof window !== "undefined" && "speechSynthesis" in window;

  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [voiceURI, setVoiceURIState] = useState("");
  const [rate, setRateState] = useState(1);
  const [active, setActive] = useState<Active>(null);

  const tokenRef = useRef(0);
  const pauseTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rateRef = useRef(rate);
  const voiceRef = useRef(voiceURI);
  const voicesRef = useRef(voices);
  useEffect(() => { rateRef.current = rate; }, [rate]);
  useEffect(() => { voiceRef.current = voiceURI; }, [voiceURI]);
  useEffect(() => { voicesRef.current = voices; }, [voices]);

  useEffect(() => {
    const r = Number(localStorage.getItem(LS_RATE));
    if (r) setRateState(r);
    const v = localStorage.getItem(LS_VOICE);
    if (v) setVoiceURIState(v);
  }, []);

  useEffect(() => {
    if (!supported) return;
    const load = () => {
      const all = window.speechSynthesis.getVoices();
      const ja = all.filter((v) => v.lang.toLowerCase().startsWith("ja"));
      const list = ja.length ? ja : all;
      // Google提供の音声を先頭に（Chromeの「Google 日本語」など）
      list.sort((a, b) => {
        const ag = /google/i.test(a.name) ? 0 : 1;
        const bg = /google/i.test(b.name) ? 0 : 1;
        return ag - bg;
      });
      setVoices(list);
      // ユーザー未選択、または前回の声が今の端末に無い場合はGoogle音声を自動採用
      const saved = localStorage.getItem(LS_VOICE) || "";
      const savedExists = saved && list.some((v) => v.voiceURI === saved);
      if (!savedExists) {
        const google = list.find((v) => /google/i.test(v.name));
        if (google) setVoiceURIState(google.voiceURI);
      }
    };
    load();
    window.speechSynthesis.onvoiceschanged = load;
    return () => { window.speechSynthesis.onvoiceschanged = null; };
  }, [supported]);

  const setRate = useCallback((r: number) => {
    setRateState(r);
    localStorage.setItem(LS_RATE, String(r));
  }, []);
  const setVoiceURI = useCallback((v: string) => {
    setVoiceURIState(v);
    localStorage.setItem(LS_VOICE, v);
  }, []);

  const stop = useCallback(() => {
    tokenRef.current += 1;
    if (pauseTimer.current) { clearTimeout(pauseTimer.current); pauseTimer.current = null; }
    if (supported) window.speechSynthesis.cancel();
    setActive(null);
  }, [supported]);

  const play = useCallback(
    (id: string, steps: SpeechStep[], opts?: { repeat?: boolean }) => {
      if (!supported) return;
      tokenRef.current += 1;
      window.speechSynthesis.cancel();
      const my = tokenRef.current;
      const repeat = !!opts?.repeat;
      setActive({ id, mode: repeat ? "repeat" : "once" });

      const speakOne = (text: string) =>
        new Promise<void>((resolve) => {
          const u = new SpeechSynthesisUtterance(text);
          u.lang = "ja-JP";
          u.rate = rateRef.current;
          const v = voicesRef.current.find((vv) => vv.voiceURI === voiceRef.current);
          if (v) u.voice = v;
          u.onend = () => resolve();
          u.onerror = () => resolve();
          window.speechSynthesis.speak(u);
        });

      const sleep = (ms: number) =>
        new Promise<void>((resolve) => { pauseTimer.current = setTimeout(resolve, ms); });

      const run = async () => {
        for (const step of steps) {
          if (my !== tokenRef.current) return;
          if (step.pause) await sleep(step.pause);
          else if (step.say) await speakOne(step.say);
          if (my !== tokenRef.current) return;
        }
        if (my !== tokenRef.current) return;
        if (repeat) run();
        else setActive(null);
      };
      run();
    },
    [supported]
  );

  useEffect(() => () => { if (supported) window.speechSynthesis.cancel(); }, [supported]);

  const value = useMemo<SpeechState>(
    () => ({ supported, voices, voiceURI, setVoiceURI, rate, setRate, active, play, stop }),
    [supported, voices, voiceURI, setVoiceURI, rate, setRate, active, play, stop]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function SpeechSettings() {
  const { supported, voices, voiceURI, setVoiceURI, rate, setRate } = useSpeech();
  if (!supported) {
    return (
      <p className="text-xs text-orange2">
        ⚠ このブラウザは音声読み上げに対応していません（Chrome / Edge 推奨）。
      </p>
    );
  }
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <label className="block">
        <span className="mb-1 block text-xs font-semibold text-neon">
          読み上げ速度: {rate.toFixed(2)}倍
        </span>
        <input type="range" min={0.5} max={2} step={0.05} value={rate}
          onChange={(e) => setRate(Number(e.target.value))}
          className="w-full accent-[#7b3ff2]" />
      </label>
      <label className="block">
        <span className="mb-1 block text-xs font-semibold text-neon">声の選択</span>
        <select value={voiceURI} onChange={(e) => setVoiceURI(e.target.value)}>
          <option value="">自動（Google音声を優先）</option>
          {voices.map((v) => (
            <option key={v.voiceURI} value={v.voiceURI}>
              {/google/i.test(v.name) ? "🌟 " : ""}{v.name}（{v.lang}）
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

export function PlayButtons({
  id, steps, size = "sm",
}: { id: string; steps: SpeechStep[]; size?: "sm" | "md" }) {
  const { active, play, stop, supported } = useSpeech();
  if (!supported) return null;
  const isOnce = active?.id === id && active.mode === "once";
  const isRepeat = active?.id === id && active.mode === "repeat";
  const pad = size === "md" ? "px-3 py-1.5 text-sm" : "px-2 py-1 text-xs";
  return (
    <div className="flex gap-1.5" onClick={(e) => e.stopPropagation()}>
      <button
        onClick={() => (isOnce ? stop() : play(id, steps))}
        title="1回再生"
        className={`whitespace-nowrap rounded-lg border ${pad} font-semibold transition
          ${isOnce ? "border-neon bg-[#0c2a30] text-neon"
            : "border-[#5f82ff80] bg-[#0c1230] text-[#9adfff] hover:border-neon"}`}>
        {isOnce ? "⏹" : "🔊"}
      </button>
      <button
        onClick={() => (isRepeat ? stop() : play(id, steps, { repeat: true }))}
        title="繰り返し再生"
        className={`whitespace-nowrap rounded-lg border ${pad} font-semibold transition
          ${isRepeat ? "border-violet2 bg-[#1a0c2e] text-[#d18bff]"
            : "border-[#5f82ff80] bg-[#0c1230] text-[#9adfff] hover:border-violet2"}`}>
        {isRepeat ? "⏹" : "🔁"}
      </button>
    </div>
  );
}
