import React from 'react';

export default function AdminBillingPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-slate-800">Billing & Usage</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-sm font-medium text-gray-500 uppercase">Total Revenue (MTD)</h3>
          <p className="text-3xl font-bold mt-2">$4,250.00</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-sm font-medium text-gray-500 uppercase">Token Usage</h3>
          <p className="text-3xl font-bold mt-2">12.5M</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-sm font-medium text-gray-500 uppercase">Active Subscriptions</h3>
          <p className="text-3xl font-bold mt-2">142</p>
        </div>
      </div>

      <h3 className="text-xl font-bold mb-4">Cost Breakdown</h3>
       <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cost</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">% of Total</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            <tr>
              <td className="px-6 py-4">LLM Inference</td>
              <td className="px-6 py-4 text-right">$2,100.00</td>
              <td className="px-6 py-4 text-right">49%</td>
            </tr>
            <tr>
              <td className="px-6 py-4">Vector Storage</td>
              <td className="px-6 py-4 text-right">$850.00</td>
              <td className="px-6 py-4 text-right">20%</td>
            </tr>
             <tr>
              <td className="px-6 py-4">Compute</td>
              <td className="px-6 py-4 text-right">$1,300.00</td>
              <td className="px-6 py-4 text-right">31%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
