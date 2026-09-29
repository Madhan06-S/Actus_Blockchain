import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { UploadScreen } from './pages/UploadScreen';
import { ReviewTermsScreen } from './pages/ReviewTermsScreen';
import { AnalysisScreen } from './pages/AnalysisScreen';
import { DashboardScreen } from './pages/DashboardScreen';
import { AIChatbotDrawer } from './components/AIChatbotDrawer';
import type { CandidateTerms, FinancialContract, RiskStatusResponse, ComparisonItem, RiskPredictionResponse } from './types/contract';
import {
  DEMO_CANDIDATE_TERMS,
  DEMO_FINANCIAL_CONTRACT,
  DEMO_RISK_STATUS,
  DEMO_COMPARISON_ITEMS,
  generateDynamicContractData,
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
  const [riskData, setRiskData] = useState<RiskPredictionResponse | null>(null);

  // 1. Handle PDF Upload Success from Real Backend
  const handleUploadSuccess = async (docId: string, file: File) => {
    setDocumentId(docId);
    setSelectedFile(file);
    // Always reset to known-good terms first, then try to get real ones
    setTerms(DEMO_CANDIDATE_TERMS);

    try {
      const extractedTerms = await contractsApi.getExtractedTerms(docId);
      if (extractedTerms && typeof extractedTerms === 'object' && extractedTerms.principal) {
        setTerms(extractedTerms);
      }
    } catch (err) {
      console.warn('Terms extraction fallback to demo data:', err);
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
      let createdContract: FinancialContract;
      if (documentId) {
        try {
          const confirmRes = await contractsApi.confirmDocument(documentId, terms);
          createdContract = confirmRes.contract;
        } catch {
          createdContract = await contractsApi.createContract(terms);
        }
      } else {
        createdContract = await contractsApi.createContract(terms);
      }
      setContract(createdContract);

      const statusRes = await contractsApi.getStatus(createdContract.contract_id);
      const compRes = await contractsApi.getComparison(createdContract.contract_id);

      const principalNum = parseFloat(terms.principal) || 100000;
      const expectedTotalFromItems = compRes.items?.reduce((acc, it) => acc + (parseFloat(it.expected_amount) || 0), 0) || 0;

      // Ensure comparison items match the contract's principal order of magnitude
      if (compRes.items && compRes.items.length > 0 && Math.abs(expectedTotalFromItems - principalNum) < Math.max(principalNum * 0.8, 100)) {
        setStatusData(statusRes);
        setComparisonItems(compRes.items);
      } else {
        const dynamicData = generateDynamicContractData(terms, createdContract.contract_id);
        setStatusData(dynamicData.statusData);
        setComparisonItems(dynamicData.comparisonItems);
      }

      // Fetch AI Risk Prediction automatically (non-blocking fallback)
      try {
        const riskRes = await contractsApi.getRiskAnalysis(createdContract.contract_id);
        setRiskData(riskRes);
      } catch (rErr) {
        console.warn('AI Risk analysis fetch fallback:', rErr);
      }
    } catch (err) {
      console.warn('Backend status fetch fallback to dynamic calculation:', err);
      const dynamicData = generateDynamicContractData(terms);
      setContract(dynamicData.contract);
      setStatusData(dynamicData.statusData);
      setComparisonItems(dynamicData.comparisonItems);
    }
    setStage('dashboard');
  };

  // 4. Handle Live Blockchain Payment Recorded
  const handlePaymentRecorded = (updatedItems: ComparisonItem[], paidAmount: number, _txHash: string) => {
    setComparisonItems(updatedItems);
    setStatusData((prev) => {
      const currentPaid = parseFloat(prev.total_actual_paid) || 0;
      const expectedTotal = parseFloat(prev.total_expected_amount) || 0;
      const newPaid = currentPaid + paidAmount;
      const newVariance = newPaid - expectedTotal;
      const matched = prev.matched_payment_count + 1;
      const unpaid = Math.max(0, prev.unpaid_payment_count - 1);
      const isMatched = Math.abs(newVariance) < 0.01;

      return {
        ...prev,
        total_actual_paid: newPaid.toFixed(2),
        net_amount_variance: newVariance.toFixed(2),
        matched_payment_count: matched,
        unpaid_payment_count: unpaid,
        overall_status: isMatched ? 'COMPLETED' : 'DEVIATION_DETECTED',
        discrepancy_summary: isMatched
          ? 'All scheduled payments have been recorded on MST Blockchain in full compliance.'
          : `${unpaid} expected scheduled payment(s) remain pending on MST Blockchain.`,
      };
    });
  };

  // 5. Restart Workflow
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
              riskData={riskData}
              activeTab={activeTab}
              onRestart={handleRestart}
              setActiveTab={setActiveTab}
              onPaymentRecorded={handlePaymentRecorded}
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
