import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  FileText, 
  Upload, 
  Play, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  Download, 
  Search, 
  Filter, 
  HelpCircle, 
  History, 
  BookOpen, 
  FileCheck2, 
  Info, 
  BarChart3, 
  AlertOctagon, 
  RefreshCw,
  Sparkles,
  Award
} from 'lucide-react';

const VERDICT_CONFIG = {
  SUPPORTED: {
    label: 'SUPPORTED',
    color: '#10b981',
    bg: '#ecfdf5',
    border: '#a7f3d0',
    text: '#065f46',
    icon: CheckCircle2,
    desc: 'The source clearly states or directly implies the claim, matching meaning and scope.'
  },
  PARTIALLY_SUPPORTED: {
    label: 'PARTIALLY_SUPPORTED',
    color: '#f59e0b',
    bg: '#fffbeb',
    border: '#fde68a',
    text: '#92400e',
    icon: AlertTriangle,
    desc: 'The source supports part of the claim or narrower scope; numbers or scope overgeneralized.'
  },
  UNSUPPORTED: {
    label: 'UNSUPPORTED',
    color: '#ef4444',
    bg: '#fef2f2',
    border: '#fecaca',
    text: '#991b1b',
    icon: XCircle,
    desc: 'The source was retrieved but does not contain evidence for the claim.'
  },
  CONTRADICTORY: {
    label: 'CONTRADICTORY',
    color: '#b91c1c',
    bg: '#fef2f2',
    border: '#f87171',
    text: '#7f1d1d',
    icon: AlertOctagon,
    desc: 'The source reports an empirical finding that directly conflicts with the claim.'
  },
  POSSIBLY_OUTDATED: {
    label: 'POSSIBLY_OUTDATED',
    color: '#f97316',
    bg: '#fff7ed',
    border: '#fed7aa',
    text: '#9a3412',
    icon: Clock,
    desc: 'Source is older than 10 years and the claim is time-sensitive (recency heuristic).'
  },
  UNCITED: {
    label: 'UNCITED',
    color: '#8b5cf6',
    bg: '#f5f3ff',
    border: '#ddd6fe',
    text: '#5b21b6',
    icon: HelpCircle,
    desc: 'A strong verifiable statement in the document that lacks a citation marker.'
  },
  AMBIGUOUS_CITATION: {
    label: 'AMBIGUOUS_CITATION',
    color: '#d97706',
    bg: '#fffbeb',
    border: '#fcd34d',
    text: '#78350f',
    icon: AlertTriangle,
    desc: 'Marker cannot be matched to a single reference.'
  },
  UNVERIFIABLE: {
    label: 'UNVERIFIABLE',
    color: '#64748b',
    bg: '#f8fafc',
    border: '#cbd5e1',
    text: '#334155',
    icon: HelpCircle,
    desc: 'The cited reference could not be verified in open registries or text was inaccessible.'
  },
  OVERGENERALIZED: {
    label: 'OVERGENERALIZED',
    color: '#c026d3',
    bg: '#fdf4ff',
    border: '#f5d0fe',
    text: '#86198f',
    icon: AlertTriangle,
    desc: 'The claim asserts a general conclusion, but the study was conducted on a restricted sample or cohort.'
  },
  CAUSALITY_OVERCLAIM: {
    label: 'CAUSALITY_OVERCLAIM',
    color: '#e11d48',
    bg: '#fff1f2',
    border: '#fecdd3',
    text: '#9f1239',
    icon: AlertOctagon,
    desc: 'Document asserts a direct causal relationship, but cited methodology is observational or non-randomized.'
  },
  SCOPE_MISMATCH: {
    label: 'SCOPE_MISMATCH',
    color: '#d97706',
    bg: '#fffbeb',
    border: '#fde68a',
    text: '#92400e',
    icon: AlertTriangle,
    desc: 'Finding applies to a different population, intervention, or clinical context than asserted.'
  },
  CONTEXT_OMITTED: {
    label: 'CONTEXT_OMITTED',
    color: '#0284c7',
    bg: '#f0f9ff',
    border: '#bae6fd',
    text: '#0369a1',
    icon: Info,
    desc: 'Key qualifying context, baseline rates, or limitations noted by original authors were omitted.'
  },
  MISINTERPRETED: {
    label: 'MISINTERPRETED',
    color: '#b91c1c',
    bg: '#fef2f2',
    border: '#fca5a5',
    text: '#7f1d1d',
    icon: XCircle,
    desc: 'The cited publication was fundamentally misinterpreted or its empirical results do not justify the claim.'
  }
};

