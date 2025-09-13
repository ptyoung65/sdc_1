'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('arthur');
  const [loading, setLoading] = useState(false);
  
  // Arthur AI state
  const [arthurRules, setArthurRules] = useState<any[]>([]);
  const [arthurLoading, setArthurLoading] = useState(false);
  const [arthurFilterType, setArthurFilterType] = useState('all');
  const [arthurFilterStatus, setArthurFilterStatus] = useState('all');
  const [arthurFilterAction, setArthurFilterAction] = useState('all');
  const [arthurSearchText, setArthurSearchText] = useState('');

  const loadArthurRules = async () => {
    try {
      setArthurLoading(true);
      const response = await axios.get('http://localhost:8009/api/v1/arthur/rules');
      setArthurRules(response.data);
    } catch (error) {
      console.error('Failed to load Arthur rules:', error);
      setArthurRules([]);
    } finally {
      setArthurLoading(false);
    }
  };

  const getFilteredArthurRules = () => {
    let filtered = [...arthurRules];
    
    if (arthurFilterType !== 'all') {
      filtered = filtered.filter(rule => rule.type === arthurFilterType);
    }
    
    if (arthurFilterStatus !== 'all') {
      filtered = filtered.filter(rule => {
        if (arthurFilterStatus === 'active') return rule.enabled === true;
        if (arthurFilterStatus === 'inactive') return rule.enabled === false;
        return true;
      });
    }
    
    if (arthurFilterAction !== 'all') {
      filtered = filtered.filter(rule => rule.action === arthurFilterAction);
    }
    
    if (arthurSearchText.trim()) {
      const searchLower = arthurSearchText.toLowerCase();
      filtered = filtered.filter(rule => 
        rule.name.toLowerCase().includes(searchLower) ||
        rule.description?.toLowerCase().includes(searchLower) ||
        rule.id.toLowerCase().includes(searchLower)
      );
    }
    
    return filtered;
  };

  useEffect(() => {
    if (activeTab === 'arthur') {
      loadArthurRules();
    }
  }, [activeTab]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-lg font-semibold">AI 가드레일 시스템</h2>
          <p className="text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-lg">🛡️</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">AI 가드레일 관리자</h1>
              <p className="text-sm text-gray-600">Arthur AI 필터 테스트</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {activeTab === 'arthur' && (
          <div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-medium text-gray-900">Arthur AI Guardrails</h3>
                <button
                  onClick={loadArthurRules}
                  disabled={arthurLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {arthurLoading ? '새로고침 중...' : '새로고침'}
                </button>
              </div>

              {/* Filter Section */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium text-gray-900">규칙 필터</h4>
                  <div className="text-sm text-gray-600">
                    총 {getFilteredArthurRules().length}개 / {arthurRules.length}개 규칙
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">검색</label>
                    <input
                      type="text"
                      value={arthurSearchText}
                      onChange={(e) => setArthurSearchText(e.target.value)}
                      placeholder="규칙 이름, 설명, ID 검색"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">타입</label>
                    <select
                      value={arthurFilterType}
                      onChange={(e) => setArthurFilterType(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="all">전체</option>
                      <option value="pii">PII</option>
                      <option value="content_filter">콘텐츠 필터</option>
                      <option value="korean_specific">한국어 특화</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">상태</label>
                    <select
                      value={arthurFilterStatus}
                      onChange={(e) => setArthurFilterStatus(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="all">전체</option>
                      <option value="active">활성</option>
                      <option value="inactive">비활성</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">액션</label>
                    <select
                      value={arthurFilterAction}
                      onChange={(e) => setArthurFilterAction(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="all">전체</option>
                      <option value="block">차단</option>
                      <option value="warn">경고</option>
                      <option value="monitor">모니터링</option>
                    </select>
                  </div>
                </div>
                
                {/* Active Filters */}
                {(arthurFilterType !== 'all' || arthurFilterStatus !== 'all' || arthurFilterAction !== 'all' || arthurSearchText.trim()) && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    <span className="text-sm font-medium text-gray-700">적용된 필터:</span>
                    {arthurFilterType !== 'all' && (
                      <span className="inline-flex items-center px-2 py-1 rounded-md bg-blue-100 text-blue-800 text-sm">
                        타입: {arthurFilterType}
                        <button
                          onClick={() => setArthurFilterType('all')}
                          className="ml-1 text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    )}
                    {arthurFilterStatus !== 'all' && (
                      <span className="inline-flex items-center px-2 py-1 rounded-md bg-green-100 text-green-800 text-sm">
                        상태: {arthurFilterStatus === 'active' ? '활성' : '비활성'}
                        <button
                          onClick={() => setArthurFilterStatus('all')}
                          className="ml-1 text-green-600 hover:text-green-800"
                        >
                          ×
                        </button>
                      </span>
                    )}
                    {arthurFilterAction !== 'all' && (
                      <span className="inline-flex items-center px-2 py-1 rounded-md bg-purple-100 text-purple-800 text-sm">
                        액션: {arthurFilterAction}
                        <button
                          onClick={() => setArthurFilterAction('all')}
                          className="ml-1 text-purple-600 hover:text-purple-800"
                        >
                          ×
                        </button>
                      </span>
                    )}
                    {arthurSearchText.trim() && (
                      <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-100 text-gray-800 text-sm">
                        검색: "{arthurSearchText}"
                        <button
                          onClick={() => setArthurSearchText('')}
                          className="ml-1 text-gray-600 hover:text-gray-800"
                        >
                          ×
                        </button>
                      </span>
                    )}
                    <button
                      onClick={() => {
                        setArthurFilterType('all');
                        setArthurFilterStatus('all');
                        setArthurFilterAction('all');
                        setArthurSearchText('');
                      }}
                      className="inline-flex items-center px-2 py-1 rounded-md bg-red-100 text-red-800 text-sm hover:bg-red-200"
                    >
                      모든 필터 제거
                    </button>
                  </div>
                )}
              </div>

              {/* Rules List */}
              <div className="space-y-4">
                {getFilteredArthurRules().length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-gray-500 mb-2">필터 조건에 맞는 규칙이 없습니다.</div>
                    <button
                      onClick={() => {
                        setArthurFilterType('all');
                        setArthurFilterStatus('all');
                        setArthurFilterAction('all');
                        setArthurSearchText('');
                      }}
                      className="text-blue-600 hover:text-blue-800 underline"
                    >
                      필터 초기화
                    </button>
                  </div>
                ) : (
                  getFilteredArthurRules().map((rule, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-3">
                          <h4 className="font-medium text-gray-900">{rule.name}</h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            rule.enabled 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {rule.enabled ? '활성' : '비활성'}
                          </span>
                          <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {rule.type}
                          </span>
                          <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            {rule.action}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">{rule.description}</p>
                      <div className="mt-2 text-xs text-gray-500">
                        ID: {rule.id} | 임계값: {rule.threshold}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}