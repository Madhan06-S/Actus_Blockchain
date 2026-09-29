import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { UploadScreen } from './pages/UploadScreen';
import { ReviewTermsScreen } from './pages/ReviewTermsScreen';
import { AnalysisScreen } from './pages/AnalysisScreen';
import { DashboardScreen } from './pages/DashboardScreen';
import { AIChatbotDrawer } from './components/AIChatbotDrawer';
import type { CandidateTerms, FinancialContract, RiskStatusResponse, ComparisonItem, RiskPredictionResponse } from './types/contract';
import { contractsApi } from './api/contractsApi';

export type AppStage = 'upload' | 'review' | 'analysis' | 'dashboard';

export const App: React.FC = () => {
  const [stage, setStage] = useState<AppStage>('upload');
  const [activeTab, setActiveTab] = useState('overview');

  // Application state for contract upload and document tracking
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Workflow data state
  const [terms, setTerms] = useState<CandidateTerms | null>(null);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [contract, setContract] = useState<FinancialContract | null>(null);
  const [statusData, setStatusData] = useState<RiskStatusResponse | null>(null);
  const [comparisonItems, setComparisonItems] = useState<ComparisonItem[]>([]);
  const [riskData, setRiskData] = useState<RiskPredictionResponse | null>(null);

  // 1. Handle PDF Upload Success from Real Backend
  const handleUploadSuccess = async (docId: string, file: File) => {
    // Reset all prior state so a new upload never shows stale previous contract
    setDocumentId(docId);
    setSelectedFile(file);
    setTerms(null);
    setExtractionError(null);
    setContract(null);
    setStatusData(null);
    setComparisonItems([]);
    setRiskData(null);

    try {
      const extractedTerms = await contractsApi.getExtractedTerms(docId);
      setTerms(extractedTerms);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Could not extract contract terms.';
      setExtractionError(msg);
    }
    setStage('review');
  };

  // 2. Handle Term Review Confirmation
  const handleConfirmTerms = async (confirmedTerms: CandidateTerms) => {
    setTerms(confirmedTerms);
    setStage('analysis');
  };

  // 3. Handle Analysis Completion
  const handleAnalysisComplete = async () => {
    if (!terms) { setStage('dashboard'); return; }
    try {
      let contractId: string;
      if (documentId) {
        const confirmRes = await contractsApi.confirmDocument(documentId, terms);
        contractId = confirmRes.contract_id;
      } else {
        const created = await contractsApi.createContract(terms);
        contractId = created.contract_id;
        setContract(created);
      }

      // Fetch full contract details if we only have an ID
      if (contractId && !contract) {
        try {
          const contractDetails = await contractsApi.createContract(terms);
          setContract(contractDetails);
        } catch { /* use id only */ }
      }

      // Use contractId for downstream calls
      const idToUse = contractId || contract?.contract_id;
      if (!idToUse) throw new Error('No contract ID available');

      const statusRes = await contractsApi.getStatus(idToUse);
      setStatusData(statusRes);

      const compRes = await contractsApi.getComparison(idToUse);
      setComparisonItems(compRes.items);

      // Set a minimal contract if we don't have one yet
      if (!contract) {
        setContract({
          contract_id: idToUse,
          principal: terms.principal,
          currency: terms.currency,
          annual_interest_rate: terms.annual_interest_rate,
          start_date: terms.start_date,
          maturity_date: terms.maturity_date,
          payment_frequency: terms.payment_frequency,
          contract_role: terms.contract_role,
          description: 'Fixed-Rate Annuity Financial Contract',
          status: 'VALIDATED',
          created_at: new Date().toISOString(),
        });
      }

      // Fetch AI Risk Prediction (non-blocking)
      try {
        const riskRes = await contractsApi.getRiskAnalysis(idToUse);
        setRiskData(riskRes);
      } catch { /* non-blocking */ }

    } catch (err) {
      console.warn('Analysis completion fallback:', err);
      // No demo data fallback — show what we have
    }
    setStage('dashboard');
  };

  // 4. Restart Workflow
  const handleRestart = () => {
    setDocumentId(null);
    setSelectedFile(null);
    setTerms(null);
    setExtractionError(null);
    setContract(null);
    setStatusData(null);
    setComparisonItems([]);
    setRiskData(null);
    setStage('upload');
    setActiveTab('overview');
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <div style={{ display: 'flex', flex: 1 }}>
        {stage === 'dashboard' && (
          <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        )}

        <main style={{ flex: 1, overflowX: 'hidden' }}>
          {stage === 'upload' && (
            <UploadScreen onUploadSuccess={handleUploadSuccess} />
          )}

          {stage === 'review' && (
            <ReviewTermsScreen
              documentId={documentId}
              fileName={selectedFile?.name}
              initialTerms={terms}
              extractionError={extractionError}
              onConfirm={handleConfirmTerms}
              onRetry={() => {
                setStage('upload');
                setTerms(null);
                setExtractionError(null);
              }}
            />
          )}

          {stage === 'analysis' && (
            <AnalysisScreen onComplete={handleAnalysisComplete} />
          )}

          {stage === 'dashboard' && (
            <DashboardScreen
              contract={contract}
              statusData={statusData}
              comparisonItems={comparisonItems}
              riskData={riskData}
              activeTab={activeTab}
              onRestart={handleRestart}
              setActiveTab={setActiveTab}
            />
          )}
        </main>
      </div>

      {/* FLOATING AI CHATBOT DRAWER */}
      {stage === 'dashboard' && contract && (
        <AIChatbotDrawer contractId={contract.contract_id} />
      )}
    </div>
  );
};

export default App;
