import React, { useState } from 'react';
import { Landmark, CheckCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import type { LiquidityForecastResponse } from '../types/contract';
import { contractsApi } from '../api/contractsApi';

export const LiquidityScreen: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [liquidityData, setLiquidityData] = useState<LiquidityForecastResponse | null>(null);

  const fetchLiquidity = async () => {
    setLoading(true);
    try {
      const res = await contractsApi.getLiquidityForecast({
        bank_outflows_by_year: {
          '2027': 50000.0,
          '2028': 60000.0,
          '2029': 70000.0,
        },
      });
      setLiquidityData(res);
    } catch (err) {
      console.warn('Liquidity API fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchLiquidity();
  }, []);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
  };

  return (
    <div style={{ padding: '2rem 2.5rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* HEADER */}
      <div
        style={{
          backgroundColor: '#ffffff',
          padding: '1.5rem 2rem',
          borderRadius: '14px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.05)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.75rem', borderRadius: '10px', backgroundColor: '#f0f9ff', color: '#0284c7' }}>
            <Landmark size={28} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Portfolio Liquidity Engine
            </h2>
            <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.2rem' }}>
              Aggregate expected cash inflows across contracts vs bank outflows
            </div>
          </div>
        </div>

        <button
          onClick={fetchLiquidity}
          className="btn-secondary"
          disabled={loading}
          style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <RefreshCw size={15} />
          {loading ? 'Refreshing...' : 'Refresh Forecast'}
        </button>
      </div>

      {/* OVERALL STATUS BANNER */}
      {liquidityData && (
        <div
          style={{
            backgroundColor: liquidityData.overall_status === 'SAFE' ? '#f0fdf4' : '#fff1f2',
            border: `1px solid ${liquidityData.overall_status === 'SAFE' ? '#bbf7d0' : '#fecdd3'}`,
            borderRadius: '12px',
            padding: '1.25rem 1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {liquidityData.overall_status === 'SAFE' ? (
              <CheckCircle size={24} color="#16a34a" />
            ) : (
              <AlertTriangle size={24} color="#e11d48" />
            )}
            <div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>
                Portfolio Liquidity Status: {liquidityData.overall_status}
              </div>
              <div style={{ fontSize: '0.85rem', color: '#475569', marginTop: '0.15rem' }}>
                Forecast compiled across {liquidityData.contract_count} active contract(s)
              </div>
            </div>
          </div>

          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>
            Cumulative Net: {formatCurrency(liquidityData.total_inflow - liquidityData.total_outflow)}
          </div>
        </div>
      )}

      {/* YEARLY FORECAST TABLE */}
      {liquidityData && (
        <div className="card" style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.5rem' }}>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', marginBottom: '1.25rem' }}>
            Yearly Portfolio Cash Flow Forecast
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600, color: '#475569' }}>Year</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600, color: '#475569' }}>Portfolio Inflow</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600, color: '#475569' }}>Bank Outflow</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600, color: '#475569' }}>Net Liquidity</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600, color: '#475569' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {Object.values(liquidityData.forecast).map((item) => (
                <tr key={item.year} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '1rem', fontWeight: 700, color: '#0f172a' }}>
                    {item.year}
                  </td>
                  <td style={{ padding: '1rem', fontWeight: 700, color: '#16a34a' }}>
                    +{formatCurrency(item.portfolio_inflow)}
                  </td>
                  <td style={{ padding: '1rem', fontWeight: 700, color: '#dc2626' }}>
                    -{formatCurrency(item.bank_outflow)}
                  </td>
                  <td style={{ padding: '1rem', fontWeight: 800, color: item.net_liquidity >= 0 ? '#047857' : '#b91c1c' }}>
                    {item.net_liquidity >= 0 ? '+' : ''}{formatCurrency(item.net_liquidity)}
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <span
                      style={{
                        padding: '0.25rem 0.65rem',
                        borderRadius: '12px',
                        fontSize: '0.78rem',
                        fontWeight: 700,
                        backgroundColor: item.status === 'SAFE' ? '#ecfdf5' : '#fef2f2',
                        color: item.status === 'SAFE' ? '#047857' : '#b91c1c',
                        border: `1px solid ${item.status === 'SAFE' ? '#a7f3d0' : '#fecaca'}`,
                      }}
                    >
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
