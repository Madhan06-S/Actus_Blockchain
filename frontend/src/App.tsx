import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { UploadScreen } from './pages/UploadScreen';
import { ReviewTermsScreen } from './pages/ReviewTermsScreen';
import { AnalysisScreen } from './pages/AnalysisScreen';
import { DashboardScreen } from './pages/DashboardScreen';
import type { CandidateTerms, FinancialContract, RiskStatusResponse, ComparisonItem } from './types/contract';
import {
  DEMO_CANDIDATE_TERMS,
  DEMO_FINANCIAL_CONTRACT,
  DEMO_RISK_STATUS,
  DEMO_COMPARISON_ITEMS,
} from './mock/demoData';
import { contractsApi } from './api/contractsApi';

export type AppStage = 'upload' | 'review' | 'analysis' | 'dashboard';

export const App: React.FC = () => {
  const [stage, setStage] = useState<AppStage>('upload');
  const [activeTab, setActiveTab] = useState('overview');

  // Application state for contract upload and document tracking
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Workflow data state
  const [terms, setTerms] = useState<CandidateTerms>(DEMO_CANDIDATE_TERMS);
  const [contract, setContract] = useState<FinancialContract>(DEMO_FINANCIAL_CONTRACT);
  const [statusData, setStatusData] = useState<RiskStatusResponse>(DEMO_RISK_STATUS);
  const [comparisonItems, setComparisonItems] = useState<ComparisonItem[]>(DEMO_COMPARISON_ITEMS);

  // 1. Handle PDF Upload Success from Real Backend
  const handleUploadSuccess = async (docId: string, file: File) => {
    setDocumentId(docId);
    setSelectedFile(file);

    try {
      const confirmRes = await contractsApi.confirmDocument(docId);
      setTerms(confirmRes.terms);
    } catch (err) {
      console.warn('Backend candidate terms extraction fallback:', err);
      setTerms(DEMO_CANDIDATE_TERMS);
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
    try {
      const createdContract = await contractsApi.createContract(terms);
      setContract(createdContract);

      const statusRes = await contractsApi.getStatus(createdContract.contract_id);
      setStatusData(statusRes);

      const compRes = await contractsApi.getComparison(createdContract.contract_id);
      setComparisonItems(compRes.items);
    } catch (err) {
      console.warn('Backend status fetch fallback to demo dataset:', err);
      setContract(DEMO_FINANCIAL_CONTRACT);
      setStatusData(DEMO_RISK_STATUS);
      setComparisonItems(DEMO_COMPARISON_ITEMS);
    }
    setStage('dashboard');
  };

  // 4. Restart Workflow
  const handleRestart = () => {
    setDocumentId(null);
    setSelectedFile(null);
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
              onConfirm={handleConfirmTerms}
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
              activeTab={activeTab}
              onRestart={handleRestart}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
