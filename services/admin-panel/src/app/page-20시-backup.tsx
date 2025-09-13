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

  // Other admin tabs state
  const [documents, setDocuments] = useState<any[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentLoading, setDocumentLoading] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [rbacLoading, setRbacLoading] = useState(false);
  const [ragMetrics, setRagMetrics] = useState<any[]>([]);
  const [monitoringData, setMonitoringData] = useState<any>({});
  const [statistics, setStatistics] = useState<any>({});

  // Document management specific state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [newDocument, setNewDocument] = useState({
    title: '',
    content: '',
    metadata: ''
  });
  const [isUploading, setIsUploading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);

  // Rules management state
  const [rules, setRules] = useState<any[]>([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [showAddRuleModal, setShowAddRuleModal] = useState(false);
  const [newRule, setNewRule] = useState({
    name: '',
    type: 'content_filter',
    threshold: 0.7,
    action: 'block',
    description: '',
    patterns: ['']
  });

  // Tab definitions
  const tabs = [
    { id: 'arthur', name: 'Arthur AI', icon: '🛡️' },
    { id: 'rules', name: '규칙관리', icon: '⚙️' },
    { id: 'realtime', name: '실시간테스트', icon: '🔍' },
    { id: 'documents', name: '문서관리', icon: '📄' },
    { id: 'rbac', name: 'RBAC설정', icon: '👥' },
    { id: 'rag', name: 'RAG성과평가', icon: '📊' },
    { id: 'monitoring', name: '모니터링', icon: '📈' },
    { id: 'statistics', name: '통계', icon: '📋' }
  ];

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

  // Load functions for other tabs
  const loadRules = async () => {
    try {
      setRulesLoading(true);
      const response = await axios.get('http://localhost:8001/api/v1/rules');
      setRules(response.data);
    } catch (error) {
      console.error('Failed to load rules:', error);
      setRules([]);
    } finally {
      setRulesLoading(false);
    }
  };

  const loadDocuments = async () => {
    setDocumentLoading(true);
    try {
      // Call main backend API at port 8000
      const response = await axios.get('http://localhost:8000/api/v1/documents/default_user');
      console.log('Document API Response:', response.data);
      
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

  const loadUsers = async () => {
    try {
      setRbacLoading(true);
      const response = await axios.get('http://localhost:8005/api/v1/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
      setUsers([]);
    } finally {
      setRbacLoading(false);
    }
  };

  const createRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:8001/api/v1/rules', newRule);
      setRules([...rules, response.data]);
      setNewRule({
        name: '',
        type: 'content_filter',
        threshold: 0.7,
        action: 'block',
        description: '',
        patterns: ['']
      });
      setShowAddRuleModal(false);
    } catch (error) {
      console.error('Failed to create rule:', error);
    }
  };

  const uploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!uploadFile) {
      alert('업로드할 파일을 선택해주세요.');
      return;
    }

    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('title', newDocument.title || uploadFile.name);
      
      if (newDocument.metadata.trim()) {
        formData.append('metadata', newDocument.metadata);
      }

      const response = await axios.post('http://localhost:8009/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        alert(`파일이 성공적으로 업로드되었습니다: ${response.data.data.chunks_created}개 청크 생성`);
        
        // Reset form
        setUploadFile(null);
        setNewDocument({ title: '', content: '', metadata: '' });
        
        // Reload documents list
        await loadDocuments();
        
        // Reset file input
        const fileInput = document.getElementById('file-input') as HTMLInputElement;
        if (fileInput) {
          fileInput.value = '';
        }
      } else {
        alert(`업로드 실패: ${response.data.message || '알 수 없는 오류'}`);
      }
    } catch (error: any) {
      console.error('Failed to upload document:', error);
      alert(`업로드 중 오류가 발생했습니다: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const createDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newDocument.title.trim() || !newDocument.content.trim()) {
      alert('제목과 내용을 모두 입력해주세요.');
      return;
    }

    setIsUploading(true);
    
    try {
      let metadata = {};
      if (newDocument.metadata.trim()) {
        try {
          metadata = JSON.parse(newDocument.metadata);
        } catch (error) {
          alert('메타데이터는 올바른 JSON 형식이어야 합니다.');
          setIsUploading(false);
          return;
        }
      }

      const response = await axios.post('http://localhost:8009/documents/create', {
        title: newDocument.title.trim(),
        content: newDocument.content.trim(),
        metadata: metadata
      });

      if (response.data.success) {
        alert(`문서가 성공적으로 생성되었습니다: ${response.data.data.chunks_created}개 청크 생성`);
        
        // Reset form
        setNewDocument({ title: '', content: '', metadata: '' });
        
        // Reload documents list
        await loadDocuments();
      } else {
        alert(`문서 생성 실패: ${response.data.message || '알 수 없는 오류'}`);
      }
    } catch (error: any) {
      console.error('Failed to create document:', error);
      alert(`문서 생성 중 오류가 발생했습니다: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const deleteDocument = async (documentId: string) => {
    if (!confirm('정말로 이 문서를 삭제하시겠습니까?')) {
      return;
    }

    try {
      const response = await axios.delete(`http://localhost:8009/documents/${documentId}`);
      
      if (response.data.success) {
        alert('문서가 성공적으로 삭제되었습니다.');
        await loadDocuments();
      } else {
        alert(`문서 삭제 실패: ${response.data.message || '알 수 없는 오류'}`);
      }
    } catch (error: any) {
      console.error('Failed to delete document:', error);
      alert(`문서 삭제 중 오류가 발생했습니다: ${error.response?.data?.detail || error.message}`);
    }
  };

  const testSearch = async (query: string) => {
    if (!query.trim()) {
      alert('검색할 질문을 입력해주세요.');
      return;
    }

    setSearchLoading(true);
    
    try {
      const response = await axios.post('http://localhost:8009/search', {
        query: query.trim(),
        top_k: 5
      });

      if (response.data.success && response.data.data.results) {
        const results = response.data.data.results;
        alert(`검색 완료!\n찾은 문서 청크: ${results.length}개\n\n` +
              results.map((r: any, i: number) => 
                `${i+1}. 유사도: ${r.score.toFixed(3)}\n내용: ${r.content.substring(0, 100)}...`
              ).join('\n\n'));
      } else {
        alert('검색 결과가 없습니다.');
      }
    } catch (error: any) {
      console.error('Search failed:', error);
      alert(`검색 중 오류가 발생했습니다: ${error.response?.data?.detail || error.message}`);
    } finally {
      setSearchLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'rules') {
      loadRules();
    } else if (activeTab === 'documents') {
      loadDocuments();
    } else if (activeTab === 'rbac') {
      loadUsers();
    }
  }, [activeTab]);

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

      {/* Tab Navigation */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                aria-current={activeTab === tab.id ? 'page' : undefined}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
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

        {/* Rules Management Tab */}
        {activeTab === 'rules' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">⚙️ 규칙 관리</h2>
                <button
                  onClick={() => setShowAddRuleModal(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  새 규칙 추가
                </button>
              </div>
              
              {rulesLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">규칙을 불러오는 중...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {rules.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-gray-500">등록된 규칙이 없습니다.</p>
                    </div>
                  ) : (
                    rules.map((rule, index) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{rule.name}</h4>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              rule.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {rule.enabled ? '활성' : '비활성'}
                            </span>
                            <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {rule.type}
                            </span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{rule.description}</p>
                        <div className="text-xs text-gray-500">
                          임계값: {rule.threshold} | 액션: {rule.action}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Add Rule Modal */}
            {showAddRuleModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">새 규칙 추가</h3>
                  <form onSubmit={createRule} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">규칙 이름</label>
                        <input
                          type="text"
                          value={newRule.name}
                          onChange={(e) => setNewRule({...newRule, name: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">타입</label>
                        <select
                          value={newRule.type}
                          onChange={(e) => setNewRule({...newRule, type: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="content_filter">콘텐츠 필터</option>
                          <option value="pii">개인정보</option>
                          <option value="security">보안</option>
                          <option value="compliance">컴플라이언스</option>
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">설명</label>
                      <textarea
                        value={newRule.description}
                        onChange={(e) => setNewRule({...newRule, description: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        rows={3}
                      />
                    </div>
                    <div className="flex items-center justify-end space-x-3">
                      <button
                        type="button"
                        onClick={() => setShowAddRuleModal(false)}
                        className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                      >
                        취소
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                      >
                        추가
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Real-time Testing Tab */}
        {activeTab === 'realtime' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-6">🔍 실시간 AI 테스트</h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-md font-medium text-gray-900">가드레일 테스트</h3>
                  <div className="space-y-3">
                    <textarea
                      placeholder="테스트할 텍스트를 입력하세요..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      rows={4}
                    />
                    <div className="flex items-center space-x-3">
                      <select className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                        <option value="all">모든 규칙</option>
                        <option value="pii">개인정보 탐지</option>
                        <option value="content_filter">콘텐츠 필터</option>
                        <option value="korean_specific">한국어 특화</option>
                      </select>
                      <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                        테스트 실행
                      </button>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-md font-medium text-gray-900">테스트 결과</h3>
                  <div className="bg-gray-50 rounded-lg p-4 min-h-[200px]">
                    <div className="text-center text-gray-500 mt-16">
                      테스트를 실행하여 결과를 확인하세요
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-md font-medium text-gray-900 mb-4">성능 지표</h3>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">-</div>
                  <div className="text-sm text-gray-600">평균 응답시간</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">-</div>
                  <div className="text-sm text-gray-600">성공률</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">-</div>
                  <div className="text-sm text-gray-600">차단된 콘텐츠</div>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">-</div>
                  <div className="text-sm text-gray-600">오탐지율</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Documents Management Tab */}
        {activeTab === 'documents' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">📚 RAG 문서 관리</h2>
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={loadDocuments}
                      disabled={documentLoading}
                      className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 disabled:bg-gray-400 text-sm"
                    >
                      {documentLoading ? '로딩 중...' : '🔄 새로고침'}
                    </button>
                    <span className="text-sm text-gray-500">Korean RAG Service: localhost:8009</span>
                  </div>
                </div>
              </div>

              <div className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                  {/* File Upload Section */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium mb-3 flex items-center">
                      📁 다중 형식 파일 업로드
                      <span className="ml-2 text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">PDF•DOC•PPT•XLS•TXT</span>
                    </h3>
                    <form onSubmit={uploadDocument} className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">파일 선택</label>
                        <input
                          id="file-input"
                          type="file"
                          accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.md"
                          onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        />
                        <div className="text-xs text-gray-500 mt-1">
                          지원 형식: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, TXT, MD (최대 50MB)
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">제목 (선택사항)</label>
                        <input
                          type="text"
                          placeholder="파일명을 기본으로 사용"
                          value={newDocument.title}
                          onChange={(e) => setNewDocument({...newDocument, title: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">메타데이터 (JSON, 선택사항)</label>
                        <textarea
                          rows={2}
                          placeholder='{"category": "manual", "department": "IT"}'
                          value={newDocument.metadata}
                          onChange={(e) => setNewDocument({...newDocument, metadata: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={!uploadFile || isUploading}
                        className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 text-sm"
                      >
                        {isUploading ? '업로드 중...' : '📤 파일 업로드'}
                      </button>
                    </form>
                  </div>

                  {/* Manual Document Creation Section */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium mb-3 flex items-center">
                      ✏️ 직접 입력
                    </h3>
                    <form onSubmit={createDocument} className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">문서 제목</label>
                        <input
                          type="text"
                          placeholder="문서 제목을 입력하세요"
                          value={newDocument.title}
                          onChange={(e) => setNewDocument({...newDocument, title: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">문서 내용</label>
                        <textarea
                          rows={4}
                          placeholder="문서 내용을 입력하세요..."
                          value={newDocument.content}
                          onChange={(e) => setNewDocument({...newDocument, content: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">메타데이터 (JSON, 선택사항)</label>
                        <textarea
                          rows={2}
                          placeholder='{"category": "policy", "author": "admin"}'
                          value={newDocument.metadata}
                          onChange={(e) => setNewDocument({...newDocument, metadata: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={!newDocument.title.trim() || !newDocument.content.trim() || isUploading}
                        className="w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400 text-sm"
                      >
                        {isUploading ? '추가 중...' : '📝 문서 추가'}
                      </button>
                    </form>
                  </div>
                </div>

                {/* Search Test Section */}
                <div className="bg-blue-50 rounded-lg p-4 mb-6">
                  <h3 className="font-medium mb-3 flex items-center">
                    🔍 검색 테스트
                  </h3>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      placeholder="검색할 질문을 입력하세요 (예: 인공지능이란 무엇인가요?)"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          testSearch((e.target as HTMLInputElement).value);
                        }
                      }}
                    />
                    <button
                      onClick={() => {
                        const input = document.querySelector('input[placeholder*="검색할 질문"]') as HTMLInputElement;
                        if (input) testSearch(input.value);
                      }}
                      disabled={searchLoading}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
                    >
                      {searchLoading ? '🔍 검색 중...' : '🚀 검색'}
                    </button>
                  </div>
                  <div className="text-xs text-gray-600 mt-2">
                    벡터 유사도 검색을 통해 관련 문서 청크를 찾아 컨텍스트로 제공합니다.
                  </div>
                </div>

                {/* Document Statistics */}
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <h3 className="font-medium mb-3">📊 문서 현황</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div className="bg-white rounded-lg p-3">
                      <div className="text-2xl font-bold text-blue-600">{documents.length}</div>
                      <div className="text-xs text-gray-600">총 문서</div>
                    </div>
                    <div className="bg-white rounded-lg p-3">
                      <div className="text-2xl font-bold text-green-600">
                        {documents.filter(doc => doc.processing_status === 'completed').length}
                      </div>
                      <div className="text-xs text-gray-600">처리 완료</div>
                    </div>
                    <div className="bg-white rounded-lg p-3">
                      <div className="text-2xl font-bold text-orange-600">
                        {documents.reduce((sum, doc) => sum + (doc.chunks || 0), 0)}
                      </div>
                      <div className="text-xs text-gray-600">총 청크</div>
                    </div>
                    <div className="bg-white rounded-lg p-3">
                      <div className="text-2xl font-bold text-purple-600">
                        {Math.round(documents.reduce((sum, doc) => sum + (doc.size || 0), 0) / 1024)}KB
                      </div>
                      <div className="text-xs text-gray-600">총 크기</div>
                    </div>
                  </div>
                </div>

                {/* Document List */}
                <div className="bg-white rounded-lg border">
                  <div className="px-4 py-3 border-b bg-gray-50">
                    <h3 className="font-medium">문서 목록</h3>
                  </div>
                  <div className="p-4">
                    {documentLoading ? (
                      <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                        <p className="mt-2 text-gray-600">문서를 불러오는 중...</p>
                      </div>
                    ) : documents.length === 0 ? (
                      <div className="text-center py-8">
                        <div className="text-4xl mb-4">📄</div>
                        <p className="text-gray-500">업로드된 문서가 없습니다.</p>
                        <p className="text-sm text-gray-400 mt-2">위에서 파일을 업로드하거나 직접 입력해 보세요.</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {documents.map((doc, index) => (
                          <div key={index} className="border rounded-lg p-4 hover:bg-gray-50">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium text-gray-900">{doc.title || doc.filename}</h4>
                              <div className="flex items-center space-x-2">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  doc.processing_status === 'completed' ? 'bg-green-100 text-green-800' :
                                  doc.processing_status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                                  doc.processing_status === 'failed' ? 'bg-red-100 text-red-800' :
                                  'bg-blue-100 text-blue-800'
                                }`}>
                                  {doc.processing_status === 'completed' ? '처리완료' :
                                   doc.processing_status === 'processing' ? '처리중' :
                                   doc.processing_status === 'failed' ? '처리실패' : '대기중'}
                                </span>
                                {doc.id && (
                                  <button
                                    onClick={() => deleteDocument(doc.id)}
                                    className="text-red-600 hover:text-red-800 text-sm"
                                    title="문서 삭제"
                                  >
                                    🗑️
                                  </button>
                                )}
                              </div>
                            </div>
                            <div className="text-sm text-gray-600">
                              {doc.size && <div>크기: {Math.round(doc.size / 1024)}KB</div>}
                              {doc.chunks && <div>청크: {doc.chunks}개</div>}
                              {doc.created_at && <div>생성: {new Date(doc.created_at).toLocaleString('ko-KR')}</div>}
                              {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                                <div className="mt-1">
                                  <span className="text-xs text-gray-500">메타데이터: </span>
                                  <span className="text-xs bg-gray-100 px-1 rounded">{JSON.stringify(doc.metadata)}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* RBAC Settings Tab */}
        {activeTab === 'rbac' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">RBAC 권한 관리</h2>
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={loadUsers}
                      disabled={rbacLoading}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                    >
                      {rbacLoading ? '새로고침 중...' : '새로고침'}
                    </button>
                  </div>
                </div>
              </div>

              <div className="p-6">
                {rbacLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-2 text-gray-600">사용자 정보를 불러오는 중...</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                        <div>
                          <div className="text-2xl font-bold text-blue-600">{users.length}</div>
                          <div className="text-sm text-gray-600">총 사용자</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-green-600">
                            {users.filter(user => user.is_active).length}
                          </div>
                          <div className="text-sm text-gray-600">활성 사용자</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-purple-600">
                            {new Set(users.flatMap(user => user.roles || [])).size}
                          </div>
                          <div className="text-sm text-gray-600">총 역할</div>
                        </div>
                      </div>
                    </div>

                    {users.length === 0 ? (
                      <div className="text-center py-8">
                        <div className="text-4xl mb-4">👥</div>
                        <p className="text-gray-500">등록된 사용자가 없습니다.</p>
                        <p className="text-sm text-gray-400 mt-2">RBAC 서비스가 실행 중인지 확인해주세요.</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <h3 className="text-lg font-medium text-gray-900">사용자 목록</h3>
                        <div className="space-y-3">
                          {users.map((user, index) => (
                            <div key={index} className="border rounded-lg p-4 hover:bg-gray-50">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center space-x-3">
                                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                    <span className="text-sm font-medium text-blue-600">
                                      {user.full_name ? user.full_name.charAt(0) : user.username?.charAt(0)}
                                    </span>
                                  </div>
                                  <div>
                                    <h4 className="font-medium text-gray-900">
                                      {user.full_name || user.username}
                                    </h4>
                                    <p className="text-sm text-gray-500">{user.email}</p>
                                  </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                    user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                  }`}>
                                    {user.is_active ? '활성' : '비활성'}
                                  </span>
                                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                    {user.clearance_level || 'N/A'}
                                  </span>
                                </div>
                              </div>
                              <div className="text-sm text-gray-600">
                                <div className="flex items-center space-x-4">
                                  <div>부서: {user.department || 'N/A'}</div>
                                  <div>직책: {user.job_title || 'N/A'}</div>
                                </div>
                                {user.roles && user.roles.length > 0 && (
                                  <div className="mt-2">
                                    <span className="text-xs text-gray-500">역할: </span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {user.roles.map((role, roleIndex) => (
                                        <span key={roleIndex} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                          {role}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* RAG Performance Tab */}
        {activeTab === 'rag' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-6">📊 RAG 성과 평가</h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">85.2%</div>
                  <div className="text-sm text-gray-600">컨텍스트 관련성</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-3xl font-bold text-green-600">92.1%</div>
                  <div className="text-sm text-gray-600">답변 정확도</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-3xl font-bold text-purple-600">78.9%</div>
                  <div className="text-sm text-gray-600">충실도</div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-md font-medium text-gray-900">최근 성능 지표</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">평균 응답시간</span>
                      <span className="font-medium">1.2초</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">검색 정확도</span>
                      <span className="font-medium">89.5%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">환각 발생률</span>
                      <span className="font-medium">3.2%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">사용자 만족도</span>
                      <span className="font-medium">4.3/5.0</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-md font-medium text-gray-900">시간별 성능 추이</h3>
                  <div className="bg-gray-50 rounded-lg p-4 h-48 flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <div className="text-2xl mb-2">📈</div>
                      <div>차트 데이터 로딩 중...</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-md font-medium text-gray-900 mb-4">최근 평가 결과</h3>
              <div className="space-y-3">
                <div className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">2025-09-07 15:30</span>
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">Good</span>
                  </div>
                  <div className="text-xs text-gray-600">평균 점수: 87.3% | 쿼리: 15개 | 응답시간: 1.1초</div>
                </div>
                <div className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">2025-09-07 14:45</span>
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs">Fair</span>
                  </div>
                  <div className="text-xs text-gray-600">평균 점수: 76.8% | 쿼리: 22개 | 응답시간: 1.5초</div>
                </div>
                <div className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">2025-09-07 13:20</span>
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">Excellent</span>
                  </div>
                  <div className="text-xs text-gray-600">평균 점수: 93.1% | 쿼리: 8개 | 응답시간: 0.9초</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Monitoring Tab */}
        {activeTab === 'monitoring' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-6">📈 시스템 모니터링</h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">99.8%</div>
                  <div className="text-sm text-gray-600">시스템 가용성</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">245ms</div>
                  <div className="text-sm text-gray-600">평균 응답시간</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">1,847</div>
                  <div className="text-sm text-gray-600">활성 세션</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">23.4GB</div>
                  <div className="text-sm text-gray-600">메모리 사용량</div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-md font-medium text-gray-900">서비스 상태</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span className="text-sm font-medium">Backend API</span>
                      </div>
                      <span className="text-xs text-green-600">정상</span>
                    </div>
                    <div className="flex justify-between items-center p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span className="text-sm font-medium">Arthur AI Service</span>
                      </div>
                      <span className="text-xs text-green-600">정상</span>
                    </div>
                    <div className="flex justify-between items-center p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                        <span className="text-sm font-medium">RBAC Service</span>
                      </div>
                      <span className="text-xs text-yellow-600">경고</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-md font-medium text-gray-900">리소스 사용률</h3>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-gray-600">CPU</span>
                        <span className="text-sm font-medium">67%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full" style={{width: '67%'}}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-gray-600">메모리</span>
                        <span className="text-sm font-medium">45%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-green-600 h-2 rounded-full" style={{width: '45%'}}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-gray-600">디스크</span>
                        <span className="text-sm font-medium">28%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-yellow-600 h-2 rounded-full" style={{width: '28%'}}></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Statistics Tab */}
        {activeTab === 'statistics' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-6">📋 사용 통계</h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">15,642</div>
                  <div className="text-sm text-gray-600">총 쿼리 수</div>
                  <div className="text-xs text-gray-500 mt-1">+12% vs 지난주</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-3xl font-bold text-green-600">2,847</div>
                  <div className="text-sm text-gray-600">활성 사용자</div>
                  <div className="text-xs text-gray-500 mt-1">+8% vs 지난주</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-3xl font-bold text-purple-600">456</div>
                  <div className="text-sm text-gray-600">처리된 문서</div>
                  <div className="text-xs text-gray-500 mt-1">+23% vs 지난주</div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-md font-medium text-gray-900">인기 기능</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">문서 검색</span>
                      <span className="font-medium">67%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">AI 질의응답</span>
                      <span className="font-medium">23%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">문서 업로드</span>
                      <span className="font-medium">10%</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-md font-medium text-gray-900">시간대별 사용량</h3>
                  <div className="bg-gray-50 rounded-lg p-4 h-32 flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <div className="text-xl mb-1">📊</div>
                      <div className="text-sm">차트 로딩 중...</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-md font-medium text-gray-900 mb-4">최근 활동 로그</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                  <span className="text-gray-600">사용자 "admin"이 새로운 규칙을 추가했습니다</span>
                  <span className="text-xs text-gray-400">2분 전</span>
                </div>
                <div className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                  <span className="text-gray-600">"project-report.pdf" 문서가 처리되었습니다</span>
                  <span className="text-xs text-gray-400">5분 전</span>
                </div>
                <div className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                  <span className="text-gray-600">시스템 백업이 완료되었습니다</span>
                  <span className="text-xs text-gray-400">1시간 전</span>
                </div>
                <div className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                  <span className="text-gray-600">RAG 성능 평가가 완료되었습니다</span>
                  <span className="text-xs text-gray-400">2시간 전</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}