import { useState, useRef, useCallback } from 'react'

const API_URL = 'http://localhost:8000'

/* ───────── Animated Score Ring ───────── */
function ScoreRing({ score, maxScore = 1000 }) {
    const radius = 80
    const stroke = 10
    const circumference = 2 * Math.PI * radius
    const pct = Math.min(score / maxScore, 1)
    const offset = circumference * (1 - pct)

    const color =
        score >= 750 ? '#34d399' : score >= 600 ? '#fbbf24' : '#f87171'

    return (
        <svg width="200" height="200" viewBox="0 0 200 200" style={{ filter: `drop-shadow(0 0 18px ${color}55)` }}>
            <circle cx="100" cy="100" r={radius} fill="none" stroke="#1e293b" strokeWidth={stroke} />
            <circle
                cx="100" cy="100" r={radius}
                fill="none" stroke={color} strokeWidth={stroke}
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                transform="rotate(-90 100 100)"
                style={{ transition: 'stroke-dashoffset 1.2s ease-out, stroke 0.5s' }}
            />
            <text x="100" y="92" textAnchor="middle" fill={color} fontSize="42" fontWeight="800" style={{ fontFamily: 'Inter' }}>
                {score}
            </text>
            <text x="100" y="118" textAnchor="middle" fill="#94a3b8" fontSize="13" fontWeight="500">
                / {maxScore}
            </text>
        </svg>
    )
}