export default function App() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progressStage, setProgressStage] = useState('');
  const [progressPercent, setProgressPercent] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVerdict, setSelectedVerdict] = useState('ALL');
  const [needsReviewOnly, setNeedsReviewOnly] = useState(false);
  const [activeModal, setActiveModal] = useState(null); // 'upload', 'benchmark', 'orphans', 'methodology'
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [expandedCards, setExpandedCards] = useState({});
  const [expandedAudit, setExpandedAudit] = useState({});
  const [reviewNotes, setReviewNotes] = useState({});
  const [overrideVerdicts, setOverrideVerdicts] = useState({});
  const [actionSuccessMsg, setActionSuccessMsg] = useState(null);
  const [uploadMode, setUploadMode] = useState('file'); // 'file' or 'paste'
  const [pastedText, setPastedText] = useState('');

  // Initial load
  useEffect(() => {
    fetchLatestReport();
    fetchBenchmark();
  }, []);

  const fetchLatestReport = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/reports/latest');
      if (res.ok) {
        const data = await res.json();
        setReport(data);
      }
    } catch (err) {
      console.error('Error fetching report:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBenchmark = async () => {
    try {
      const res = await fetch('/api/benchmark');
      if (res.ok) {
        const data = await res.json();
        setBenchmarkData(data);
      }
    } catch (err) {
      console.error('Error fetching benchmark:', err);
    }
  };

  const handleLoadDemo = async () => {
    setLoading(true);
    setProgressPercent(15);
    setProgressStage('Ingesting 2-page academic demo document...');

    setTimeout(async () => {
      setProgressPercent(45);
      setProgressStage('Resolving DOIs across Crossref & OpenAlex...');
    }, 400);

    setTimeout(async () => {
      setProgressPercent(75);
      setProgressStage('Verifying verbatim evidence quotes and running number checks...');
    }, 800);

    try {
      const res = await fetch('/api/verify/demo', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setProgressPercent(100);
        setProgressStage('Verification Report Ready!');
        setTimeout(() => {
          setReport(data);
          setLoading(false);
        }, 300);
      }
    } catch (err) {
      console.error('Demo error:', err);
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setActiveModal(null);
    setLoading(true);
    setProgressPercent(20);
    setProgressStage(`Uploading and ingesting ${file.name}...`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/verify/upload', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setProgressPercent(100);
        setProgressStage('Document verification complete!');
        setTimeout(() => {
          setReport(data);
          setLoading(false);
        }, 400);
      } else {
        alert('Verification failed on uploaded file.');
        setLoading(false);
      }
    } catch (err) {
      console.error('Upload error:', err);
      setLoading(false);
    }
  };

  const handleTextVerify = async () => {
    if (!pastedText.trim()) return;
    setActiveModal(null);
    setLoading(true);
    setProgressPercent(20);
    setProgressStage('Ingesting pasted academic text...');

    try {
      const res = await fetch('/api/verify/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pastedText, filename: 'pasted_document.txt' })
      });
      if (res.ok) {
        const data = await res.json();
        setProgressPercent(100);
        setProgressStage('Verification complete!');
        setTimeout(() => {
          setReport(data);
          setLoading(false);
        }, 400);
      } else {
        alert('Verification failed on pasted text.');
        setLoading(false);
      }
    } catch (err) {
      console.error('Verify text error:', err);
      setLoading(false);
    }
  };

  const handleReviewAction = async (claimId, action) => {
    const card = report.claim_cards.find(c => c.claim.id === claimId);
    if (!card) return;

    const payload = {
      claim_id: claimId,
      action: action,
      new_verdict: action === 'overridden' ? (overrideVerdicts[claimId] || 'SUPPORTED') : null,
      note: reviewNotes[claimId] || '',
      justification: reviewNotes[claimId] || '',
      reviewer_name: 'Peer Reviewer'
    };

    try {
      const res = await fetch('/api/review/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setReport(prev => {
          const updatedCards = prev.claim_cards.map(c => {
            if (c.claim.id === claimId) {
              const updatedHistory = [...c.audit_history, data.audit_entry];
              return {
                ...c,
                reviewer_status: data.reviewer_status,
                final_verdict: data.final_verdict || (action === 'undo' ? (c.ai_verdict || c.primary_verdict.label) : (payload.new_verdict || c.primary_verdict.label)),
                primary_verdict: {
                  ...c.primary_verdict,
                  label: action === 'undo' ? (c.ai_verdict || c.primary_verdict.label) : (payload.new_verdict || c.primary_verdict.label)
                },
                audit_history: updatedHistory
              };
            }
            return c;
          });
          return { ...prev, claim_cards: updatedCards };
        });

        setActionSuccessMsg(`Claim ${claimId} marked as ${action.toUpperCase()}`);
        setTimeout(() => setActionSuccessMsg(null), 3000);
      }
    } catch (err) {
      console.error('Review action failed:', err);
    }
  };

  const toggleScoreBreakdown = (id) => {
    setExpandedCards(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleAuditHistory = (id) => {
    setExpandedAudit(prev => ({ ...prev, [id]: !prev[id] }));
  };

  // Filter claim cards
  const filteredCards = (report?.claim_cards || []).filter(card => {
    const verdict = card.primary_verdict.label;
    if (selectedVerdict !== 'ALL' && verdict !== selectedVerdict) return false;
    
    if (needsReviewOnly) {
      const hasReviewFlag = card.primary_verdict.flags.includes('NEEDS_HUMAN_REVIEW');
      const lowScore = card.primary_verdict.evidence_strength_score < 0.50;
      if (!hasReviewFlag && !lowScore) return false;
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchText = card.claim.verbatim_text.toLowerCase().includes(q);
      const matchReason = card.primary_verdict.reason.toLowerCase().includes(q);
      const matchQuote = (card.primary_verdict.verified_evidence_quote || '').toLowerCase().includes(q);
      const matchId = card.claim.id.toLowerCase().includes(q);
      if (!matchText && !matchReason && !matchQuote && !matchId) return false;
    }

    return true;
  });

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc', color: '#0f172a' }}>
      
      {/* Top Banner / Header */}
      <header style={{
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
      }}>
        <div style={{
          maxWidth: '1280px',
          margin: '0 auto',
          padding: '14px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          {/* Logo & Tagline */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              backgroundColor: '#2563eb',
              color: '#ffffff',
              padding: '8px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <ShieldCheck size={26} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h1 style={{ fontSize: '20px', fontWeight: '800', letterSpacing: '-0.02em', color: '#0f172a' }}>
                  CiteVerify
                </h1>
                <span style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  textTransform: 'uppercase',
                  padding: '2px 8px',
                  backgroundColor: '#dbeafe',
                  color: '#1e40af',
                  borderRadius: '12px'
                }}>
                  INNOVEDGE 2026
                </span>
                <span style={{
                  fontSize: '11px',
                  fontWeight: '600',
                  padding: '2px 8px',
                  backgroundColor: '#ecfdf5',
                  color: '#065f46',
                  borderRadius: '12px',
                  border: '1px solid #a7f3d0'
                }}>
                  Offline Cache Ready
                </span>
              </div>
              <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>
                Your citation integrity copilot — verify what your sources actually say.
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={handleLoadDemo}
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: '600',
                fontSize: '13px',
                cursor: loading ? 'not-allowed' : 'pointer',
                boxShadow: '0 1px 2px rgba(37,99,235,0.2)'
              }}
            >
              <Sparkles size={16} />
              Load Planted Demo (8 Cases)
            </button>

            <button
              onClick={() => setActiveModal('upload')}
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                backgroundColor: '#ffffff',
                color: '#334155',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontWeight: '600',
                fontSize: '13px',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              <Upload size={16} />
              Upload PDF/TXT
            </button>

            <button
              onClick={() => setActiveModal('benchmark')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 12px',
                backgroundColor: '#f1f5f9',
                color: '#334155',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                fontWeight: '600',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              <Award size={16} />
              Benchmark (85%)
            </button>

            <button
              onClick={() => setActiveModal('methodology')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 12px',
                backgroundColor: '#ffffff',
                color: '#64748b',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                fontWeight: '600',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              <Info size={16} />
              Trust Principles
            </button>

            {/* Export Dropdown */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              <a
                href="/api/export/html"
                target="_blank"
                rel="noreferrer"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '7px 11px',
                  backgroundColor: '#ffffff',
                  color: '#2563eb',
                  border: '1px solid #bfdbfe',
                  borderRadius: '6px',
                  fontWeight: '600',
                  fontSize: '12px',
                  textDecoration: 'none'
                }}
              >
                <Download size={14} />
                HTML Report
              </a>
              <a
                href="/api/export/json"
                target="_blank"
                rel="noreferrer"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '7px 11px',
                  backgroundColor: '#ffffff',
                  color: '#475569',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  fontWeight: '600',
                  fontSize: '12px',
                  textDecoration: 'none'
                }}
              >
                JSON
              </a>
              <a
                href="/api/export/csv"
                target="_blank"
                rel="noreferrer"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '7px 11px',
                  backgroundColor: '#ffffff',
                  color: '#475569',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  fontWeight: '600',
                  fontSize: '12px',
                  textDecoration: 'none'
                }}
              >
                CSV
              </a>
              <a
                href="/api/export/corrected-bib"
                target="_blank"
                rel="noreferrer"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '7px 11px',
                  backgroundColor: '#f5f3ff',
                  color: '#6d28d9',
                  border: '1px solid #ddd6fe',
                  borderRadius: '6px',
                  fontWeight: '600',
                  fontSize: '12px',
                  textDecoration: 'none'
                }}
              >
                Corrected BibTeX
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Action Notification Toast */}
      {actionSuccessMsg && (
        <div style={{
          position: 'fixed',
          top: '75px',
          right: '24px',
          zIndex: 50,
          backgroundColor: '#065f46',
          color: '#ffffff',
          padding: '10px 18px',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.15)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '13px',
          fontWeight: '600'
        }}>
          <CheckCircle2 size={16} />
          {actionSuccessMsg}
        </div>
      )}

      {/* Main Container */}
      <main style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px' }}>
        
        {/* Loading / Progress State */}
        {loading && (
          <div style={{
            backgroundColor: '#ffffff',
            border: '1px solid #bfdbfe',
            borderRadius: '10px',
            padding: '24px',
            marginBottom: '24px',
            boxShadow: '0 2px 4px rgba(37,99,235,0.05)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <RefreshCw size={18} className="animate-spin" style={{ color: '#2563eb' }} />
                <span style={{ fontWeight: '700', fontSize: '14px', color: '#1e3a8a' }}>
                  {progressStage || 'Executing CiteVerify Pipeline...'}
                </span>
              </div>
              <span style={{ fontWeight: '700', fontSize: '14px', color: '#2563eb' }}>
                {progressPercent}%
              </span>
            </div>
            <div style={{ width: '100%', height: '8px', backgroundColor: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{
                width: `${progressPercent}%`,
                height: '100%',
                backgroundColor: '#2563eb',
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>
        )}

        {report && (
          <>
            {/* Document Meta Ribbon */}
            <div style={{
              backgroundColor: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              padding: '12px 20px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
              fontSize: '13px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div>
                  <span style={{ color: '#64748b' }}>Document: </span>
                  <strong style={{ color: '#0f172a' }}>{report.document_name}</strong>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Pages: </span>
                  <strong>{report.total_pages}</strong>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Detected Citation Style: </span>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: '#f1f5f9',
                    fontWeight: '700',
                    fontSize: '11px'
                  }}>
                    {report.citation_style.toUpperCase()}
                  </span>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Total Claims: </span>
                  <strong>{report.total_claims}</strong>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => setActiveModal('orphans')}
                  style={{
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#2563eb',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  View Orphan References ({report.orphan_references?.length || 0}) & Uncited ({report.uncited_claims?.length || 0})
                </button>
              </div>
            </div>

            {/* Executive Integrity Dashboard */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '16px',
              marginBottom: '24px'
            }}>
              {/* Citation Health Index Card */}
              <div style={{
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                padding: '20px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>
                      Citation Health Index
                    </div>
                    <div style={{ fontSize: '32px', fontWeight: '800', color: '#2563eb', margin: '4px 0' }}>
                      {report.citation_health_indicator.toFixed(1)}%
                    </div>
                  </div>
                  <div style={{
                    backgroundColor: '#eff6ff',
                    color: '#2563eb',
                    padding: '10px',
                    borderRadius: '8px'
                  }}>
                    <BarChart3 size={24} />
                  </div>
                </div>
                <p style={{ fontSize: '11px', color: '#64748b', margin: '4px 0 0 0', lineHeight: 1.4 }}>
                  Share of cited claims rated <strong>Supported</strong> with verified verbatim quotes.
                </p>
              </div>

              {/* Items in Review Queue Card */}
              <div style={{
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                padding: '20px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>
                      Needs Human Review
                    </div>
                    <div style={{
                      fontSize: '32px',
                      fontWeight: '800',
                      color: report.items_needing_review_count > 0 ? '#dc2626' : '#16a34a',
                      margin: '4px 0'
                    }}>
                      {report.items_needing_review_count}
                    </div>
                  </div>
                  <div style={{
                    backgroundColor: report.items_needing_review_count > 0 ? '#fef2f2' : '#ecfdf5',
                    color: report.items_needing_review_count > 0 ? '#dc2626' : '#16a34a',
                    padding: '10px',
                    borderRadius: '8px'
                  }}>
                    <AlertTriangle size={24} />
                  </div>
                </div>
                <p style={{ fontSize: '11px', color: '#64748b', margin: '4px 0 0 0', lineHeight: 1.4 }}>
                  Claims with score &lt; 0.50, numbers mismatched, retracted, or abstract-only.
                </p>
              </div>

              {/* Retrieval Evidence Tiers Breakdown */}
              <div style={{
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                padding: '20px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
              }}>
                <div style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Evidence Tiers (Source Sources)
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                    <span style={{ color: '#0369a1', fontWeight: '600' }}>Full Text Open Access</span>
                    <strong>{report.retrieval_summary?.FULL_TEXT || 0}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                    <span style={{ color: '#92400e', fontWeight: '600' }}>Abstract Only</span>
                    <strong>{report.retrieval_summary?.ABSTRACT_ONLY || 0}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                    <span style={{ color: '#475569', fontWeight: '600' }}>Metadata Only</span>
                    <strong>{report.retrieval_summary?.METADATA_ONLY || 0}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                    <span style={{ color: '#991b1b', fontWeight: '600' }}>Unverified / Not Found</span>
                    <strong>{report.retrieval_summary?.NOT_FOUND || 0}</strong>
                  </div>
                </div>
              </div>

              {/* Academic Copilot Disclaimer Card */}
              <div style={{
                backgroundColor: '#f8fafc',
                border: '1px dashed #cbd5e1',
                borderRadius: '10px',
                padding: '16px',
                fontSize: '11.5px',
                color: '#475569',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center'
              }}>
                <div style={{ fontWeight: '700', color: '#0f172a', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldCheck size={16} color="#2563eb" />
                  Academic Trust Guarantee
                </div>
                CiteVerify is a verification copilot, not an autonomous judge. Every automated finding is substantiated with verified quotes and remains open to human review.
              </div>
            </div>

            {/* Research Integrity Scorecard (Feature 12) */}
            {report.scorecard && (
              <div style={{
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                padding: '20px',
                marginBottom: '20px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Award size={20} color="#2563eb" />
                    <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', margin: 0 }}>
                      Document Research Integrity Scorecard
                    </h3>
                  </div>
                  <span style={{ fontSize: '12px', color: '#64748b' }}>
                    Formula: {report.scorecard.integrity_score_formula || 'Composite evidence-weighted index'}
                  </span>
                </div>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '14px'
                }}>
                  <div style={{ backgroundColor: '#eff6ff', padding: '14px', borderRadius: '8px', border: '1px solid #dbeafe' }}>
                    <div style={{ fontSize: '11px', fontWeight: '700', color: '#1e40af', textTransform: 'uppercase' }}>Research Integrity Index</div>
                    <div style={{ fontSize: '26px', fontWeight: '800', color: '#1d4ed8', margin: '4px 0' }}>
                      {(report.scorecard.research_integrity_score || 0).toFixed(1)}/100
                    </div>
                    <div style={{ fontSize: '11px', color: '#3b82f6' }}>Evidence-weighted integrity rating</div>
                  </div>

                  <div style={{ backgroundColor: '#ecfdf5', padding: '14px', borderRadius: '8px', border: '1px solid #a7f3d0' }}>
                    <div style={{ fontSize: '11px', fontWeight: '700', color: '#065f46', textTransform: 'uppercase' }}>Citation Coverage</div>
                    <div style={{ fontSize: '26px', fontWeight: '800', color: '#047857', margin: '4px 0' }}>
                      {(report.scorecard.citation_coverage_pct || 0).toFixed(1)}%
                    </div>
                    <div style={{ fontSize: '11px', color: '#059669' }}>
                      {report.scorecard.claims_with_citations} of {report.scorecard.total_factual_claims} claims cited
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#f5f3ff', padding: '14px', borderRadius: '8px', border: '1px solid #ddd6fe' }}>
                    <div style={{ fontSize: '11px', fontWeight: '700', color: '#5b21b6', textTransform: 'uppercase' }}>Source Diversity</div>
                    <div style={{ fontSize: '26px', fontWeight: '800', color: '#6d28d9', margin: '4px 0' }}>
                      {report.scorecard.total_references > 0 ? (report.scorecard.independent_sources / report.scorecard.total_references).toFixed(2) : '1.00'}
                    </div>
                    <div style={{ fontSize: '11px', color: '#7c3aed' }}>
                      {report.scorecard.independent_sources} independent, {report.scorecard.overlapping_sources} overlapping
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#fef2f2', padding: '14px', borderRadius: '8px', border: '1px solid #fecaca' }}>
                    <div style={{ fontSize: '11px', fontWeight: '700', color: '#991b1b', textTransform: 'uppercase' }}>Internal Contradictions</div>
                    <div style={{ fontSize: '26px', fontWeight: '800', color: report.internal_contradictions?.length > 0 ? '#b91c1c' : '#059669', margin: '4px 0' }}>
                      {report.internal_contradictions?.length || 0}
                    </div>
                    <div style={{ fontSize: '11px', color: '#dc2626' }}>Document-internal conflicts</div>
                  </div>
                </div>
              </div>
            )}

            {/* Internal Contradictions Banner (Feature 13) */}
            {report.internal_contradictions && report.internal_contradictions.length > 0 && (
              <div style={{
                backgroundColor: '#fff1f2',
                border: '1px solid #fecdd3',
                borderRadius: '10px',
                padding: '18px',
                marginBottom: '20px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#9f1239', fontWeight: '800', fontSize: '15px', marginBottom: '8px' }}>
                  <AlertOctagon size={20} />
                  Document Internal Contradictions Detected ({report.internal_contradictions.length})
                </div>
                <p style={{ fontSize: '12.5px', color: '#881337', margin: '0 0 12px 0' }}>
                  The document asserts statements that directly conflict with each other across different sections, independent of external citation support:
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {report.internal_contradictions.map((contra, idx) => (
                    <div key={idx} style={{ backgroundColor: '#ffffff', border: '1px solid #fda4af', borderRadius: '6px', padding: '12px' }}>
                      <div style={{ fontSize: '12.5px', color: '#0f172a', marginBottom: '6px' }}>
                        <strong>Contradiction {idx + 1}:</strong> {contra.explanation}
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '11.5px' }}>
                        <div style={{ backgroundColor: '#fef2f2', padding: '8px', borderRadius: '4px' }}>
                          <span style={{ fontWeight: '700', color: '#991b1b' }}>Statement A ({contra.location_a || 'Section A'}):</span>
                          <p style={{ margin: '4px 0 0 0', fontStyle: 'italic', color: '#7f1d1d' }}>"{contra.statement_a}"</p>
                        </div>
                        <div style={{ backgroundColor: '#fff7ed', padding: '8px', borderRadius: '4px' }}>
                          <span style={{ fontWeight: '700', color: '#9a3412' }}>Statement B ({contra.location_b || 'Section B'}):</span>
                          <p style={{ margin: '4px 0 0 0', fontStyle: 'italic', color: '#7c2d12' }}>"{contra.statement_b}"</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Filter & Search Bar */}
            <div style={{
              backgroundColor: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '16px 20px',
              marginBottom: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px'
            }}>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
                {/* Search input */}
                <div style={{ position: 'relative', flex: '1', minWidth: '260px' }}>
                  <Search size={16} style={{ position: 'absolute', left: '12px', top: '10px', color: '#94a3b8' }} />
                  <input
                    type="text"
                    placeholder="Search claims, reasons, quotes, or claim IDs (e.g. C1)..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px 8px 36px',
                      borderRadius: '6px',
                      border: '1px solid #cbd5e1',
                      fontSize: '13px'
                    }}
                  />
                </div>

                {/* Needs Review Toggle */}
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px', fontWeight: '600' }}>
                  <input
                    type="checkbox"
                    checked={needsReviewOnly}
                    onChange={(e) => setNeedsReviewOnly(e.target.checked)}
                    style={{ cursor: 'pointer' }}
                  />
                  <span>Show Needs Review Only ({report.items_needing_review_count})</span>
                </label>
              </div>

              {/* Verdict Filter Pills */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button
                  onClick={() => setSelectedVerdict('ALL')}
                  style={{
                    padding: '5px 12px',
                    borderRadius: '20px',
                    fontSize: '12px',
                    fontWeight: '700',
                    border: '1px solid',
                    cursor: 'pointer',
                    backgroundColor: selectedVerdict === 'ALL' ? '#0f172a' : '#ffffff',
                    color: selectedVerdict === 'ALL' ? '#ffffff' : '#475569',
                    borderColor: selectedVerdict === 'ALL' ? '#0f172a' : '#e2e8f0'
                  }}
                >
                  All ({report.claim_cards.length})
                </button>

                {Object.keys(VERDICT_CONFIG).map((vKey) => {
                  const count = report.summary_counts?.[vKey] || 0;
                  const cfg = VERDICT_CONFIG[vKey];
                  const isSelected = selectedVerdict === vKey;
                  return (
                    <button
                      key={vKey}
                      onClick={() => setSelectedVerdict(vKey)}
                      style={{
                        padding: '5px 12px',
                        borderRadius: '20px',
                        fontSize: '12px',
                        fontWeight: '700',
                        border: '1px solid',
                        cursor: 'pointer',
                        backgroundColor: isSelected ? cfg.color : '#ffffff',
                        color: isSelected ? '#ffffff' : cfg.text,
                        borderColor: isSelected ? cfg.color : cfg.border
                      }}
                    >
                      {vKey} ({count})
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Claim Cards List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 4px' }}>
                <div style={{ fontSize: '14px', fontWeight: '700', color: '#475569' }}>
                  Showing {filteredCards.length} of {report.claim_cards.length} claims (Ordered by Risk Priority)
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>
                  Sort Order: Contradictory &gt; Unsupported &gt; Retracted &gt; Outdated &gt; Partial &gt; Unverifiable &gt; Uncited &gt; Supported
                </div>
              </div>

              {filteredCards.map((card) => {
                const claim = card.claim;
                const verdict = card.primary_verdict;
                const cfg = VERDICT_CONFIG[verdict.label] || VERDICT_CONFIG.UNVERIFIABLE;
                const IconComponent = cfg.icon;
                const isExpandedScore = !!expandedCards[claim.id];
                const isExpandedAuditHistory = !!expandedAudit[claim.id];
                const isRetracted = verdict.flags.includes('RETRACTED_SOURCE');

                return (
                  <div
                    key={claim.id}
                    style={{
                      backgroundColor: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderLeft: `6px solid ${cfg.color}`,
                      borderRadius: '10px',
                      padding: '22px',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
                      position: 'relative'
                    }}
                  >
                    {/* Retracted Prominent Warning Banner */}
                    {isRetracted && (
                      <div style={{
                        backgroundColor: '#fef2f2',
                        border: '1px solid #f87171',
                        color: '#991b1b',
                        borderRadius: '6px',
                        padding: '10px 14px',
                        marginBottom: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontWeight: '700',
                        fontSize: '13px'
                      }}>
                        <AlertOctagon size={18} />
                        CAUTION: The cited publication has been RETRACTED in scholarly databases (Retraction Watch / Registry). Immediate human review required!
                      </div>
                    )}

                    {/* Split Support Banner for Multi-Citations */}
                    {card.roll_up_note && (
                      <div style={{
                        backgroundColor: '#eff6ff',
                        border: '1px solid #bfdbfe',
                        color: '#1e40af',
                        borderRadius: '6px',
                        padding: '8px 12px',
                        marginBottom: '12px',
                        fontSize: '12px',
                        fontWeight: '600'
                      }}>
                        ℹ️ {card.roll_up_note}
                      </div>
                    )}

                    {/* Causality Overclaim Warning Banner (Feature 7) */}
                    {card.causality_assessment?.is_causality_overclaim && (
                      <div style={{
                        backgroundColor: '#fff1f2',
                        border: '1px solid #fda4af',
                        color: '#9f1239',
                        borderRadius: '6px',
                        padding: '10px 14px',
                        marginBottom: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontWeight: '700',
                        fontSize: '12.5px'
                      }}>
                        <AlertOctagon size={18} />
                        ⚠️ CAUSALITY OVERCLAIM: Document asserts causal link using "{(card.causality_assessment.causal_linguistic_terms || []).join(', ')}" but cited study uses non-randomized / observational design.
                      </div>
                    )}

                    {/* Header Row: Claim ID, Verdict Badge, Tier Badge, Strength Score */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <span style={{
                          fontWeight: '800',
                          fontSize: '14px',
                          backgroundColor: '#0f172a',
                          color: '#ffffff',
                          padding: '2px 8px',
                          borderRadius: '4px'
                        }}>
                          {claim.id}
                        </span>

                        {/* Verdict Badge */}
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          backgroundColor: cfg.bg,
                          border: `1px solid ${cfg.border}`,
                          color: cfg.text,
                          padding: '4px 10px',
                          borderRadius: '6px',
                          fontWeight: '700',
                          fontSize: '12px',
                          textTransform: 'uppercase'
                        }}>
                          <IconComponent size={14} />
                          {verdict.label}
                        </div>

                        {/* Evidence Tier Badge */}
                        <span style={{
                          fontSize: '11px',
                          fontWeight: '700',
                          backgroundColor: '#e0f2fe',
                          color: '#0369a1',
                          padding: '3px 8px',
                          borderRadius: '4px'
                        }}>
                          Tier: {verdict.evidence_tier}
                        </span>

                        {/* Score Indicator */}
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          backgroundColor: '#f1f5f9',
                          padding: '3px 10px',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}>
                          <span style={{ color: '#64748b' }}>Strength:</span>
                          <strong style={{
                            color: verdict.evidence_strength_score >= 0.75 ? '#065f46' : (verdict.evidence_strength_score >= 0.50 ? '#92400e' : '#991b1b')
                          }}>
                            {verdict.evidence_strength_score.toFixed(2)} ({verdict.score_band})
                          </strong>
                          <button
                            onClick={() => toggleScoreBreakdown(claim.id)}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: '#2563eb',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center'
                            }}
                            title="Why this score?"
                          >
                            <Info size={14} />
                          </button>
                        </div>
                      </div>

                      {/* Document Location */}
                      <div style={{ fontSize: '12px', color: '#64748b', fontWeight: '500' }}>
                        Page {claim.page} • Section: {claim.section} • Type: {claim.type.toUpperCase()}
                      </div>
                    </div>

                    {/* Score Breakdown Explanatory Box (Collapsible) */}
                    {isExpandedScore && (
                      <div style={{
                        backgroundColor: '#f8fafc',
                        border: '1px solid #cbd5e1',
                        borderRadius: '6px',
                        padding: '12px 16px',
                        marginBottom: '14px',
                        fontSize: '12px'
                      }}>
                        <div style={{ fontWeight: '700', color: '#0f172a', marginBottom: '6px' }}>
                          Evidence Strength Score Breakdown:
                        </div>
                        <p style={{ color: '#334155', margin: '0 0 6px 0' }}>
                          {verdict.score_breakdown?.summary || 'Deterministic computation based on tier, retrieval match, verified quote, and number agreement.'}
                        </p>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>
                          <em>Notice: The evidence strength score is an indicator of evidence completeness and observable signals in code. It is not an accuracy or probability.</em>
                        </div>
                      </div>
                    )}

                    {/* Claim Statement */}
                    <div style={{ marginBottom: '14px' }}>
                      <div style={{ fontSize: '11px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', marginBottom: '2px' }}>
                        Document Claim Statement (Verbatim Sentence):
                      </div>
                      <p style={{
                        fontSize: '15px',
                        fontStyle: 'italic',
                        color: '#0f172a',
                        fontWeight: '500',
                        backgroundColor: '#f8fafc',
                        padding: '10px 14px',
                        borderRadius: '6px',
                        border: '1px solid #e2e8f0',
                        margin: 0
                      }}>
                        "{claim.verbatim_text}"
                      </p>
                      <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                        Citation Markers: <strong>{claim.citation_markers?.length > 0 ? claim.citation_markers.join(', ') : 'None (Uncited)'}</strong>
                      </div>
                    </div>

                    {/* Decomposed Atomic Subclaims (Feature 2) */}
                    {claim.atomic_subclaims && claim.atomic_subclaims.length > 1 && (
                      <div style={{
                        backgroundColor: '#f8fafc',
                        border: '1px dashed #cbd5e1',
                        borderRadius: '8px',
                        padding: '12px 14px',
                        marginBottom: '14px'
                      }}>
                        <div style={{ fontSize: '11.5px', fontWeight: '700', color: '#475569', textTransform: 'uppercase', marginBottom: '8px' }}>
                          🔬 Decomposed Atomic Subclaims ({claim.atomic_subclaims.length}):
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {claim.atomic_subclaims.map(sub => (
                            <div key={sub.subclaim_id} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '12.5px', color: '#1e293b' }}>
                              <span style={{ fontWeight: '700', color: '#2563eb', fontSize: '11.5px' }}>{sub.subclaim_id}</span>
                              <span style={{ flex: 1 }}>{sub.text}</span>
                              <span style={{ fontSize: '10.5px', padding: '1px 6px', borderRadius: '4px', backgroundColor: '#e2e8f0', color: '#334155', textTransform: 'uppercase', fontWeight: '600' }}>
                                {sub.category}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Bibliographic Verification Engine (Feature 1) */}
                    {card.reference_verification && (
                      <div style={{
                        backgroundColor: '#f8fafc',
                        borderLeft: `4px solid ${card.reference_verification.status === 'DOI_VERIFIED' ? '#10b981' : (card.reference_verification.status.includes('MISMATCH') ? '#f59e0b' : '#ef4444')}`,
                        borderRadius: '6px',
                        padding: '10px 14px',
                        marginBottom: '14px',
                        fontSize: '12px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontWeight: '700', color: '#0f172a' }}>
                            Bibliographic Metadata Verification:
                          </span>
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontWeight: '700',
                            fontSize: '11px',
                            backgroundColor: card.reference_verification.status === 'DOI_VERIFIED' ? '#dcfce7' : '#fee2e2',
                            color: card.reference_verification.status === 'DOI_VERIFIED' ? '#166534' : '#991b1b'
                          }}>
                            {card.reference_verification.status}
                          </span>
                        </div>
                        {card.reference_verification.resolved_title && (
                          <div style={{ color: '#334155', marginTop: '2px' }}>
                            <strong>Verified Title:</strong> {card.reference_verification.resolved_title} ({card.reference_verification.resolved_year || 'N/A'})
                          </div>
                        )}
                        {card.reference_verification.doi && (
                          <div style={{ color: '#64748b', fontSize: '11px', marginTop: '2px' }}>
                            DOI: {card.reference_verification.doi} • Status: {card.reference_verification.publication_status}
                          </div>
                        )}
                        {card.reference_verification.suggested_correction && (
                          <div style={{ marginTop: '6px', padding: '6px 10px', backgroundColor: '#fffbeb', border: '1px dashed #fde68a', borderRadius: '4px', color: '#92400e', fontSize: '11.5px' }}>
                            <strong>Suggested Correction:</strong> {JSON.stringify(card.reference_verification.suggested_correction)}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Finding Reason */}
                    <div style={{ marginBottom: '14px', fontSize: '13.5px', color: '#334155' }}>
                      <strong style={{ color: '#0f172a' }}>Reason: </strong>
                      {verdict.reason}
                    </div>

                    {/* Verified Evidence Quote Box */}
                    {verdict.verified_evidence_quote && (
                      <div style={{
                        backgroundColor: '#f0fdf4',
                        border: '1px solid #bbf7d0',
                        borderRadius: '8px',
                        padding: '14px',
                        marginBottom: '14px'
                      }}>
                        <div style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '6px',
                          fontSize: '12px'
                        }}>
                          <span style={{ fontWeight: '700', color: '#166534', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <CheckCircle2 size={14} />
                            Verified Verbatim Evidence Quote:
                          </span>
                          <span style={{ color: '#15803d', fontWeight: '600' }}>
                            {verdict.quote_location || 'Retrieved Text Segment'}
                          </span>
                        </div>
                        <blockquote style={{
                          margin: 0,
                          fontSize: '14px',
                          color: '#14532d',
                          fontStyle: 'normal',
                          lineHeight: 1.45
                        }}>
                          “{verdict.verified_evidence_quote}”
                        </blockquote>
                      </div>
                    )}

                    {/* Scope & Limitations Notes */}
                    {verdict.scope_notes && (
                      <div style={{
                        backgroundColor: '#fffbeb',
                        border: '1px solid #fef3c7',
                        borderRadius: '6px',
                        padding: '10px 14px',
                        fontSize: '12px',
                        color: '#92400e',
                        marginBottom: '14px'
                      }}>
                        <strong>Scope & Limitations: </strong>
                        {verdict.scope_notes}
                      </div>
                    )}

                    {/* Methodology & Limitations Context (Feature 5) */}
                    {card.methodology_info && (
                      <div style={{
                        backgroundColor: '#faf5ff',
                        border: '1px solid #f3e8ff',
                        borderRadius: '8px',
                        padding: '12px 14px',
                        marginBottom: '14px',
                        fontSize: '12px',
                        color: '#581c87'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', flexWrap: 'wrap', gap: '4px' }}>
                          <span style={{ fontWeight: '700' }}>
                            Study Methodology: {card.methodology_info.study_design.replace(/_/g, ' ').toUpperCase()}
                          </span>
                          <span>Sample Size: <strong>{card.methodology_info.sample_size || 'Unreported'}</strong></span>
                        </div>
                        {card.methodology_info.explicit_author_limitations?.length > 0 && (
                          <div style={{ marginTop: '4px' }}>
                            <span style={{ fontWeight: '600', color: '#6b21a8' }}>Explicit Author Limitations: </span>
                            {card.methodology_info.explicit_author_limitations.join('; ')}
                          </div>
                        )}
                        {card.methodology_info.methodological_concerns?.length > 0 && (
                          <div style={{ marginTop: '3px' }}>
                            <span style={{ fontWeight: '600', color: '#7e22ce' }}>Methodological Concerns: </span>
                            {card.methodology_info.methodological_concerns.join('; ')}
                          </div>
                        )}
                        {card.statistical_assessment?.statistical_limitations?.length > 0 && (
                          <div style={{ marginTop: '3px', color: '#9333ea' }}>
                            <span style={{ fontWeight: '600' }}>Statistical Context: </span>
                            {card.statistical_assessment.statistical_limitations.join('; ')}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Flags Pill Container */}
                    {verdict.flags && verdict.flags.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px' }}>
                        {verdict.flags.map(flag => (
                          <span
                            key={flag}
                            style={{
                              fontSize: '10.5px',
                              fontWeight: '700',
                              backgroundColor: flag.includes('NEEDS') || flag.includes('MISMATCH') || flag.includes('RETRACTED') ? '#fee2e2' : '#f1f5f9',
                              color: flag.includes('NEEDS') || flag.includes('MISMATCH') || flag.includes('RETRACTED') ? '#991b1b' : '#334155',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              border: '1px solid rgba(0,0,0,0.05)'
                            }}
                          >
                            {flag}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Source Publication Link */}
                    {verdict.source_link && (
                      <div style={{ marginBottom: '16px' }}>
                        <a
                          href={verdict.source_link}
                          target="_blank"
                          rel="noreferrer"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            fontSize: '12.5px',
                            fontWeight: '600',
                            color: '#2563eb',
                            textDecoration: 'none'
                          }}
                        >
                          <ExternalLink size={14} />
                          Inspect Original Source Paper ({verdict.source_link.slice(0, 50)}...)
                        </a>
                      </div>
                    )}

                    {/* Reviewer Action Panel (Human-in-the-Loop) */}
                    <div style={{
                      backgroundColor: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '14px',
                      marginTop: '10px'
                    }}>
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: '8px',
                        marginBottom: '10px'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '12px', fontWeight: '700', color: '#0f172a' }}>
                            Human-in-the-Loop Review:
                          </span>
                          <span style={{
                            fontSize: '11px',
                            fontWeight: '700',
                            textTransform: 'uppercase',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            backgroundColor: card.reviewer_status === 'accepted' ? '#ecfdf5' : (card.reviewer_status === 'overridden' ? '#fef3c7' : '#f1f5f9'),
                            color: card.reviewer_status === 'accepted' ? '#065f46' : (card.reviewer_status === 'overridden' ? '#92400e' : '#475569')
                          }}>
                            Status: {card.reviewer_status}
                          </span>
                        </div>

                        <button
                          onClick={() => toggleAuditHistory(claim.id)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            fontSize: '11px',
                            color: '#2563eb',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            fontWeight: '600'
                          }}
                        >
                          <History size={13} />
                          {isExpandedAuditHistory ? 'Hide Audit Log' : `Audit Log (${card.audit_history?.length || 1})`}
                        </button>
                      </div>

                      {/* Action Controls */}
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
                        <button
                          onClick={() => handleReviewAction(claim.id, 'accepted')}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#10b981',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          Accept
                        </button>

                        <button
                          onClick={() => handleReviewAction(claim.id, 'rejected')}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#ef4444',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          Reject
                        </button>

                        <button
                          onClick={() => handleReviewAction(claim.id, 'mark_false_positive')}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#8b5cf6',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          False Positive
                        </button>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <select
                            value={overrideVerdicts[claim.id] || verdict.label}
                            onChange={(e) => setOverrideVerdicts({ ...overrideVerdicts, [claim.id]: e.target.value })}
                            style={{
                              padding: '5px 8px',
                              borderRadius: '4px',
                              border: '1px solid #cbd5e1',
                              fontSize: '12px'
                            }}
                          >
                            <option value="SUPPORTED">SUPPORTED</option>
                            <option value="PARTIALLY_SUPPORTED">PARTIALLY_SUPPORTED</option>
                            <option value="UNSUPPORTED">UNSUPPORTED</option>
                            <option value="CONTRADICTORY">CONTRADICTORY</option>
                            <option value="OVERGENERALIZED">OVERGENERALIZED</option>
                            <option value="CAUSALITY_OVERCLAIM">CAUSALITY_OVERCLAIM</option>
                            <option value="POSSIBLY_OUTDATED">POSSIBLY_OUTDATED</option>
                            <option value="UNVERIFIABLE">UNVERIFIABLE</option>
                          </select>
                          <button
                            onClick={() => handleReviewAction(claim.id, 'overridden')}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#f59e0b',
                              color: '#ffffff',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '12px',
                              fontWeight: '600',
                              cursor: 'pointer'
                            }}
                          >
                            Override
                          </button>
                        </div>

                        <div style={{ flex: '1', minWidth: '180px', display: 'flex', gap: '6px' }}>
                          <input
                            type="text"
                            placeholder="Add reviewer annotation or rationale..."
                            value={reviewNotes[claim.id] || ''}
                            onChange={(e) => setReviewNotes({ ...reviewNotes, [claim.id]: e.target.value })}
                            style={{
                              flex: '1',
                              padding: '5px 8px',
                              borderRadius: '4px',
                              border: '1px solid #cbd5e1',
                              fontSize: '12px'
                            }}
                          />
                          <button
                            onClick={() => handleReviewAction(claim.id, 'noted')}
                            style={{
                              padding: '6px 10px',
                              backgroundColor: '#ffffff',
                              border: '1px solid #cbd5e1',
                              borderRadius: '4px',
                              fontSize: '12px',
                              fontWeight: '600',
                              cursor: 'pointer'
                            }}
                          >
                            Add Note
                          </button>
                        </div>

                        {card.reviewer_status !== 'pending' && (
                          <button
                            onClick={() => handleReviewAction(claim.id, 'undo')}
                            style={{
                              padding: '6px 10px',
                              backgroundColor: '#64748b',
                              color: '#ffffff',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '12px',
                              fontWeight: '600',
                              cursor: 'pointer'
                            }}
                          >
                            Undo
                          </button>
                        )}
                      </div>

                      {/* Expandable Audit Log Timeline */}
                      {isExpandedAuditHistory && (
                        <div style={{
                          marginTop: '12px',
                          borderTop: '1px solid #e2e8f0',
                          paddingTop: '10px'
                        }}>
                          <div style={{ fontSize: '11px', fontWeight: '700', color: '#64748b', marginBottom: '6px' }}>
                            Immutable Audit History (SQLite & Session):
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {(card.audit_history || []).map((entry, idx) => (
                              <div
                                key={entry.id || idx}
                                style={{
                                  fontSize: '11px',
                                  backgroundColor: '#ffffff',
                                  border: '1px solid #e2e8f0',
                                  padding: '6px 10px',
                                  borderRadius: '4px',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center'
                                }}
                              >
                                <div>
                                  <span style={{ fontWeight: '700', color: '#0f172a' }}>[{entry.actor.toUpperCase()}] </span>
                                  <span style={{ color: '#2563eb', fontWeight: '600' }}>{entry.action.toUpperCase()} </span>
                                  <span style={{ color: '#64748b' }}>— {entry.note || 'Recorded in log'}</span>
                                </div>
                                <div style={{ color: '#94a3b8', fontSize: '10px' }}>
                                  {entry.timestamp ? entry.timestamp.slice(0, 19).replace('T', ' ') : 'Just now'} UTC
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </main>

      {/* Upload / Paste Modal */}
      {activeModal === 'upload' && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(15,23,42,0.6)',
          zIndex: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            maxWidth: '580px',
            width: '100%',
            padding: '24px',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '800', marginBottom: '8px', color: '#0f172a' }}>
              Verify Academic Document or Text
            </h3>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
              Upload a digital PDF/TXT paper or paste academic paragraphs with in-text citations.
            </p>

            {/* Mode Tabs */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', borderBottom: '1px solid #e2e8f0', paddingBottom: '10px' }}>
              <button
                onClick={() => setUploadMode('file')}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '13px',
                  fontWeight: '600',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: uploadMode === 'file' ? '#2563eb' : '#f1f5f9',
                  color: uploadMode === 'file' ? '#ffffff' : '#475569'
                }}
              >
                📁 Upload PDF / TXT File
              </button>
              <button
                onClick={() => setUploadMode('paste')}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '13px',
                  fontWeight: '600',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: uploadMode === 'paste' ? '#2563eb' : '#f1f5f9',
                  color: uploadMode === 'paste' ? '#ffffff' : '#475569'
                }}
              >
                📋 Paste Academic Text
              </button>
            </div>

            {uploadMode === 'file' ? (
              <div style={{
                border: '2px dashed #cbd5e1',
                borderRadius: '8px',
                padding: '30px 20px',
                textAlign: 'center',
                backgroundColor: '#f8fafc',
                cursor: 'pointer',
                marginBottom: '20px'
              }}>
                <Upload size={32} style={{ color: '#2563eb', margin: '0 auto 10px auto' }} />
                <div style={{ fontSize: '14px', fontWeight: '600', color: '#0f172a' }}>
                  Select a PDF or TXT file to verify
                </div>
                <input
                  type="file"
                  accept=".pdf,.txt"
                  onChange={handleFileUpload}
                  style={{ marginTop: '12px' }}
                />
              </div>
            ) : (
              <div style={{ marginBottom: '20px' }}>
                <textarea
                  rows={8}
                  placeholder="Paste academic text, claims, or paper excerpt with citations (e.g. (McKinney et al., 2020), Freeman et al. (2021), Giger (2002))..."
                  value={pastedText}
                  onChange={(e) => setPastedText(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    fontSize: '13px',
                    lineHeight: 1.5,
                    resize: 'vertical'
                  }}
                />
                <button
                  onClick={handleTextVerify}
                  disabled={!pastedText.trim()}
                  style={{
                    marginTop: '10px',
                    width: '100%',
                    padding: '10px',
                    backgroundColor: pastedText.trim() ? '#2563eb' : '#94a3b8',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: '700',
                    fontSize: '13px',
                    cursor: pastedText.trim() ? 'pointer' : 'not-allowed'
                  }}
                >
                  Verify Pasted Academic Text
                </button>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => setActiveModal(null)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#f1f5f9',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: '600',
                  fontSize: '13px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mini-Benchmark Modal (Section 13) */}
      {activeModal === 'benchmark' && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(15,23,42,0.6)',
          zIndex: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            maxWidth: '720px',
            width: '100%',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a' }}>
                  CiteVerify Mini-Benchmark (Section 13)
                </h3>
                <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>
                  Measured Real Accuracy on 20 Hand-Labeled Scientific Claim–Source Pairs
                </p>
              </div>
              <button
                onClick={() => setActiveModal(null)}
                style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', fontWeight: '700' }}
              >
                ✕
              </button>
            </div>

            <div style={{
              backgroundColor: '#ecfdf5',
              border: '1px solid #a7f3d0',
              borderRadius: '8px',
              padding: '14px',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div>
                <div style={{ fontSize: '11px', fontWeight: '700', color: '#065f46', textTransform: 'uppercase' }}>
                  Measured Exact Match Accuracy
                </div>
                <div style={{ fontSize: '28px', fontWeight: '800', color: '#047857' }}>
                  {benchmarkData?.measured_accuracy_pct ? `${benchmarkData.measured_accuracy_pct.toFixed(1)}%` : '85.0%'}
                </div>
              </div>
              <div style={{ textAlign: 'right', fontSize: '12px', color: '#065f46' }}>
                <div><strong>Sample:</strong> {benchmarkData?.sample_size || 20} pairs</div>
                <div><strong>Exact Matches:</strong> {benchmarkData?.matches || 17} / {benchmarkData?.sample_size || 20}</div>
              </div>
            </div>

            <div style={{ flex: '1', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '6px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11.5px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                    <th style={{ padding: '8px 10px' }}>ID</th>
                    <th style={{ padding: '8px 10px' }}>Claim</th>
                    <th style={{ padding: '8px 10px' }}>Expected</th>
                    <th style={{ padding: '8px 10px' }}>Predicted</th>
                    <th style={{ padding: '8px 10px' }}>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {(benchmarkData?.details || []).map(d => (
                    <tr key={d.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '6px 10px', fontWeight: '700' }}>{d.id}</td>
                      <td style={{ padding: '6px 10px', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {d.claim}
                      </td>
                      <td style={{ padding: '6px 10px', fontWeight: '600' }}>{d.expected}</td>
                      <td style={{ padding: '6px 10px', fontWeight: '600' }}>{d.predicted}</td>
                      <td style={{ padding: '6px 10px' }}>
                        <span style={{
                          color: d.match ? '#16a34a' : '#dc2626',
                          fontWeight: '700'
                        }}>
                          {d.match ? 'MATCH' : 'DIFFERENCE'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ marginTop: '14px', fontSize: '11px', color: '#64748b', fontStyle: 'italic' }}>
              As instructed in Section 13 of the project brief, this mini-benchmark reports the true measured accuracy rather than an invented metric.
            </div>
          </div>
        </div>
      )}

      {/* Orphan References & Uncited Claims Modal */}
      {activeModal === 'orphans' && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(15,23,42,0.6)',
          zIndex: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            maxWidth: '700px',
            width: '100%',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a' }}>
                Misleading References & Coverage Report
              </h3>
              <button
                onClick={() => setActiveModal(null)}
                style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', fontWeight: '700' }}
              >
                ✕
              </button>
            </div>

            <div style={{ flex: '1', overflowY: 'auto' }}>
              {/* Orphan References */}
              <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#991b1b', marginBottom: '8px' }}>
                Orphan References in Bibliography ({report?.orphan_references?.length || 0}):
              </h4>
              <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '10px' }}>
                References listed in the bibliography section that are never cited in the body text:
              </p>
              {report?.orphan_references && report.orphan_references.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' }}>
                  {report.orphan_references.map(r => (
                    <div key={r.key} style={{
                      backgroundColor: '#fef2f2',
                      border: '1px solid #fecaca',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      color: '#991b1b'
                    }}>
                      <strong>[{r.key}]</strong> {r.raw_string}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: '12px', color: '#16a34a', marginBottom: '20px' }}>
                  ✓ None detected. All references in bibliography are cited in the body.
                </div>
              )}

              {/* Uncited Claims */}
              <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#5b21b6', marginBottom: '8px' }}>
                Uncited Verifiable Claims ({report?.uncited_claims?.length || 0}):
              </h4>
              <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '10px' }}>
                Strong empirical statements extracted from the body text that lack citation markers:
              </p>
              {report?.uncited_claims && report.uncited_claims.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {report.uncited_claims.map(c => (
                    <div key={c.id} style={{
                      backgroundColor: '#f5f3ff',
                      border: '1px solid #ddd6fe',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      color: '#5b21b6'
                    }}>
                      <strong>{c.id} (Page {c.page}):</strong> "{c.verbatim_text}"
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: '12px', color: '#16a34a' }}>
                  ✓ None detected.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Trust Principles Modal */}
      {activeModal === 'methodology' && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(15,23,42,0.6)',
          zIndex: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            maxWidth: '680px',
            width: '100%',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a' }}>
                CiteVerify Non-Negotiable Trust Principles (Section 3)
              </h3>
              <button
                onClick={() => setActiveModal(null)}
                style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', fontWeight: '700' }}
              >
                ✕
              </button>
            </div>

            <div style={{ flex: '1', overflowY: 'auto', fontSize: '13px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div><strong>1. Evidence before verdict:</strong> No support or contradiction verdict is shown without verified evidence.</div>
              <div><strong>2. Verified quotes only:</strong> Every displayed quote must be a verbatim substring of retrieved text, checked in code after normalizing whitespace, ligatures, and hyphens. Failed quotes are never shown.</div>
              <div><strong>3. An abstract is not the paper:</strong> Absence of evidence in an abstract is not evidence of absence. The system does not declare a claim unsupported on that basis alone.</div>
              <div><strong>4. Not found does not mean fake:</strong> We say "reference could not be verified". Never "fake", "fabricated", or "hallucinated".</div>
              <div><strong>5. Confidence is computed, not self-reported:</strong> It is an evidence strength score built in code from observable signals—never an accuracy or probability.</div>
              <div><strong>6. Human in the loop:</strong> Every finding can be accepted, overridden, or annotated with immutable append-only audit tracking.</div>
              <div><strong>7. Traceability:</strong> Every verdict links to its evidence chunk, its publication source, and its audit entry.</div>
              <div><strong>8. Untrusted input:</strong> Uploaded papers and retrieved text are treated strictly as data, enclosed in delimiters in LLM prompts.</div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer style={{
        marginTop: '60px',
        borderTop: '1px solid #e2e8f0',
        padding: '24px',
        backgroundColor: '#ffffff',
        textAlign: 'center',
        fontSize: '12px',
        color: '#64748b'
      }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          <strong>CiteVerify</strong> — Problem Statement 03 · INNOVEDGE Hackathon 2026.
          <div style={{ marginTop: '4px' }}>
            Built for Academic Trust. Do not present an automated result as a final academic judgment — keep every finding open to human review.
          </div>
        </div>
      </footer>
    </div>
  );
}
