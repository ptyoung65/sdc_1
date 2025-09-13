'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('documents');
  const [loading, setLoading] = useState(false);
  
  // Arthur AI state
  const [arthurRules, setArthurRules] = useState<any[]>([]);
  const [arthurLoading, setArthurLoading] = useState(false);
  const [arthurFilterType, setArthurFilterType] = useState('all');
  const [arthurFilterStatus, setArthurFilterStatus] = useState('all');
  const [arthurFilterAction, setArthurFilterAction] = useState('all');
  const [arthurSearchText, setArthurSearchText] = useState('');
  
  // Document management state
  const [documents, setDocuments] = useState<any[]>([]);
  const [documentLoading, setDocumentLoading] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [newDocument, setNewDocument] = useState({
    title: '',
    content: '',
    metadata: ''
  });
  const [isUploading, setIsUploading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  
  // RAG evaluation state
  const [ragMetrics, setRagMetrics] = useState<any[]>([]);
  const [ragLoading, setRagLoading] = useState(false);
  
  // Monitoring state
  const [serviceStatus, setServiceStatus] = useState<any>({});
  const [monitoringLoading, setMonitoringLoading] = useState(false);

  // Load Arthur rules from integrated backend
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
  
  // Document management functions
  const loadDocuments = async () => {
    setDocumentLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/v1/documents/default_user');
      if (response.data && response.data.documents) {
        setDocuments(response.data.documents);
      } else {
        setDocuments([]);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
      setDocuments([]);
    } finally {
      setDocumentLoading(false);
    }
  };
  
  const uploadDocument = async () => {
    if (!uploadFile) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await axios.post('http://localhost:8000/api/v1/documents', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      console.log('Upload response:', response.data);
      setUploadFile(null);
      await loadDocuments();
    } catch (error) {
      console.error('Failed to upload document:', error);
    } finally {
      setIsUploading(false);
    }
  };
  
  const deleteDocument = async (docId: string) => {
    if (!confirm('정말로 이 문서를 삭제하시겠습니까?')) return;

    try {
      await axios.delete(`http://localhost:8000/api/v1/documents/${docId}`);
      await loadDocuments();
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };
  
  const testSearch = async () => {
    setSearchLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/api/v1/search', {
        query: 'AI 기술',
        user_id: 'default_user'
      });
      console.log('Search results:', response.data);
    } catch (error) {
      console.error('Search test failed:', error);
    } finally {
      setSearchLoading(false);
    }
  };
  
  // RAG evaluation functions
  const loadRagMetrics = async () => {
    setRagLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/v1/providers');
      setRagMetrics(response.data || []);
    } catch (error) {
      console.error('Failed to load RAG metrics:', error);
      setRagMetrics([]);
    } finally {
      setRagLoading(false);
    }
  };
  
  // Monitoring functions
  const loadServiceStatus = async () => {
    setMonitoringLoading(true);
    try {
      const services = {
        backend: 'http://localhost:8000',
        arthur: 'http://localhost:8009/api/v1/arthur/rules',
        frontend: 'http://localhost:3000'
      };
      
      const statusPromises = Object.entries(services).map(async ([name, url]) => {
        try {
          const response = await axios.get(url, { timeout: 5000 });
          return { name, status: 'healthy', response_time: Date.now() };
        } catch (error) {
          return { name, status: 'unhealthy', error: error.message };
        }
      });
      
      const results = await Promise.all(statusPromises);
      const statusMap = results.reduce((acc, result) => {
        acc[result.name] = result;
        return acc;
      }, {});
      
      setServiceStatus(statusMap);
    } catch (error) {
      console.error('Failed to load service status:', error);
    } finally {
      setMonitoringLoading(false);
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
    } else if (activeTab === 'documents') {
      loadDocuments();
    } else if (activeTab === 'rag') {
      loadRagMetrics();
    } else if (activeTab === 'monitoring') {
      loadServiceStatus();
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
              <h1 className="text-xl font-bold text-gray-900">통합 관리자 패널</h1>
              <p className="text-sm text-gray-600">문서 관리, RAG 시스템, Arthur AI 가드레일 통합 관리</p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex space-x-8">
            {[
              { id: 'documents', name: '문서 관리', icon: '📚' },
              { id: 'arthur', name: 'Arthur AI', icon: '🛡️' },
              { id: 'rag', name: 'RAG 성과평가', icon: '🧠' },
              { id: 'monitoring', name: '모니터링', icon: '📈' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div>
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-6">문서 업로드</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      파일 선택
                    </label>
                    <input
                      type="file"
                      onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                      accept=".pdf,.doc,.docx,.txt,.md"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      지원 형식: PDF, DOC, DOCX, TXT, MD
                    </p>
                  </div>
                  
                  <button
                    onClick={uploadDocument}
                    disabled={!uploadFile || isUploading}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isUploading ? '업로드 중...' : '파일 업로드'}
                  </button>
                </div>

                <div className="space-y-4">
                  <button
                    onClick={testSearch}
                    disabled={searchLoading}
                    className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
                  >
                    {searchLoading ? '검색 중...' : '검색 테스트 (AI 기술)'}
                  </button>
                  
                  <button
                    onClick={loadDocuments}
                    disabled={documentLoading}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {documentLoading ? '로딩 중...' : '문서 목록 새로고침'}
                  </button>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-medium text-gray-900">문서 목록</h3>
                <div className="text-sm text-gray-500">
                  총 {documents.length}개 문서
                </div>
              </div>

              {documentLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">문서를 불러오는 중...</p>
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  업로드된 문서가 없습니다.
                </div>
              ) : (
                <div className="space-y-4">
                  {documents.map((doc, index) => (
                    <div key={index} className="border rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">{doc.title || 'Untitled'}</h4>
                          <p className="text-sm text-gray-600 mt-1">{doc.content || 'No content'}</p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                            <span>크기: {doc.size || 'N/A'}</span>
                            <span>타입: {doc.type || 'Unknown'}</span>
                            {doc.created_at && (
                              <span>생성: {new Date(doc.created_at).toLocaleString()}</span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => deleteDocument(doc.id)}
                          className="ml-4 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                        >
                          삭제
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* RAG Performance Tab */}
        {activeTab === 'rag' && (
          <div>
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-6">RAG 시스템 성과평가</h3>
              
              {ragLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">RAG 메트릭 로딩 중...</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">Multi-RAG</div>
                    <div className="text-sm text-blue-800">통합 RAG 시스템</div>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">Korean-RAG</div>
                    <div className="text-sm text-green-800">한국어 특화 RAG</div>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">Docling</div>
                    <div className="text-sm text-purple-800">문서 처리 시스템</div>
                  </div>
                </div>
              )}
              
              <div className="mt-6">
                <h4 className="text-md font-medium text-gray-700 mb-3">AI 제공자 목록</h4>
                <div className="space-y-2">
                  {ragMetrics.map((provider, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="font-medium">{provider.name || `Provider ${index + 1}`}</div>
                      <div className="text-sm text-gray-600">{provider.description || '설명 없음'}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Monitoring Tab */}
        {activeTab === 'monitoring' && (
          <div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-medium text-gray-900">서비스 모니터링</h3>
                <button
                  onClick={loadServiceStatus}
                  disabled={monitoringLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {monitoringLoading ? '확인 중...' : '상태 새로고침'}
                </button>
              </div>
              
              {monitoringLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">서비스 상태 확인 중...</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(serviceStatus).map(([name, status]: [string, any]) => (
                    <div key={name} className={`p-4 rounded-lg border-2 ${
                      status.status === 'healthy' 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-red-50 border-red-200'
                    }`}>
                      <div className="flex items-center justify-between">
                        <div className="font-medium text-gray-900">
                          {name.toUpperCase()}
                        </div>
                        <div className={`text-sm px-2 py-1 rounded ${
                          status.status === 'healthy'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {status.status === 'healthy' ? '정상' : '오류'}
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-600 mt-2">
                        {status.status === 'healthy' 
                          ? '서비스가 정상 작동 중입니다'
                          : `오류: ${status.error || '알 수 없는 오류'}`
                        }
                      </div>
                      
                      {status.response_time && (
                        <div className="text-xs text-gray-500 mt-1">
                          응답 시간: {status.response_time}ms
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Arthur AI Tab */}
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