/* ───────── Main App ───────── */
export default function App() {
    const [file, setFile] = useState(null)
    const [dragging, setDragging] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [certLoading, setCertLoading] = useState(false)
    const inputRef = useRef()

    /* ── Drag & Drop handlers ── */
    const onDragOver = useCallback((e) => {
        e.preventDefault()
        setDragging(true)
    }, [])

    const onDragLeave = useCallback(() => setDragging(false), [])

    const onDrop = useCallback((e) => {
        e.preventDefault()
        setDragging(false)
        const dropped = e.dataTransfer.files[0]
        if (dropped && dropped.type === 'application/pdf') {
            setFile(dropped)
            setError(null)
        } else {
            setError('Please drop a valid PDF file.')
        }
    }, [])

    const onFileChange = (e) => {
        const chosen = e.target.files[0]
        if (chosen) {
            setFile(chosen)
            setError(null)
        }
    }

    /* ── Upload handler ── */
    const handleUpload = async () => {
        if (!file) return
        setUploading(true)
        setError(null)
        setResult(null)

        const formData = new FormData()
        formData.append('file', file)

        try {
            const res = await fetch(`${API_URL}/api/upload-receipt/1`, {
                method: 'POST',
                body: formData,
            })
            if (!res.ok) throw new Error(`Server error: ${res.status}`)
            const data = await res.json()
            setResult(data)
        } catch (err) {
            setError(err.message || 'Upload failed. Is the backend running?')
        } finally {
            setUploading(false)
        }
    }

    const resetState = () => {
        setFile(null)
        setResult(null)
        setError(null)
    }

    /* ── Certificate download ── */
    const handleCertificate = async () => {
        if (!file) return
        setCertLoading(true)
        try {
            const formData = new FormData()
            formData.append('file', file)
            const res = await fetch(`${API_URL}/api/certificate/1`, {
                method: 'POST',
                body: formData,
            })
            if (!res.ok) {
                const err = await res.json()
                throw new Error(err.detail || 'Certificate generation failed')
            }
            const blob = await res.blob()
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = 'KeyCred_Certificate.pdf'
            document.body.appendChild(a)
            a.click()
            a.remove()
            URL.revokeObjectURL(url)
        } catch (err) {
            setError(err.message)
        } finally {
            setCertLoading(false)
        }
    }

    const scoreColor = result
        ? result.keycred_score >= 750
            ? '#34d399'
            : result.keycred_score >= 600
                ? '#fbbf24'
                : '#f87171'
        : '#6366f1'

    return (
        <div style={{ minHeight: '100vh', background: 'linear-gradient(145deg, #0a0e1a 0%, #111827 50%, #0f172a 100%)' }}>
            {/* ═══ Header ═══ */}
            <header style={{
                backdropFilter: 'blur(16px)',
                background: 'rgba(17, 24, 39, 0.7)',
                borderBottom: '1px solid rgba(99, 102, 241, 0.15)',
                position: 'sticky', top: 0, zIndex: 50,
            }}>
                <div style={{ maxWidth: 1100, margin: '0 auto', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <img src="/keycred-logo.png" alt="KeyCred" style={{
                            width: 44, height: 44, borderRadius: 10,
                            objectFit: 'cover',
                            filter: 'drop-shadow(0 0 12px rgba(99,162,241,0.4))',
                        }} />
                        <div>
                            <h1 style={{ fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em', color: '#f1f5f9' }}>KeyCred</h1>
                            <p style={{ fontSize: 11, color: '#64748b', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Tenant Dashboard</p>
                        </div>
                    </div>
                    <div style={{
                        padding: '6px 16px', borderRadius: 20,
                        background: 'rgba(52, 211, 153, 0.1)', border: '1px solid rgba(52, 211, 153, 0.25)',
                        fontSize: 12, fontWeight: 600, color: '#34d399',
                    }}>● Live</div>
                </div>
            </header>

            {/* ═══ Main Content ═══ */}
            <main style={{ maxWidth: 1100, margin: '0 auto', padding: '48px 24px' }}>
                {/* Hero */}
                <div style={{ textAlign: 'center', marginBottom: 48 }}>
                    <img src="/keycred-logo.png" alt="KeyCred" style={{
                        width: 90, height: 90, margin: '0 auto 16px',
                        display: 'block', objectFit: 'cover',
                        filter: 'drop-shadow(0 0 24px rgba(99,162,241,0.35))',
                        borderRadius: 16,
                    }} />
                    <p style={{ fontSize: 13, fontWeight: 600, color: '#818cf8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
                        Financial Creditworthiness
                    </p>
                    <h2 style={{
                        fontSize: 36, fontWeight: 800, letterSpacing: '-0.03em',
                        background: 'linear-gradient(135deg, #f1f5f9 0%, #94a3b8 100%)',
                        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                    }}>
                        Upload Your Bank Receipt
                    </h2>
                    <p style={{ fontSize: 14, color: '#64748b', marginTop: 8, maxWidth: 500, margin: '8px auto 0', fontStyle: 'italic' }}>
                        Because trust is priceless
                    </p>
                    <p style={{ fontSize: 15, color: '#64748b', marginTop: 12, maxWidth: 500, margin: '12px auto 0' }}>
                        Get your KeyCred score instantly. Upload a Turkish bank receipt PDF to assess your rental creditworthiness.
                    </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: result ? '1fr 1fr' : '1fr', gap: 32, maxWidth: result ? 900 : 560, margin: '0 auto', transition: 'all 0.4s ease' }}>

                    {/* ── Upload Card ── */}
                    <div style={{
                        background: 'rgba(26, 31, 54, 0.6)',
                        border: `1px solid ${dragging ? 'rgba(99,102,241,0.6)' : 'rgba(99,102,241,0.15)'}`,
                        borderRadius: 20, padding: 32,
                        backdropFilter: 'blur(12px)',
                        transition: 'border-color 0.3s, box-shadow 0.3s',
                        boxShadow: dragging ? '0 0 40px rgba(99,102,241,0.15)' : 'none',
                    }}>
                        <h3 style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: 20, opacity: 0.7 }}>📄</span> Receipt Upload
                        </h3>

                        {/* Drop zone */}
                        <div
                            id="drop-zone"
                            onDragOver={onDragOver}
                            onDragLeave={onDragLeave}
                            onDrop={onDrop}
                            onClick={() => inputRef.current?.click()}
                            style={{
                                border: `2px dashed ${dragging ? '#6366f1' : file ? '#34d399' : '#334155'}`,
                                borderRadius: 16, padding: '40px 24px',
                                textAlign: 'center', cursor: 'pointer',
                                background: dragging ? 'rgba(99,102,241,0.06)' : file ? 'rgba(52,211,153,0.04)' : 'rgba(15,23,42,0.4)',
                                transition: 'all 0.3s',
                            }}
                        >
                            <input ref={inputRef} type="file" accept=".pdf" onChange={onFileChange} style={{ display: 'none' }} />
                            <div style={{ fontSize: 48, marginBottom: 12, opacity: 0.6 }}>
                                {file ? '✅' : dragging ? '📥' : '☁️'}
                            </div>
                            {file ? (
                                <div>
                                    <p style={{ fontSize: 15, fontWeight: 600, color: '#34d399' }}>{file.name}</p>
                                    <p style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                                        {(file.size / 1024).toFixed(1)} KB — Ready to process
                                    </p>
                                </div>
                            ) : (
                                <div>
                                    <p style={{ fontSize: 15, fontWeight: 600, color: '#94a3b8' }}>
                                        {dragging ? 'Drop it here!' : 'Drag & drop your PDF here'}
                                    </p>
                                    <p style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                                        or <span style={{ color: '#818cf8', textDecoration: 'underline' }}>browse files</span>
                                    </p>
                                </div>
                            )}
                        </div>

                        {/* Error */}
                        {error && (
                            <div style={{
                                marginTop: 16, padding: '12px 16px', borderRadius: 12,
                                background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.25)',
                                color: '#f87171', fontSize: 13, fontWeight: 500,
                            }}>
                                ⚠️ {error}
                            </div>
                        )}

                        {/* Upload button */}
                        <button
                            id="upload-btn"
                            onClick={handleUpload}
                            disabled={!file || uploading}
                            style={{
                                width: '100%', marginTop: 20, padding: '14px',
                                borderRadius: 12, border: 'none', cursor: file && !uploading ? 'pointer' : 'not-allowed',
                                background: file && !uploading
                                    ? 'linear-gradient(135deg, #6366f1, #818cf8)'
                                    : 'rgba(99,102,241,0.2)',
                                color: '#fff', fontSize: 15, fontWeight: 700,
                                letterSpacing: '-0.01em',
                                transition: 'all 0.3s',
                                boxShadow: file && !uploading ? '0 4px 20px rgba(99,102,241,0.3)' : 'none',
                                opacity: file && !uploading ? 1 : 0.5,
                            }}
                        >
                            {uploading ? (
                                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                                    <span style={{ display: 'inline-block', width: 16, height: 16, borderRadius: '50%', border: '2px solid transparent', borderTopColor: '#fff', animation: 'spin 0.8s linear infinite' }} />
                                    Processing…
                                </span>
                            ) : 'Analyze Receipt'}
                        </button>

                        {result && (
                            <button
                                onClick={resetState}
                                style={{
                                    width: '100%', marginTop: 10, padding: '12px',
                                    borderRadius: 12, border: '1px solid rgba(99,102,241,0.2)',
                                    background: 'transparent', color: '#818cf8',
                                    fontSize: 13, fontWeight: 600, cursor: 'pointer',
                                    transition: 'all 0.3s',
                                }}
                            >
                                Upload Another Receipt
                            </button>
                        )}
                    </div>

                    {/* ── Score Summary Card ── */}
                    {result && (
                        <div style={{
                            background: 'rgba(26, 31, 54, 0.6)',
                            border: '1px solid rgba(52,211,153,0.15)',
                            borderRadius: 20, padding: 32,
                            backdropFilter: 'blur(12px)',
                            animation: 'fadeIn 0.6s ease-out',
                        }}>
                            <h3 style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span style={{ fontSize: 20, opacity: 0.7 }}>🏆</span> KeyCred Score
                            </h3>

                            <div style={{ textAlign: 'center', marginBottom: 24 }}>
                                <ScoreRing score={result.keycred_score} />
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                                {[
                                    { label: 'Max Rent Limit', value: `₺${result.max_rent_limit.toLocaleString()}`, icon: '🏠' },
                                    { label: 'Pages Parsed', value: result.pages_parsed, icon: '📑' },
                                    { label: 'Status', value: result.status, icon: '✓' },
                                    { label: 'Receipt ID', value: `#${result.receipt_id}`, icon: '🗃️' },
                                ].map((item, i) => (
                                    <div key={i} style={{
                                        padding: '14px 16px', borderRadius: 12,
                                        background: 'rgba(15, 23, 42, 0.5)',
                                        border: '1px solid rgba(99,102,241,0.1)',
                                    }}>
                                        <div style={{ fontSize: 18, marginBottom: 4 }}>{item.icon}</div>
                                        <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 2 }}>
                                            {item.label}
                                        </div>
                                        <div style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9' }}>
                                            {item.value}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Rating badge */}
                            <div style={{
                                marginTop: 20, padding: '12px 20px', borderRadius: 12, textAlign: 'center',
                                background: `linear-gradient(135deg, ${scoreColor}15, ${scoreColor}08)`,
                                border: `1px solid ${scoreColor}30`,
                            }}>
                                <span style={{ fontSize: 14, fontWeight: 700, color: scoreColor }}>
                                    {result.keycred_score >= 750 ? '🌟 Excellent Creditworthiness' :
                                        result.keycred_score >= 600 ? '👍 Good Creditworthiness' :
                                            '⚠️ Needs Improvement'}
                                </span>
                            </div>

                            {/* Certificate download button */}
                            {result.is_approved && (
                                <button
                                    onClick={handleCertificate}
                                    disabled={certLoading}
                                    style={{
                                        width: '100%', marginTop: 14, padding: '14px',
                                        borderRadius: 12, border: 'none', cursor: certLoading ? 'wait' : 'pointer',
                                        background: 'linear-gradient(135deg, #34d399, #059669)',
                                        color: '#fff', fontSize: 14, fontWeight: 700,
                                        letterSpacing: '-0.01em',
                                        boxShadow: '0 4px 20px rgba(52,211,153,0.3)',
                                        transition: 'all 0.3s',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                                    }}
                                >
                                    {certLoading ? (
                                        <>
                                            <span style={{ display: 'inline-block', width: 16, height: 16, borderRadius: '50%', border: '2px solid transparent', borderTopColor: '#fff', animation: 'spin 0.8s linear infinite' }} />
                                            Generating…
                                        </>
                                    ) : (
                                        <>
                                            📜 Download Score Certificate
                                        </>
                                    )}
                                </button>
                            )}

                            {!result.is_approved && (
                                <div style={{
                                    marginTop: 14, padding: '12px 16px', borderRadius: 12, textAlign: 'center',
                                    background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)',
                                    fontSize: 12, color: '#f87171',
                                }}>
                                    ⚠️ Score must be ≥ 650 for certificate eligibility
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div style={{ textAlign: 'center', marginTop: 64, paddingBottom: 32 }}>
                    <img src="/keycred-logo.png" alt="KeyCred" style={{
                        width: 32, height: 32, margin: '0 auto 8px',
                        display: 'block', objectFit: 'cover',
                        opacity: 0.4, borderRadius: 6,
                        filter: 'grayscale(0.3)',
                    }} />
                    <p style={{ fontSize: 12, color: '#334155' }}>
                        KeyCred MVP • Because trust is priceless • © 2026
                    </p>
                </div>
            </main>

            <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
        </div>
    )
}
