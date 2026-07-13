"use client";

const DRIVE_EMBED_URL =
  "https://drive.google.com/file/d/1q8orxigGT68C3G5raJB9LNs_U0RG8fCC/preview";

export default function WatchDemo() {
  const highlights = [
    { label: "The Insight", desc: "3 problem statements, one shared data backbone" },
    { label: "Data Pipeline", desc: "Berka → Indianized → 51 engineered features" },
    { label: "ML Models", desc: "3 XGBoost heads with TreeSHAP explainability" },
    { label: "Agentic Layer", desc: "4 autonomous agents on Strands + AWS Bedrock" },
  ];

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold gradient-text mb-1">Understand the Solution</h2>
        <p className="text-sm text-[var(--text-muted)]">
          A 3-minute walkthrough — from dataset to ML pipeline to the agentic platform
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Video player */}
        <div className="col-span-2 card p-0 overflow-hidden">
          <div className="relative w-full" style={{ paddingTop: "56.25%" }}>
            <iframe
              src={DRIVE_EMBED_URL}
              allow="autoplay; encrypted-media"
              allowFullScreen
              className="absolute top-0 left-0 w-full h-full"
              style={{ border: "none" }}
              title="FinPulse Demo Video"
            />
          </div>
        </div>

        {/* Side panel */}
        <div className="flex flex-col gap-4">
          <div className="card">
            <h3 className="font-semibold text-[var(--text)] mb-3">What you&apos;ll see</h3>
            <div className="space-y-3">
              {highlights.map((h, i) => (
                <div key={i} className="flex gap-3">
                  <div className="w-6 h-6 rounded-md bg-[var(--primary-blue)]/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-[var(--primary-blue)] text-xs font-bold">{i + 1}</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-[var(--text)]">{h.label}</p>
                    <p className="text-xs text-[var(--text-muted)]">{h.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              <span className="font-semibold text-[var(--text)]">FinPulse</span> unifies
              Prospect Assist, MSME Health Scoring, and Default Prediction on a single
              behavioral-intelligence engine — every prediction explainable, every action
              human-approved.
            </p>
            <a
              href="https://drive.google.com/file/d/1q8orxigGT68C3G5raJB9LNs_U0RG8fCC/view"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-3 text-xs text-[var(--primary-blue)] hover:underline"
            >
              Open in Google Drive →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
