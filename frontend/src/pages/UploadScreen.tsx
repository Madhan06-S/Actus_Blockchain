import React, { useState, useRef } from 'react';
import { Upload, FileText, AlertCircle, ShieldCheck, Loader2 } from 'lucide-react';
import { contractsApi } from '../api/contractsApi';

interface UploadScreenProps {
  onUploadSuccess: (documentId: string, file: File) => void;
}

export const UploadScreen: React.FC<UploadScreenProps> = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleFileSelect = async (file: File) => {
    setError(null);
    setSelectedFile(file);

    // Validation 1: PDF format
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please choose a PDF file.');
      setSelectedFile(null);
      return;
    }

    // Validation 2: Max 10 MB
    if (file.size > 10 * 1024 * 1024) {
      setError('This file is larger than 10 MB. Please choose a smaller contract.');
      setSelectedFile(null);
      return;
    }

    // Trigger Upload to FastAPI Backend
    setIsUploading(true);
    let docId: string;
    try {
      const res = await contractsApi.uploadDocument(file);
      docId = res.document_id;
      setIsUploading(false);
    } catch (err: unknown) {
      setIsUploading(false);
      const msg = err instanceof Error ? err.message : "We couldn't upload this contract. Please try again.";
      setError(msg);
      return;
    }

    // Safely advance to Review Terms screen
    try {
      await onUploadSuccess(docId, file);
    } catch (err) {
      console.warn('Workflow transition warning:', err);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '3rem auto', padding: '0 1.5rem' }} className="animate-fade-in">
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.2rem', color: '#0f172a', marginBottom: '0.75rem', fontWeight: 700 }}>
          Understand What Your Financial Contract Should Do
        </h1>
        <p style={{ fontSize: '1.05rem', color: '#475569', maxWidth: '640px', margin: '0 auto' }}>
          Upload a contract and we'll calculate its expected financial behavior and compare it with recorded activity.
        </p>
      </div>

      {error && (
        <div
          style={{
            backgroundColor: '#fff1f2',
            border: '1px solid #fecdd3',
            color: '#e11d48',
            padding: '0.85rem 1.25rem',
            borderRadius: '10px',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            fontSize: '0.9rem',
            fontWeight: 500,
          }}
        >
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {selectedFile && isUploading && (
        <div
          style={{
            backgroundColor: '#f0f9ff',
            border: '1px solid #bae6fd',
            color: '#0369a1',
            padding: '1rem 1.25rem',
            borderRadius: '12px',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <FileText size={24} color="#0284c7" />
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{selectedFile.name}</div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{formatFileSize(selectedFile.size)}</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.88rem', fontWeight: 600 }}>
            <Loader2 size={18} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
            Uploading & processing document...
          </div>
        </div>
      )}

      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragActive ? '#0284c7' : '#cbd5e1'}`,
          backgroundColor: dragActive ? '#f0f9ff' : '#ffffff',
          borderRadius: '16px',
          padding: '3.5rem 2rem',
          textAlign: 'center',
          cursor: isUploading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05)',
          opacity: isUploading ? 0.7 : 1,
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleChange}
          disabled={isUploading}
          style={{ display: 'none' }}
        />

        <div
          style={{
            width: '64px',
            height: '64px',
            backgroundColor: '#f0f9ff',
            color: '#0284c7',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem auto',
          }}
        >
          {isUploading ? (
            <Loader2 size={30} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
          ) : (
            <Upload size={30} />
          )}
        </div>

        <h3 style={{ fontSize: '1.25rem', color: '#0f172a', marginBottom: '0.5rem' }}>
          {isUploading ? 'Uploading contract PDF...' : 'Drop your PDF here'}
        </h3>
        <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '1.5rem' }}>
          or <span style={{ color: '#0284c7', fontWeight: 600, textDecoration: 'underline' }}>Browse files</span> from your computer
        </p>

        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            padding: '0.4rem 0.85rem',
            borderRadius: '20px',
            fontSize: '0.8rem',
            color: '#64748b',
          }}
        >
          <FileText size={14} /> PDF only • Maximum 10 MB
        </div>
      </div>

      <div
        style={{
          marginTop: '2rem',
          display: 'flex',
          justifyContent: 'center',
          gap: '2rem',
          fontSize: '0.85rem',
          color: '#64748b',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <ShieldCheck size={16} color="#059669" /> Secure Local Processing
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <ShieldCheck size={16} color="#059669" /> ACTUS Standardized Logic
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <ShieldCheck size={16} color="#059669" /> Immutable Ledger Verification
        </span>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
