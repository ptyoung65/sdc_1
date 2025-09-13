'use client';

import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import dynamic from 'next/dynamic';

// Dynamically import charts to avoid SSR issues
const TimeSeriesChart = dynamic(() => import('../components/charts/TimeSeriesChart'), {
  ssr: false,
  loading: () => <div className="animate-pulse bg-gray-200 rounded h-64">차트 로딩 중...</div>
});

const DonutChart = dynamic(() => import('../components/charts/DonutChart'), {
  ssr: false,
  loading: () => <div className="animate-pulse bg-gray-200 rounded h-64">차트 로딩 중...</div>
});

const BarChart = dynamic(() => import('../components/charts/BarChart'), {
  ssr: false,
  loading: () => <div className="animate-pulse bg-gray-200 rounded h-64">차트 로딩 중...</div>
});

interface GuardrailRule {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  threshold: number;
  action: string;
  created_at?: string;
  updated_at?: string;
  patterns?: string[];
  examples?: string[];
}

interface GuardrailStats {
  total_checks: number;
  blocked_content: number;
  flagged_content: number;
  modified_content: number;
  success_rate: number;
  average_response_time_ms: number;
  top_violations: Array<{ rule: string; count: number }>;
}

interface RBACUser {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  department: string;
  job_title?: string;
  clearance_level: string;
  roles: string[];
  is_active: boolean;
  project_access: string[];
  attributes: any;
  created_at: string;
}

interface RBACRole {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  created_at: string;
}

interface RBACPolicy {
  id: string;
  name: string;
  description: string;
  rules: any;
  is_active: boolean;
  created_at: string;
}

interface RAGMetrics {
  context_relevance: number;
  answer_relevance: number;
  faithfulness: number;
  answer_correctness: number;
  hallucination_rate: number;
  overall_quality_score: number;
  total_latency_ms: number;
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  session_id: string;
  query: string;
  timestamp: string;
}

interface RAGAggregatedMetrics {
  period: string;
  start_time: string;
  end_time: string;
  total_queries: number;
  avg_context_relevance: number;
  avg_context_sufficiency: number;
  avg_answer_relevance: number;
  avg_answer_correctness: number;
  avg_hallucination_rate: number;
  avg_retrieval_latency_ms: number;
  avg_generation_latency_ms: number;
  avg_total_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  throughput_per_second: number;
  avg_quality_score: number;
  quality_distribution: {
    excellent: number;
    good: number;
    fair: number;
    poor: number;
  };
}

interface RAGRealtimeMetrics {
  timestamp: string;
  current_throughput: number;
  avg_latency_1min: number;
  active_sessions: number;
  success_rate: number;
  recent_quality_scores: number[];
  status: string;
}

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('rules');
  const [rules, setRules] = useState<GuardrailRule[]>([]);
  const [stats, setStats] = useState<GuardrailStats | null>(null);
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [isTestLoading, setIsTestLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // RBAC state
  const [rbacActiveTab, setRbacActiveTab] = useState('users');
  const [users, setUsers] = useState<RBACUser[]>([]);
  const [roles, setRoles] = useState<RBACRole[]>([]);
  const [policies, setPolicies] = useState<RBACPolicy[]>([]);
  const [rbacLoading, setRbacLoading] = useState(false);
  
  // New policy state
  const [newPolicy, setNewPolicy] = useState({
    name: '',
    description: '',
    rules: '',
    is_active: true
  });

  // New user state
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    department: '',
    job_title: '',
    clearance_level: 'internal'
  });

  // New role state
  const [newRole, setNewRole] = useState({
    name: '',
    description: '',
    permissions: [] as string[]
  });

  // RAG evaluation state
  const [ragMetrics, setRagMetrics] = useState<RAGMetrics[]>([]);
  const [ragRealtime, setRagRealtime] = useState<RAGRealtimeMetrics | null>(null);
  const [ragAggregated, setRagAggregated] = useState<RAGAggregatedMetrics | null>(null);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragPeriod, setRagPeriod] = useState('24h');
  
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
  
  // Document modals state
  const [showDetailModal, setShowDetailModal] = useState(false);
  
  // Arthur AI Guardrails state
  const [arthurRules, setArthurRules] = useState<any[]>([]);
  const [arthurMetrics, setArthurMetrics] = useState<any>(null);
  const [arthurInfo, setArthurInfo] = useState<any>(null);
  const [arthurLoading, setArthurLoading] = useState(false);
  const [arthurTestText, setArthurTestText] = useState('');
  const [arthurTestResult, setArthurTestResult] = useState<any>(null);
  const [arthurTestLoading, setArthurTestLoading] = useState(false);
  
  // Arthur AI 규칙 관리 상태
  const [showArthurRuleForm, setShowArthurRuleForm] = useState(false);
  const [editingArthurRule, setEditingArthurRule] = useState<any>(null);
  const [newArthurRule, setNewArthurRule] = useState({
    name: '',
    type: 'toxicity',
    description: '',
    threshold: 0.8,
    action: 'block',
    custom_patterns: [''],
    examples: ['']
  });
  
  // Arthur AI 필터 상태
  const [arthurFilterType, setArthurFilterType] = useState('all');
  const [arthurFilterStatus, setArthurFilterStatus] = useState('all');
  const [arthurFilterAction, setArthurFilterAction] = useState('all');
  const [arthurSearchText, setArthurSearchText] = useState('');
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [showChunkModal, setShowChunkModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const [documentContent, setDocumentContent] = useState('');
  
  // Search result modal state
  const [showSearchResultModal, setShowSearchResultModal] = useState(false);
  const [searchResultData, setSearchResultData] = useState<any>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  
  // Rule filter and detail state
  const [ruleFilter, setRuleFilter] = useState('all');
  const [ruleSearchQuery, setRuleSearchQuery] = useState('');
  const [selectedRule, setSelectedRule] = useState<GuardrailRule | null>(null);
  const [showRuleDetailModal, setShowRuleDetailModal] = useState(false);
  const [editingRule, setEditingRule] = useState<GuardrailRule | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<any>(null);
  const [documentChunks, setDocumentChunks] = useState<any[]>([]);
  const [chunksLoading, setChunksLoading] = useState(false);

  // 규칙 상세 정보 매핑 함수 (useMemo 이전에 정의)
  const getRuleDetails = (ruleName: string) => {
    const ruleDetailsMap: { [key: string]: { description: string; patterns: string[]; examples: string[]; risk_level: string } } = {
      '욕설 및 비속어 차단': {
        description: '욕설, 비속어, 속어 등 부적절한 언어를 감지하고 차단합니다.',
        patterns: [
          'regex: (씨발|시발|씨팔|ㅅㅂ|ㅆㅂ)',
          'regex: (개새끼|개쉑|개색|ㄱㅅㄲ)',
          'regex: (병신|븅신|ㅂㅅ)',
          'keyword: 욕설_사전_DB',
          'ai_model: toxicity_classifier'
        ],
        examples: [
          '이런 ㅅㅂ 일이 왜 자꾸...',
          '그 새ㄲ가 또 그랬어',
          '진짜 ㅂㅅ같은 결정이네'
        ],
        risk_level: 'high'
      },
      '인신공격 방지': {
        description: '특정 개인이나 집단에 대한 인신공격성 발언을 탐지합니다.',
        patterns: [
          'regex: (너|당신|네놈|니놈).*(무능|멍청|바보|한심)',
          'regex: (팀|부서|회사).*(쓰레기|무능|최악)',
          'context: personal_attack_detector',
          'sentiment: negative + target_person'
        ],
        examples: [
          '너 같은 무능한 사람은 회사 그만둬야 해',
          '영업팀 놈들은 다 쓸모없어',
          '김 과장님은 정말 한심한 사람이야'
        ],
        risk_level: 'medium'
      },
      '주민등록번호 노출 방지': {
        description: '주민등록번호 형식의 데이터를 감지하고 차단합니다.',
        patterns: [
          'regex: \\d{6}-[1-4]\\d{6}',
          'regex: \\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\\d|3[01])-[1-4]\\d{6}',
          'format: YYMMDD-GXXXXXX',
          'validator: korean_rrn_checksum'
        ],
        examples: [
          '990101-1234567',
          '홍길동 주민번호: 850315-1******',
          '등록번호 771225-2341234 입니다'
        ],
        risk_level: 'critical'
      },
      '회사 기밀정보 누출 방지': {
        description: '회사 내부 기밀 정보, 영업 비밀 등의 유출을 방지합니다.',
        patterns: ['매출 정보', '고객 데이터', '사업 전략', '기술 문서'],
        examples: ['2024년 매출 목표', '주요 고객사 리스트'],
        risk_level: 'critical'
      },
      '성별 편견 방지': {
        description: '성별에 대한 고정관념이나 차별적 표현을 감지합니다.',
        patterns: ['성별 고정관념', '성차별적 표현'],
        examples: ['"여자라서..."', '"남자답게..."'],
        risk_level: 'medium'
      }
    };
    return ruleDetailsMap[ruleName] || {
      description: '규칙에 대한 상세 설명',
      patterns: ['패턴 정보'],
      examples: ['예시'],
      risk_level: 'medium'
    };
  };

  // Computed rule details for the selected rule
  const ruleDetails = useMemo(() => {
    return selectedRule ? getRuleDetails(selectedRule.name) : null;
  }, [selectedRule]);

  // Policy templates
  const policyTemplates = {
    basicAccess: {
      name: '기본 접근 권한',
      rules: JSON.stringify({
        resource: "*",
        action: "read",
        condition: {
          department: "all"
        }
      }, null, 2)
    },
    adminAccess: {
      name: '관리자 접근 권한',
      rules: JSON.stringify({
        resource: "*",
        action: ["create", "read", "update", "delete"],
        condition: {
          role: "admin",
          ip_range: ["192.168.1.0/24"]
        }
      }, null, 2)
    },
    departmentAccess: {
      name: '부서별 접근 권한',
      rules: JSON.stringify({
        resource: "/api/department/*",
        action: ["read", "update"],
        condition: {
          department: "${user.department}",
          time_range: {
            start: "09:00",
            end: "18:00"
          }
        }
      }, null, 2)
    },
    fileAccess: {
      name: '파일 접근 권한',
      rules: JSON.stringify({
        resource: "/files/${user.id}/*",
        action: ["read", "write"],
        condition: {
          file_type: ["pdf", "doc", "txt"],
          max_size: "10MB"
        }
      }, null, 2)
    },
    apiAccess: {
      name: 'API 호출 제한',
      rules: JSON.stringify({
        resource: "/api/*",
        action: "*",
        condition: {
          rate_limit: {
            requests: 100,
            per: "hour"
          },
          auth_required: true
        }
      }, null, 2)
    }
  };

  const applyTemplate = (templateKey: keyof typeof policyTemplates) => {
    const template = policyTemplates[templateKey];
    setNewPolicy({
      ...newPolicy,
      rules: template.rules
    });
  };

  const [showTemplateHelp, setShowTemplateHelp] = useState(false);
  const [jsonError, setJsonError] = useState<string>('');

  const validateJSON = (jsonString: string) => {
    if (!jsonString.trim()) {
      setJsonError('');
      return;
    }
    
    try {
      JSON.parse(jsonString);
      setJsonError('');
    } catch (error) {
      setJsonError('올바르지 않은 JSON 형식입니다.');
    }
  };

  const [newRule, setNewRule] = useState({
    name: '',
    type: 'toxicity',
    threshold: 0.5,
    action: 'block'
  });

  useEffect(() => {
    loadRules();
    loadStats();
    setLoading(false);
  }, []);

  useEffect(() => {
    if (activeTab === 'rag') {
      loadRAGMetrics();
    } else if (activeTab === 'arthur') {
      loadArthurInfo();
      loadArthurRules();
      loadArthurMetrics();
    }
  }, [activeTab, ragPeriod]);

  const loadRules = async () => {
    try {
      const response = await axios.get('http://localhost:8001/api/v1/guardrails/rules');
      setRules(response.data);
    } catch (error) {
      console.error('Failed to load rules:', error);
    }
  };


  // 샘플 규칙 생성 함수
  const createSampleRules = async () => {
    const sampleRules = [
      // 독성콘텐츠 (Toxicity) 규칙 10개
      { name: '욕설 및 비속어 차단', type: 'toxicity', threshold: 0.8, action: 'block', ...getRuleDetails('욕설 및 비속어 차단') },
      { name: '인신공격 방지', type: 'toxicity', threshold: 0.7, action: 'warn', ...getRuleDetails('인신공격 방지') },
      { name: '혐오 발언 탐지', type: 'toxicity', threshold: 0.75, action: 'block' },
      { name: '직장 내 괴롭힘 방지', type: 'toxicity', threshold: 0.6, action: 'flag' },
      { name: '성희롱 발언 차단', type: 'toxicity', threshold: 0.9, action: 'block' },
      { name: '차별적 언어 탐지', type: 'toxicity', threshold: 0.65, action: 'warn' },
      { name: '위협적 언어 방지', type: 'toxicity', threshold: 0.85, action: 'block' },
      { name: '임직원 비방 방지', type: 'toxicity', threshold: 0.7, action: 'flag' },
      { name: '부적절한 농담 차단', type: 'toxicity', threshold: 0.6, action: 'warn' },
      { name: '공격적 언어 탐지', type: 'toxicity', threshold: 0.75, action: 'flag' },

      // 개인정보 (Privacy) 규칙 10개  
      { name: '주민등록번호 노출 방지', type: 'privacy', threshold: 0.95, action: 'block', ...getRuleDetails('주민등록번호 노출 방지') },
      { name: '신용카드 번호 보호', type: 'privacy', threshold: 0.9, action: 'block' },
      { name: '개인 전화번호 차단', type: 'privacy', threshold: 0.8, action: 'warn' },
      { name: '이메일 주소 보호', type: 'privacy', threshold: 0.7, action: 'flag' },
      { name: '임직원 개인정보 보호', type: 'privacy', threshold: 0.85, action: 'block' },
      { name: '주소 정보 차단', type: 'privacy', threshold: 0.75, action: 'warn' },
      { name: '계좌 정보 보호', type: 'privacy', threshold: 0.95, action: 'block' },
      { name: '생년월일 정보 차단', type: 'privacy', threshold: 0.6, action: 'flag' },
      { name: '의료 정보 보호', type: 'privacy', threshold: 0.9, action: 'block' },
      { name: '가족 정보 보호', type: 'privacy', threshold: 0.65, action: 'warn' },

      // 편향성 (Bias) 규칙 10개
      { name: '성별 편견 방지', type: 'bias', threshold: 0.7, action: 'warn', ...getRuleDetails('성별 편견 방지') },
      { name: '연령 차별 탐지', type: 'bias', threshold: 0.75, action: 'flag' },
      { name: '종교적 편견 방지', type: 'bias', threshold: 0.8, action: 'warn' },
      { name: '지역 차별 탐지', type: 'bias', threshold: 0.65, action: 'flag' },
      { name: '학벌 편견 방지', type: 'bias', threshold: 0.6, action: 'warn' },
      { name: '직급 기반 차별 방지', type: 'bias', threshold: 0.7, action: 'flag' },
      { name: '외모 기반 편견 탐지', type: 'bias', threshold: 0.75, action: 'warn' },
      { name: '정치적 편향 방지', type: 'bias', threshold: 0.8, action: 'flag' },
      { name: '사회적 편견 탐지', type: 'bias', threshold: 0.65, action: 'warn' },
      { name: '문화적 편견 방지', type: 'bias', threshold: 0.7, action: 'flag' },

      // 콘텐츠필터 (Content Filter) 규칙 10개
      { name: '회사 기밀정보 누출 방지', type: 'content', threshold: 0.9, action: 'block', ...getRuleDetails('회사 기밀정보 누출 방지') },
      { name: '재무정보 유출 차단', type: 'content', threshold: 0.85, action: 'block' },
      { name: '조직도 정보 보호', type: 'content', threshold: 0.8, action: 'warn' },
      { name: '임원진 정보 보호', type: 'content', threshold: 0.75, action: 'flag' },
      { name: '사업계획 정보 차단', type: 'content', threshold: 0.9, action: 'block' },
      { name: '고객정보 유출 방지', type: 'content', threshold: 0.95, action: 'block' },
      { name: '계약서 내용 보호', type: 'content', threshold: 0.8, action: 'warn' },
      { name: '인사정보 유출 방지', type: 'content', threshold: 0.85, action: 'block' },
      { name: '매출 데이터 보호', type: 'content', threshold: 0.9, action: 'block' },
      { name: '전략 정보 차단', type: 'content', threshold: 0.85, action: 'block' }
    ];

    let createdCount = 0;
    let errorCount = 0;

    for (const rule of sampleRules) {
      try {
        await axios.post('http://localhost:8001/api/v1/guardrails/rules', rule);
        createdCount++;
      } catch (error) {
        console.error(`Failed to create rule ${rule.name}:`, error);
        errorCount++;
      }
    }

    alert(`샘플 규칙 생성 완료!\n성공: ${createdCount}개\n실패: ${errorCount}개`);
    await loadRules();
  };

  const loadStats = async () => {
    try {
      const response = await axios.get('http://localhost:8001/api/v1/guardrails/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  // Arthur AI Guardrails API 함수들
  const loadArthurInfo = async () => {
    try {
      const response = await axios.get('http://localhost:8009/api/v1/arthur/info');
      setArthurInfo(response.data);
    } catch (error) {
      console.error('Failed to load Arthur AI info:', error);
    }
  };

  const loadArthurRules = async () => {
    try {
      setArthurLoading(true);
      const response = await axios.get('http://localhost:8009/api/v1/arthur/rules');
      setArthurRules(response.data);
    } catch (error) {
      console.error('Failed to load Arthur AI rules:', error);
    } finally {
      setArthurLoading(false);
    }
  };

  const loadArthurMetrics = async () => {
    try {
      const response = await axios.get('http://localhost:8009/api/v1/arthur/metrics');
      setArthurMetrics(response.data);
    } catch (error) {
      console.error('Failed to load Arthur AI metrics:', error);
    }
  };

  // Arthur AI 규칙 CRUD 함수들
  const createArthurRule = async () => {
    try {
      const ruleData = {
        ...newArthurRule,
        korean_specific: true,
        custom_patterns: newArthurRule.custom_patterns.filter(p => p.trim()),
        examples: newArthurRule.examples.filter(e => e.trim())
      };
      
      await axios.post('http://localhost:8009/api/v1/arthur/rules', ruleData);
      alert(`규칙 "${newArthurRule.name}"이(가) 성공적으로 생성되었습니다.`);
      
      // 폼 초기화
      setNewArthurRule({
        name: '',
        type: 'toxicity',
        description: '',
        threshold: 0.8,
        action: 'block',
        custom_patterns: [''],
        examples: ['']
      });
      setShowArthurRuleForm(false);
      loadArthurRules();
    } catch (error) {
      console.error('Arthur AI 규칙 생성 실패:', error);
      alert('규칙 생성에 실패했습니다.');
    }
  };

  const updateArthurRule = async (ruleId: string, updates: any) => {
    try {
      await axios.put(`http://localhost:8009/api/v1/arthur/rules/${ruleId}`, updates);
      alert('규칙이 성공적으로 수정되었습니다.');
      setEditingArthurRule(null);
      loadArthurRules();
    } catch (error) {
      console.error('Arthur AI 규칙 수정 실패:', error);
      alert('규칙 수정에 실패했습니다.');
    }
  };

  const deleteArthurRule = async (ruleId: string, ruleName: string) => {
    if (!confirm(`규칙 "${ruleName}"을(를) 삭제하시겠습니까?`)) return;
    
    try {
      await axios.delete(`http://localhost:8009/api/v1/arthur/rules/${ruleId}`);
      alert(`규칙 "${ruleName}"이(가) 삭제되었습니다.`);
      loadArthurRules();
    } catch (error) {
      console.error('Arthur AI 규칙 삭제 실패:', error);
      alert('규칙 삭제에 실패했습니다.');
    }
  };

  const addPatternToArthurRule = (isExample: boolean = false) => {
    if (isExample) {
      setNewArthurRule({
        ...newArthurRule,
        examples: [...newArthurRule.examples, '']
      });
    } else {
      setNewArthurRule({
        ...newArthurRule,
        custom_patterns: [...newArthurRule.custom_patterns, '']
      });
    }
  };

  const removePatternFromArthurRule = (index: number, isExample: boolean = false) => {
    if (isExample) {
      const newExamples = newArthurRule.examples.filter((_, i) => i !== index);
      setNewArthurRule({
        ...newArthurRule,
        examples: newExamples.length > 0 ? newExamples : ['']
      });
    } else {
      const newPatterns = newArthurRule.custom_patterns.filter((_, i) => i !== index);
      setNewArthurRule({
        ...newArthurRule,
        custom_patterns: newPatterns.length > 0 ? newPatterns : ['']
      });
    }
  };

  const updatePatternInArthurRule = (index: number, value: string, isExample: boolean = false) => {
    if (isExample) {
      const newExamples = [...newArthurRule.examples];
      newExamples[index] = value;
      setNewArthurRule({
        ...newArthurRule,
        examples: newExamples
      });
    } else {
      const newPatterns = [...newArthurRule.custom_patterns];
      newPatterns[index] = value;
      setNewArthurRule({
        ...newArthurRule,
        custom_patterns: newPatterns
      });
    }
  };

  // Arthur AI 규칙 필터링 함수
  const getFilteredArthurRules = () => {
    let filtered = [...arthurRules];
    
    // 타입별 필터링
    if (arthurFilterType !== 'all') {
      filtered = filtered.filter(rule => rule.type === arthurFilterType);
    }
    
    // 상태별 필터링
    if (arthurFilterStatus !== 'all') {
      filtered = filtered.filter(rule => {
        if (arthurFilterStatus === 'active') return rule.enabled === true;
        if (arthurFilterStatus === 'inactive') return rule.enabled === false;
        return true;
      });
    }
    
    // 액션별 필터링
    if (arthurFilterAction !== 'all') {
      filtered = filtered.filter(rule => rule.action === arthurFilterAction);
    }
    
    // 검색어 필터링
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

  const testArthurText = async () => {
    if (!arthurTestText.trim()) {
      alert('테스트할 텍스트를 입력해주세요.');
      return;
    }

    try {
      setArthurTestLoading(true);
      const response = await axios.post('http://localhost:8009/api/v1/arthur/evaluate', {
        text: arthurTestText,
        context: { source: 'admin_panel_test' }
      });
      setArthurTestResult(response.data);
    } catch (error) {
      console.error('Failed to test text with Arthur AI:', error);
      alert('테스트 중 오류가 발생했습니다.');
    } finally {
      setArthurTestLoading(false);
    }
  };

  const createRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRule.name.trim()) {
      alert('규칙 이름을 입력해주세요.');
      return;
    }

    try {
      const response = await axios.post('http://localhost:8001/api/v1/guardrails/rules', {
        name: newRule.name.trim(),
        type: newRule.type,
        threshold: newRule.threshold,
        action: newRule.action
      });
      
      console.log('Rule created successfully:', response.data);
      alert(`규칙 "${newRule.name}"이(가) 성공적으로 생성되었습니다.`);
      setNewRule({ name: '', type: 'toxicity', threshold: 0.5, action: 'block' });
      await loadRules();
    } catch (error: any) {
      console.error('Failed to create rule:', error);
      
      let errorMessage = '규칙 생성에 실패했습니다.';
      if (error.response?.status === 422) {
        errorMessage = '입력한 데이터 형식이 올바르지 않습니다.';
      } else if (error.response?.status === 400) {
        errorMessage = '이미 존재하는 규칙 이름입니다.';
      } else if (error.message.includes('Network Error')) {
        errorMessage = '서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.';
      }
      
      alert(errorMessage);
    }
  };

  const toggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      await axios.put(`http://localhost:8001/api/v1/guardrails/rules/${ruleId}`, { enabled });
      await loadRules();
    } catch (error) {
      console.error('Failed to toggle rule:', error);
      alert('규칙 상태 변경에 실패했습니다.');
    }
  };

  const updateThreshold = async (ruleId: string, threshold: number) => {
    try {
      await axios.put(`http://localhost:8001/api/v1/guardrails/rules/${ruleId}`, { threshold });
      await loadRules();
    } catch (error) {
      console.error('Failed to update threshold:', error);
      alert('임계값 변경에 실패했습니다.');
    }
  };

  const deleteRule = async (ruleId: string) => {
    if (!confirm('이 규칙을 삭제하시겠습니까?')) return;
    
    try {
      await axios.delete(`http://localhost:8001/api/v1/guardrails/rules/${ruleId}`);
      alert('규칙이 삭제되었습니다.');
      await loadRules();
    } catch (error) {
      console.error('Failed to delete rule:', error);
      alert('규칙 삭제에 실패했습니다.');
    }
  };

  // 필터링된 규칙 목록 가져오기
  const getFilteredRules = () => {
    let filtered = [...rules];
    
    // 타입별 필터링
    if (ruleFilter !== 'all') {
      filtered = filtered.filter(rule => rule.type === ruleFilter);
    }
    
    // 검색어 필터링
    if (ruleSearchQuery) {
      filtered = filtered.filter(rule => 
        rule.name.toLowerCase().includes(ruleSearchQuery.toLowerCase()) ||
        rule.type.toLowerCase().includes(ruleSearchQuery.toLowerCase())
      );
    }
    
    return filtered;
  };

  // 규칙 편집 처리
  const handleEditRule = (rule: GuardrailRule) => {
    setEditingRule(rule);
  };

  // 규칙 상세 정보 보기
  const viewRuleDetails = (rule: GuardrailRule) => {
    const details = getRuleDetails(rule.name);
    setSelectedRule({ ...rule, ...details });
    setShowRuleDetailModal(true);
  };

  // Save edited rule
  const saveEditedRule = async () => {
    if (!editingRule) return;
    
    try {
      await axios.put(`http://localhost:8001/api/v1/guardrails/rules/${editingRule.id}`, {
        name: editingRule.name,
        type: editingRule.type,
        threshold: editingRule.threshold,
        action: editingRule.action || 'block',
        enabled: editingRule.enabled
      });
      
      // Update rules list
      setRules(rules.map(rule => 
        rule.id === editingRule.id ? editingRule : rule
      ));
      
      // Update selected rule if it's being viewed
      if (selectedRule?.id === editingRule.id) {
        setSelectedRule(editingRule);
      }
      
      setEditingRule(null);
      
      alert('규칙이 성공적으로 수정되었습니다.');
    } catch (error) {
      console.error('Error updating rule:', error);
      alert('규칙 수정 중 오류가 발생했습니다.');
    }
  };

  const testGuardrails = async () => {
    if (!testInput.trim()) {
      alert('테스트할 텍스트를 입력해주세요.');
      return;
    }

    setIsTestLoading(true);
    try {
      const response = await axios.post('http://localhost:8001/api/v1/guardrails/validate', {
        text: testInput
      });
      setTestResult(response.data);
    } catch (error) {
      console.error('Failed to test:', error);
      alert('테스트에 실패했습니다.');
    } finally {
      setIsTestLoading(false);
    }
  };

  // RBAC API functions
  const loadRbacData = async () => {
    setRbacLoading(true);
    try {
      await Promise.all([
        loadUsers(),
        loadRoles(),
        loadPolicies()
      ]);
    } catch (error) {
      console.error('Failed to load RBAC data:', error);
    } finally {
      setRbacLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await axios.get('http://localhost:8005/api/v1/users');
      // API returns array directly, not wrapped in 'users' property
      setUsers(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Failed to load users:', error);
      setUsers([]);
    }
  };

  const loadRoles = async () => {
    try {
      const response = await axios.get('http://localhost:8005/api/v1/roles');
      // API returns array directly, not wrapped in 'roles' property
      setRoles(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Failed to load roles:', error);
      setRoles([]);
    }
  };

  const loadPolicies = async () => {
    try {
      const response = await axios.get('http://localhost:8005/api/v1/policies');
      // API returns array directly, not wrapped in 'policies' property
      setPolicies(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Failed to load policies:', error);
      setPolicies([]);
    }
  };

  const createUser = async (userData: Partial<RBACUser>) => {
    try {
      await axios.post('http://localhost:8005/api/v1/users', userData);
      alert('사용자가 생성되었습니다.');
      await loadUsers();
    } catch (error) {
      console.error('Failed to create user:', error);
      alert('사용자 생성에 실패했습니다.');
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newUser.username.trim() || !newUser.email.trim() || !newUser.full_name.trim()) {
      alert('사용자명, 이메일, 이름을 모두 입력해주세요.');
      return;
    }

    const userData = {
      ...newUser,
      password: newUser.password || 'defaultPassword123' // Provide default password if empty
    };

    try {
      await axios.post('http://localhost:8005/api/v1/users', userData);
      alert('사용자가 생성되었습니다.');
      
      // Reset form
      setNewUser({
        username: '',
        email: '',
        full_name: '',
        password: '',
        department: '',
        job_title: '',
        clearance_level: 'internal'
      });
      
      await loadUsers();
    } catch (error: any) {
      console.error('Failed to create user:', error);
      let errorMessage = '사용자 생성에 실패했습니다.';
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((e: any) => e.msg).join(', ');
        }
      } else if (error.response?.status === 400) {
        errorMessage = '이미 존재하는 사용자명 또는 이메일입니다.';
      }
      
      alert(errorMessage);
    }
  };

  const updateUser = async (userId: string, userData: Partial<RBACUser>) => {
    try {
      await axios.put(`http://localhost:8005/api/v1/users/${userId}`, userData);
      alert('사용자 정보가 업데이트되었습니다.');
      await loadUsers();
    } catch (error) {
      console.error('Failed to update user:', error);
      alert('사용자 업데이트에 실패했습니다.');
    }
  };

  const deleteUser = async (userId: string) => {
    if (!confirm('이 사용자를 삭제하시겠습니까?')) return;
    
    try {
      await axios.delete(`http://localhost:8005/api/v1/users/${userId}`);
      alert('사용자가 삭제되었습니다.');
      await loadUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
      alert('사용자 삭제에 실패했습니다.');
    }
  };

  // Role management functions
  const handleCreateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newRole.name.trim()) {
      alert('역할 이름을 입력해주세요.');
      return;
    }

    try {
      await axios.post('http://localhost:8005/api/v1/roles', {
        name: newRole.name.trim(),
        description: newRole.description.trim(),
        permissions: newRole.permissions
      });
      alert('역할이 생성되었습니다.');
      
      // Reset form
      setNewRole({
        name: '',
        description: '',
        permissions: []
      });
      
      await loadRoles();
    } catch (error: any) {
      console.error('Failed to create role:', error);
      let errorMessage = '역할 생성에 실패했습니다.';
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        }
      } else if (error.response?.status === 400) {
        errorMessage = '이미 존재하는 역할 이름이거나 잘못된 데이터입니다.';
      }
      
      alert(errorMessage);
    }
  };

  const handlePermissionToggle = (permission: string) => {
    setNewRole(prev => ({
      ...prev,
      permissions: prev.permissions.includes(permission)
        ? prev.permissions.filter(p => p !== permission)
        : [...prev.permissions, permission]
    }));
  };

  const deleteRole = async (roleId: string) => {
    if (!confirm('이 역할을 삭제하시겠습니까?')) return;
    
    try {
      await axios.delete(`http://localhost:8005/api/v1/roles/${roleId}`);
      alert('역할이 삭제되었습니다.');
      await loadRoles();
    } catch (error: any) {
      console.error('Failed to delete role:', error);
      let errorMessage = '역할 삭제에 실패했습니다.';
      
      if (error.response?.status === 404) {
        errorMessage = '삭제하려는 역할을 찾을 수 없습니다.';
      } else if (error.response?.status === 403) {
        errorMessage = '시스템 역할은 삭제할 수 없습니다.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      alert(errorMessage);
    }
  };

  // Policy functions
  const createPolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPolicy.name.trim() || !newPolicy.description.trim()) {
      alert('정책 이름과 설명을 입력해주세요.');
      return;
    }

    // Validate JSON rules
    let parsedRules;
    try {
      parsedRules = newPolicy.rules ? JSON.parse(newPolicy.rules) : {};
    } catch (error) {
      alert('정책 규칙은 올바른 JSON 형식이어야 합니다.');
      return;
    }

    try {
      await axios.post('http://localhost:8005/api/v1/policies', {
        name: newPolicy.name.trim(),
        description: newPolicy.description.trim(),
        policy_rules: parsedRules  // Changed from 'rules' to 'policy_rules'
      });
      alert('정책이 생성되었습니다.');
      setNewPolicy({ name: '', description: '', rules: '', is_active: true });
      setJsonError(''); // Clear JSON error
      await loadPolicies();
    } catch (error: any) {
      console.error('Failed to create policy:', error);
      let errorMessage = '정책 생성에 실패했습니다.';
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((e: any) => e.msg).join(', ');
        }
      } else if (error.response?.status === 400) {
        errorMessage = '이미 존재하는 정책 이름이거나 잘못된 데이터입니다.';
      } else if (error.message.includes('Network Error')) {
        errorMessage = '서버에 연결할 수 없습니다. Permission Service가 실행 중인지 확인해주세요.';
      }
      
      alert(errorMessage);
    }
  };

  const deletePolicy = async (policyId: string) => {
    if (!confirm('이 정책을 삭제하시겠습니까?')) return;
    
    try {
      await axios.delete(`http://localhost:8005/api/v1/policies/${policyId}`);
      alert('정책이 삭제되었습니다.');
      await loadPolicies();
    } catch (error) {
      console.error('Failed to delete policy:', error);
      alert('정책 삭제에 실패했습니다.');
    }
  };

  // RAG evaluation functions
  const loadRAGMetrics = async () => {
    setRagLoading(true);
    try {
      // Load real-time metrics
      const realtimeResponse = await axios.get(`http://localhost:8002/api/v1/rag/metrics/realtime?limit=50`);
      setRagRealtime(realtimeResponse.data || null);
      
      // Load aggregated metrics
      const aggregatedResponse = await axios.get(`http://localhost:8002/api/v1/rag/metrics/aggregated?period=${ragPeriod}`);
      setRagAggregated(aggregatedResponse.data || null);
      
      // For now, set empty metrics array since the API doesn't provide individual metrics yet
      setRagMetrics([]);
      
      console.log('RAG metrics loaded successfully');
    } catch (error) {
      console.error('Failed to load RAG metrics:', error);
      // Set empty data if service is not available
      setRagMetrics([]);
      setRagRealtime(null);
      setRagAggregated(null);
    } finally {
      setRagLoading(false);
    }
  };

  const handleRAGPeriodChange = async (period: string) => {
    setRagPeriod(period);
    try {
      const aggregatedResponse = await axios.get(`http://localhost:8002/api/v1/rag/metrics/aggregated?period=${period}`);
      setRagAggregated(aggregatedResponse.data || null);
    } catch (error) {
      console.error('Failed to load aggregated metrics:', error);
    }
  };

  // Document management functions
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

  const uploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!uploadFile) {
      alert('업로드할 파일을 선택해주세요.');
      return;
    }

    setIsUploading(true);
    
    // Check for duplicate files first
    try {
      const duplicateResponse = await axios.get(`http://localhost:8000/api/v1/documents/default_user/check-duplicate`, {
        params: { filename: uploadFile.name }
      });
      
      if (duplicateResponse.data.success && duplicateResponse.data.duplicate_found) {
        // Show duplicate warning modal instead of uploading
        handleDuplicateWarning({
          filename: uploadFile.name,
          existing_document: duplicateResponse.data.existing_document
        });
        setIsUploading(false);
        return;
      }
    } catch (error) {
      console.error('Failed to check for duplicates:', error);
      // Continue with upload even if duplicate check fails
    }
    
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
          return;
        }
      }

      const response = await axios.post('http://localhost:8009/documents', {
        title: newDocument.title.trim(),
        content: newDocument.content.trim(),
        metadata: metadata
      });

      if (response.data.success) {
        alert(`문서가 성공적으로 추가되었습니다: ${response.data.data.chunks_created}개 청크 생성`);
        
        // Reset form
        setNewDocument({ title: '', content: '', metadata: '' });
        
        // Reload documents list
        await loadDocuments();
      } else {
        alert(`문서 추가 실패: ${response.data.message || '알 수 없는 오류'}`);
      }
    } catch (error: any) {
      console.error('Failed to create document:', error);
      alert(`문서 추가 중 오류가 발생했습니다: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const deleteDocument = async (documentId: string) => {
    if (!confirm(`문서 '${documentId}'를 삭제하시겠습니까?`)) return;
    
    try {
      const response = await axios.delete(`http://localhost:8009/documents/${documentId}`);
      
      if (response.data.success) {
        alert('문서가 삭제되었습니다.');
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
        query: query.trim()
      });

      if (response.data.success) {
        const data = response.data.data;
        setSearchResultData({
          ...data,
          query: query.trim()
        });
        setShowSearchResultModal(true);
      } else {
        alert('검색 실패');
      }
    } catch (error: any) {
      console.error('Failed to test search:', error);
      alert(`검색 중 오류가 발생했습니다: ${error.message}`);
    } finally {
      setSearchLoading(false);
    }
  };

  // Document modal handlers
  const handleViewDocument = async (document: any) => {
    setContentLoading(true);
    setSelectedDocument(document);
    setShowDetailModal(true);
    
    try {
      // Korean RAG 문서 (doc_로 시작하는 ID)인지 확인
      if (document.id && document.id.startsWith('doc_')) {
        // Korean RAG 문서의 경우 특별한 내용 표시
        const koreanRagContent = `📄 Korean RAG 시스템 문서

이 문서는 Korean RAG 시스템에서 처리되어 원본 내용을 직접 표시할 수 없습니다.

📋 문서 정보:
• 파일명: ${document.filename || document.title || '알 수 없음'}
• 문서 ID: ${document.id}
• 청크 수: ${document.chunk_count || 'N/A'}개
• 생성일: ${document.created_at ? new Date(document.created_at).toLocaleString('ko-KR') : '알 수 없음'}
• 파일 크기: ${document.file_size ? (document.file_size / 1024).toFixed(1) + ' KB' : 'N/A'}
• 처리 방식: Korean RAG Service

💡 이 문서는 벡터 데이터베이스에 청크 단위로 저장되어 있어 
검색 시 관련 부분만 조회됩니다. 

🔍 이 문서를 활용하려면:
1. 채팅에서 관련 질문을 하시면 RAG 시스템이 이 문서의 내용을 참조하여 답변합니다
2. 원본 내용을 확인하려면 원본 파일을 참조해주세요

⚙️ 기술 정보:
- 벡터 임베딩: jhgan/ko-sroberta-multitask 모델 사용
- 저장소: Milvus 벡터 데이터베이스
- 언어 최적화: 한국어 형태소 분석 적용`;
        
        setDocumentContent(koreanRagContent);
        setContentLoading(false);
        return;
      }

      // 일반 문서의 경우 기존 API 호출
      const response = await axios.get(`http://localhost:8000/api/v1/documents/default_user/${document.id}/content`);
      if (response.data.success && response.data.document) {
        setDocumentContent(response.data.document.content || '내용을 불러올 수 없습니다.');
      } else {
        setDocumentContent('문서 내용을 불러오는데 실패했습니다.');
      }
    } catch (error: any) {
      console.error('Failed to load document content:', error);
      setDocumentContent('문서 내용을 불러오는 중 오류가 발생했습니다.');
    } finally {
      setContentLoading(false);
    }
  };

  const handleDuplicateWarning = (duplicateInfo: any) => {
    setDuplicateInfo(duplicateInfo);
    setShowDuplicateModal(true);
  };

  const closeDuplicateModal = () => {
    setShowDuplicateModal(false);
    setDuplicateInfo(null);
  };

  const handleViewChunks = async (document: any) => {
    setChunksLoading(true);
    setSelectedDocument(document);
    setShowChunkModal(true);
    
    try {
      const response = await axios.get(`http://localhost:8000/api/v1/documents/default_user/${document.id}/chunks`);
      if (response.data.success) {
        setDocumentChunks(response.data.chunks || []);
      } else {
        alert('청크 정보를 가져올 수 없습니다.');
        setDocumentChunks([]);
      }
    } catch (error: any) {
      console.error('Failed to load document chunks:', error);
      alert('청크 정보를 불러오는 중 오류가 발생했습니다.');
      setDocumentChunks([]);
    } finally {
      setChunksLoading(false);
    }
  };

  const closeChunkModal = () => {
    setShowChunkModal(false);
    setSelectedDocument(null);
    setDocumentChunks([]);
  };

  const closeDetailModal = () => {
    setShowDetailModal(false);
    setSelectedDocument(null);
    setDocumentContent('');
  };

  useEffect(() => {
    if (activeTab === 'documents') {
      loadDocuments();
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
              <p className="text-sm text-gray-600">AI 안전 관리 플랫폼</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex space-x-8">
            {[
              { id: 'rules', name: '규칙 관리', icon: '⚙️' },
              { id: 'test', name: '실시간 테스트', icon: '🚀' },
              { id: 'documents', name: '문서 관리', icon: '📚' },
              { id: 'rbac', name: 'RBAC 설정', icon: '👥' },
              { id: 'rag', name: 'RAG 성과평가', icon: '🧠' },
              { id: 'arthur', name: 'Arthur AI Guardrails', icon: '🛡️' },
              { id: 'monitoring', name: '모니터링', icon: '📈' },
              { id: 'stats', name: '통계', icon: '📊' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-4 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {activeTab === 'rules' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">새 규칙 추가</h2>
              <form onSubmit={createRule} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">규칙 이름</label>
                    <input
                      type="text"
                      value={newRule.name}
                      onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="규칙 이름을 입력하세요"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">규칙 유형</label>
                    <select
                      value={newRule.type}
                      onChange={(e) => setNewRule({ ...newRule, type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="toxicity">독성 콘텐츠</option>
                      <option value="pii">개인정보</option>
                      <option value="bias">편향성</option>
                      <option value="content">콘텐츠 필터</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">임계값 ({newRule.threshold})</label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={newRule.threshold}
                      onChange={(e) => setNewRule({ ...newRule, threshold: parseFloat(e.target.value) })}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">액션</label>
                    <select
                      value={newRule.action}
                      onChange={(e) => setNewRule({ ...newRule, action: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="block">차단</option>
                      <option value="flag">플래그</option>
                      <option value="modify">수정</option>
                    </select>
                  </div>
                </div>
                <div className="flex space-x-3">
                  <button
                    type="submit"
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                  >
                    규칙 생성
                  </button>
                  <button
                    type="button"
                    onClick={createSampleRules}
                    className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
                  >
                    📋 샘플 규칙 생성 (40개)
                  </button>
                </div>
              </form>
            </div>

            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">활성 규칙 목록</h2>
                  <div className="text-sm text-gray-600">
                    총 {getFilteredRules().length}개 / {rules.length}개 규칙
                  </div>
                </div>
                
                {/* Filter Controls */}
                <div className="flex flex-col sm:flex-row gap-4 mb-4">
                  <div className="flex-1">
                    <input
                      type="text"
                      placeholder="규칙 이름으로 검색..."
                      value={ruleSearchQuery}
                      onChange={(e) => setRuleSearchQuery(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="flex gap-2">
                    <select
                      value={ruleFilter}
                      onChange={(e) => setRuleFilter(e.target.value)}
                      className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">모든 규칙</option>
                      <option value="toxicity">독성 콘텐츠</option>
                      <option value="pii">개인정보</option>
                      <option value="bias">편향성</option>
                      <option value="content">콘텐츠 필터</option>
                    </select>
                    <button
                      onClick={() => {
                        setRuleFilter('all');
                        setRuleSearchQuery('');
                      }}
                      className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      🗑️ 초기화
                    </button>
                  </div>
                </div>
              </div>
              <div className="p-6">
                {getFilteredRules().length === 0 ? (
                  <div className="text-center py-8">
                    {rules.length === 0 ? (
                      <>
                        <div className="text-4xl mb-2">⚙️</div>
                        <p className="text-gray-500 mb-2">등록된 규칙이 없습니다.</p>
                        <p className="text-sm text-gray-400">샘플 규칙을 생성하거나 새 규칙을 직접 추가해보세요.</p>
                      </>
                    ) : (
                      <>
                        <div className="text-4xl mb-2">🔍</div>
                        <p className="text-gray-500 mb-2">검색 결과가 없습니다.</p>
                        <p className="text-sm text-gray-400">다른 검색어나 필터를 시도해보세요.</p>
                      </>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {getFilteredRules().map((rule) => {
                      const ruleDetails = getRuleDetails(rule.name);
                      return (
                        <div 
                          key={rule.id} 
                          className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                          onClick={() => viewRuleDetails(rule)}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                              <h3 className="font-medium text-blue-600 hover:text-blue-800">{rule.name}</h3>
                              <span className={`text-xs px-2 py-1 rounded ${
                                rule.type === 'toxicity' ? 'bg-red-100 text-red-700' :
                                rule.type === 'pii' ? 'bg-yellow-100 text-yellow-700' :
                                rule.type === 'bias' ? 'bg-purple-100 text-purple-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {rule.type === 'toxicity' ? '독성 콘텐츠' :
                                 rule.type === 'pii' ? '개인정보' :
                                 rule.type === 'bias' ? '편향성' : '콘텐츠 필터'}
                              </span>
                              {ruleDetails && (
                                <span className={`text-xs px-1 py-0.5 rounded text-white ${
                                  ruleDetails.risk_level === 'high' ? 'bg-red-500' :
                                  ruleDetails.risk_level === 'medium' ? 'bg-orange-500' : 'bg-green-500'
                                }`}>
                                  {ruleDetails.risk_level === 'high' ? '높음' :
                                   ruleDetails.risk_level === 'medium' ? '보통' : '낮음'}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                              <button
                                onClick={() => toggleRule(rule.id, !rule.enabled)}
                                className={`px-3 py-1 rounded-full text-xs font-medium ${
                                  rule.enabled
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-600'
                                }`}
                              >
                                {rule.enabled ? '🟢 활성화' : '🔴 비활성화'}
                              </button>
                              <button
                                onClick={() => handleEditRule(rule)}
                                className="text-blue-600 hover:text-blue-800 text-sm px-2 py-1 rounded hover:bg-blue-50"
                              >
                                ✏️ 편집
                              </button>
                              <button
                                onClick={() => deleteRule(rule.id)}
                                className="text-red-600 hover:text-red-800 text-sm px-2 py-1 rounded hover:bg-red-50"
                              >
                                🗑️ 삭제
                              </button>
                            </div>
                          </div>
                          
                          {ruleDetails && (
                            <div className="mb-3">
                              <p className="text-sm text-gray-600 line-clamp-2">
                                {ruleDetails.description}
                              </p>
                            </div>
                          )}
                          
                          <div className="flex items-center gap-4">
                            <span className="text-sm text-gray-600">임계값:</span>
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.1"
                              value={rule.threshold}
                              onChange={(e) => {
                                e.stopPropagation();
                                updateThreshold(rule.id, parseFloat(e.target.value));
                              }}
                              className="flex-1"
                              onClick={(e) => e.stopPropagation()}
                            />
                            <span className="text-sm font-medium bg-gray-100 px-2 py-1 rounded">
                              {rule.threshold}
                            </span>
                          </div>
                          
                          <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                            <span>클릭하여 상세 정보 보기</span>
                            <span>ID: {rule.id}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'test' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4">실시간 테스트</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">테스트할 텍스트</label>
                <textarea
                  value={testInput}
                  onChange={(e) => setTestInput(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="테스트할 텍스트를 입력하세요..."
                />
              </div>
              <button
                onClick={testGuardrails}
                disabled={isTestLoading}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
              >
                {isTestLoading ? '테스트 중...' : '🚀 테스트 실행'}
              </button>

              {testResult && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-medium mb-2">테스트 결과</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium">상태:</span> 
                      <span className={`ml-2 px-2 py-1 rounded text-xs ${
                        testResult.action === 'allow' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {testResult.action === 'allow' ? '✅ 허용' : '❌ 차단'}
                      </span>
                    </div>
                    <div><span className="font-medium">점수:</span> {testResult.score}</div>
                    <div><span className="font-medium">위반 규칙:</span> {testResult.violations?.join(', ') || '없음'}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'rag' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">RAG 성과평가</h2>
                  <div className="flex items-center space-x-4">
                    <select 
                      value={ragPeriod}
                      onChange={(e) => handleRAGPeriodChange(e.target.value)}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="1h">최근 1시간</option>
                      <option value="24h">최근 24시간</option>
                      <option value="7d">최근 7일</option>
                      <option value="30d">최근 30일</option>
                    </select>
                    <button
                      onClick={loadRAGMetrics}
                      disabled={ragLoading}
                      className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 disabled:bg-gray-400 text-sm"
                    >
                      {ragLoading ? '로딩 중...' : '🔄 새로고침'}
                    </button>
                  </div>
                </div>
              </div>

              <div className="p-6">
                {ragLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">RAG 성과 데이터를 불러오는 중...</p>
                  </div>
                ) : (
                  <>
                    {/* Aggregated Metrics */}
                    {ragAggregated && (
                      <div className="mb-8">
                        <h3 className="text-lg font-medium mb-4">📊 전체 성과 요약 ({ragAggregated.period})</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                          <div className="bg-blue-50 p-4 rounded-lg border">
                            <div className="text-2xl font-bold text-blue-600">
                              {ragAggregated.total_queries.toLocaleString()}
                            </div>
                            <div className="text-sm text-blue-700">총 쿼리 수</div>
                          </div>
                          <div className="bg-green-50 p-4 rounded-lg border">
                            <div className="text-2xl font-bold text-green-600">
                              {(ragAggregated.avg_quality_score * 100).toFixed(1)}%
                            </div>
                            <div className="text-sm text-green-700">평균 품질 점수</div>
                          </div>
                          <div className="bg-purple-50 p-4 rounded-lg border">
                            <div className="text-2xl font-bold text-purple-600">
                              {ragAggregated.avg_total_latency_ms.toFixed(0)}ms
                            </div>
                            <div className="text-sm text-purple-700">평균 응답시간</div>
                          </div>
                          <div className="bg-orange-50 p-4 rounded-lg border">
                            <div className="text-2xl font-bold text-orange-600">
                              {(ragAggregated.avg_hallucination_rate * 100).toFixed(1)}%
                            </div>
                            <div className="text-sm text-orange-700">평균 환각률</div>
                          </div>
                        </div>

                        {/* Real-time Metrics */}
                        {ragRealtime && (
                          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border mb-6">
                            <h4 className="font-medium mb-3">🔴 실시간 상태</h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div className="text-center">
                                <div className="text-lg font-bold text-blue-600">{ragRealtime.current_throughput.toFixed(1)}</div>
                                <div className="text-gray-600">초/요청</div>
                              </div>
                              <div className="text-center">
                                <div className="text-lg font-bold text-green-600">{ragRealtime.active_sessions}</div>
                                <div className="text-gray-600">활성 세션</div>
                              </div>
                              <div className="text-center">
                                <div className="text-lg font-bold text-purple-600">{ragRealtime.avg_latency_1min}ms</div>
                                <div className="text-gray-600">1분 평균 지연</div>
                              </div>
                              <div className="text-center">
                                <div className="text-lg font-bold text-orange-600">{(ragRealtime.success_rate * 100).toFixed(1)}%</div>
                                <div className="text-gray-600">성공률</div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Detailed Metrics */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                          <div className="bg-white border rounded-lg p-4">
                            <h4 className="font-medium mb-2">🎯 정확성 메트릭</h4>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span>컨텍스트 관련성:</span>
                                <span className="font-medium">{(ragAggregated.avg_context_relevance * 100).toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span>컨텍스트 충분성:</span>
                                <span className="font-medium">{(ragAggregated.avg_context_sufficiency * 100).toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span>답변 관련성:</span>
                                <span className="font-medium">{(ragAggregated.avg_answer_relevance * 100).toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span>답변 정확성:</span>
                                <span className="font-medium">{(ragAggregated.avg_answer_correctness * 100).toFixed(1)}%</span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="bg-white border rounded-lg p-4">
                            <h4 className="font-medium mb-2">⚡ 성능 메트릭</h4>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span>검색 지연시간:</span>
                                <span className="font-medium">{ragAggregated.avg_retrieval_latency_ms.toFixed(0)}ms</span>
                              </div>
                              <div className="flex justify-between">
                                <span>생성 지연시간:</span>
                                <span className="font-medium">{ragAggregated.avg_generation_latency_ms.toFixed(0)}ms</span>
                              </div>
                              <div className="flex justify-between">
                                <span>전체 지연시간:</span>
                                <span className="font-medium">{ragAggregated.avg_total_latency_ms.toFixed(0)}ms</span>
                              </div>
                              <div className="flex justify-between">
                                <span>P95 지연시간:</span>
                                <span className="font-medium">{ragAggregated.p95_latency_ms.toFixed(0)}ms</span>
                              </div>
                              <div className="flex justify-between">
                                <span>처리량:</span>
                                <span className="font-medium">{ragAggregated.throughput_per_second.toFixed(1)}/초</span>
                              </div>
                            </div>
                          </div>

                          <div className="bg-white border rounded-lg p-4">
                            <h4 className="font-medium mb-2">📈 품질 분포</h4>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-green-600">우수:</span>
                                <span className="font-medium">{ragAggregated.quality_distribution.excellent}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-blue-600">양호:</span>
                                <span className="font-medium">{ragAggregated.quality_distribution.good}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-yellow-600">보통:</span>
                                <span className="font-medium">{ragAggregated.quality_distribution.fair}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-red-600">미흡:</span>
                                <span className="font-medium">{ragAggregated.quality_distribution.poor}%</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Recent Evaluations */}
                    <div>
                      <h3 className="text-lg font-medium mb-4">🕐 최근 평가 내역</h3>
                      {ragMetrics.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                          최근 RAG 평가 데이터가 없습니다.
                          <br />
                          <span className="text-xs text-gray-400">RAG Evaluator Service가 실행 중인지 확인해주세요. (포트: 8002)</span>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {ragMetrics.slice(0, 10).map((metric, index) => (
                            <div key={index} className="bg-gray-50 border rounded-lg p-4">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center space-x-3">
                                  <span className="text-sm font-medium">{metric.session_id}</span>
                                  <span className="text-xs text-gray-500">
                                    {new Date(metric.timestamp).toLocaleString('ko-KR')}
                                  </span>
                                </div>
                                <div className="flex space-x-2">
                                  <span className={`px-2 py-1 text-xs rounded ${
                                    metric.overall_quality_score >= 0.8 ? 'bg-green-100 text-green-800' :
                                    metric.overall_quality_score >= 0.6 ? 'bg-blue-100 text-blue-800' :
                                    metric.overall_quality_score >= 0.4 ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-red-100 text-red-800'
                                  }`}>
                                    품질: {(metric.overall_quality_score * 100).toFixed(1)}%
                                  </span>
                                  <span className="px-2 py-1 text-xs rounded bg-purple-100 text-purple-800">
                                    {metric.total_latency_ms}ms
                                  </span>
                                </div>
                              </div>
                              <div className="text-sm text-gray-700 mb-2 truncate">
                                <strong>쿼리:</strong> {metric.query}
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                                <div>관련성: {(metric.context_relevance * 100).toFixed(0)}%</div>
                                <div>답변: {(metric.answer_relevance * 100).toFixed(0)}%</div>
                                <div>신실성: {(metric.faithfulness * 100).toFixed(0)}%</div>
                                <div>환각률: {(metric.hallucination_rate * 100).toFixed(0)}%</div>
                              </div>
                            </div>
                          ))}
                          {ragMetrics.length > 10 && (
                            <div className="text-center text-gray-500 text-sm py-2">
                              총 {ragMetrics.length}개 중 최근 10개를 표시하고 있습니다.
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Charts Section */}
                    {ragAggregated && (
                      <div className="mt-8">
                        <h3 className="text-lg font-medium mb-6">📊 성과 차트</h3>
                        
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                          {/* Quality Distribution Donut Chart */}
                          <div className="bg-white border rounded-lg p-4">
                            <DonutChart
                              data={[
                                { label: '우수', value: ragAggregated.quality_distribution.excellent, color: '#10b981' },
                                { label: '양호', value: ragAggregated.quality_distribution.good, color: '#3b82f6' },
                                { label: '보통', value: ragAggregated.quality_distribution.fair, color: '#f59e0b' },
                                { label: '미흡', value: ragAggregated.quality_distribution.poor, color: '#ef4444' }
                              ]}
                              title="품질 분포"
                              width={400}
                              height={300}
                            />
                          </div>
                          
                          {/* Performance Metrics Bar Chart */}
                          <div className="bg-white border rounded-lg p-4">
                            <BarChart
                              data={[
                                { label: '검색 지연', value: ragAggregated.avg_retrieval_latency_ms, color: '#8b5cf6' },
                                { label: '생성 지연', value: ragAggregated.avg_generation_latency_ms, color: '#06b6d4' },
                                { label: 'P95 지연', value: ragAggregated.p95_latency_ms, color: '#f59e0b' }
                              ]}
                              title="지연시간 비교"
                              width={400}
                              height={300}
                              yAxisLabel="밀리초 (ms)"
                              orientation="vertical"
                            />
                          </div>
                        </div>
                        
                        {/* Accuracy Metrics Bar Chart */}
                        <div className="bg-white border rounded-lg p-4 mb-6">
                          <BarChart
                            data={[
                              { label: '컨텍스트 관련성', value: ragAggregated.avg_context_relevance * 100, color: '#10b981' },
                              { label: '컨텍스트 충분성', value: ragAggregated.avg_context_sufficiency * 100, color: '#3b82f6' },
                              { label: '답변 관련성', value: ragAggregated.avg_answer_relevance * 100, color: '#8b5cf6' },
                              { label: '답변 정확성', value: ragAggregated.avg_answer_correctness * 100, color: '#f59e0b' },
                              { label: '환각률 (낮을수록 좋음)', value: ragAggregated.avg_hallucination_rate * 100, color: '#ef4444' }
                            ]}
                            title="정확성 메트릭 비교"
                            width={800}
                            height={400}
                            yAxisLabel="백분율 (%)"
                            orientation="vertical"
                          />
                        </div>
                        
                        {/* Time Series Chart for Quality Scores */}
                        {ragRealtime && ragRealtime.recent_quality_scores && (
                          <div className="bg-white border rounded-lg p-4">
                            <TimeSeriesChart
                              data={ragRealtime.recent_quality_scores.map((score, index) => ({
                                timestamp: new Date(Date.now() - (ragRealtime.recent_quality_scores.length - index) * 60000).toISOString(),
                                value: score * 100,
                                label: `품질 점수: ${(score * 100).toFixed(1)}%`
                              }))}
                              title="최근 품질 점수 추이"
                              width={800}
                              height={300}
                              color="#3b82f6"
                              yAxisLabel="품질 점수 (%)"
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'monitoring' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">시스템 모니터링</h2>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">Docker 컨테이너 메트릭</span>
                    <a 
                      href="http://localhost:9090" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 text-sm"
                    >
                      📊 Prometheus
                    </a>
                  </div>
                </div>
              </div>
              
              <div className="p-6">
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">📈 Grafana 대시보드</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    실시간 컨테이너 메트릭, 리소스 사용량, 네트워크 I/O 등을 모니터링할 수 있습니다.
                  </p>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                      Prometheus: localhost:9091
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                      Grafana: localhost:3010
                    </div>
                  </div>
                </div>

                <div className="border rounded-lg overflow-hidden" style={{ height: '80vh' }}>
                  <iframe 
                    src="http://localhost:3010/d/sdc-docker-containers/sdc-docker-containers-monitoring?orgId=1&refresh=30s&kiosk=tv"
                    width="100%" 
                    height="100%"
                    style={{ border: 'none' }}
                    title="Grafana Dashboard"
                    allow="fullscreen"
                  />
                </div>
                
                <div className="mt-4 text-center">
                  <a 
                    href="http://localhost:3010/d/sdc-docker-containers/sdc-docker-containers-monitoring?orgId=1"
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm"
                  >
                    🔗 새 창에서 열기
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

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

                {/* Documents List */}
                <div>
                  <h3 className="text-lg font-medium mb-4">📋 저장된 문서 목록</h3>
                  {documentLoading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                      <p className="text-gray-600">문서 목록을 불러오는 중...</p>
                    </div>
                  ) : documents.length === 0 ? (
                    <div className="text-center text-gray-500 py-8">
                      저장된 문서가 없습니다.
                      <br />
                      <span className="text-xs text-gray-400">위에서 파일을 업로드하거나 문서를 직접 입력해보세요.</span>
                    </div>
                  ) : (
                    <div className="bg-white border rounded-lg overflow-hidden">
                      <div className="px-4 py-3 bg-gray-50 border-b">
                        <div className="flex items-center justify-between text-sm">
                          <div className="font-medium">총 {(documents || []).length}개 문서</div>
                          <div className="text-gray-500">데이터 소스: Main Backend API (포트 8000)</div>
                        </div>
                      </div>
                      
                      {/* Document Table */}
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">문서명</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">업로드 일자</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">파일 크기</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">청크 수</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">처리 방법</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">업로드 담당자</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">액션</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {(documents || []).map((doc, index) => {
                              const formatFileSize = (bytes) => {
                                if (!bytes) return 'N/A';
                                const kb = bytes / 1024;
                                const mb = kb / 1024;
                                if (mb >= 1) return `${mb.toFixed(1)} MB`;
                                return `${kb.toFixed(1)} KB`;
                              };

                              const formatDate = (dateString) => {
                                if (!dateString) return 'N/A';
                                return new Date(dateString).toLocaleDateString('ko-KR', {
                                  year: 'numeric',
                                  month: '2-digit',
                                  day: '2-digit',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                });
                              };

                              const getFileType = (filename) => {
                                if (!filename) return 'Unknown';
                                const extension = filename.split('.').pop()?.toLowerCase();
                                const typeMap = {
                                  'pdf': 'PDF',
                                  'doc': 'Word',
                                  'docx': 'Word',
                                  'ppt': 'PowerPoint',
                                  'pptx': 'PowerPoint',
                                  'xls': 'Excel',
                                  'xlsx': 'Excel',
                                  'txt': 'Text',
                                  'md': 'Markdown'
                                };
                                return typeMap[extension] || extension?.toUpperCase() || 'Unknown';
                              };

                              return (
                                <tr key={doc.id || index} className="hover:bg-gray-50">
                                  <td className="px-4 py-3 whitespace-nowrap">
                                    <div className="flex items-center">
                                      <div className="flex-shrink-0 h-8 w-8">
                                        <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                                          <span className="text-xs font-medium text-blue-800">
                                            {getFileType(doc.filename).charAt(0)}
                                          </span>
                                        </div>
                                      </div>
                                      <div className="ml-3">
                                        <div className="text-sm font-medium text-gray-900 max-w-xs truncate" title={doc.filename || doc.title}>
                                          {doc.filename || doc.title || 'Untitled'}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                          {getFileType(doc.filename)}
                                        </div>
                                      </div>
                                    </div>
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                    {formatDate(doc.created_at)}
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                    {formatFileSize(doc.file_size)}
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap">
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                      {doc.chunk_count || 0} 청크
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                    <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800">
                                      {doc.processing_method || 'Unknown'}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                    default_user
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap">
                                    <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${
                                      doc.is_processed 
                                        ? 'bg-green-100 text-green-800' 
                                        : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                      {doc.is_processed ? '✓ 처리완료' : '⏳ 처리중'}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium space-x-2">
                                    <button 
                                      onClick={() => handleViewDocument(doc)}
                                      className="text-blue-600 hover:text-blue-900 hover:underline"
                                    >
                                      상세보기
                                    </button>
                                    <button 
                                      onClick={() => handleViewChunks(doc)}
                                      className="text-green-600 hover:text-green-900 hover:underline"
                                    >
                                      청크 보기
                                    </button>
                                    <button 
                                      onClick={() => deleteDocument(doc.id)}
                                      className="text-red-600 hover:text-red-900 hover:underline"
                                    >
                                      삭제
                                    </button>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                      
                      {/* Summary Stats */}
                      <div className="px-4 py-3 bg-gray-50 border-t">
                        <div className="flex justify-between items-center text-sm text-gray-600">
                          <div>
                            총 문서: {(documents || []).length}개 | 
                            총 청크: {(documents || []).reduce((sum, doc) => sum + (doc.chunk_count || 0), 0)}개
                          </div>
                          <div>
                            벡터 저장소: Milvus | 임베딩 모델: KURE-v1
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* RAG System Status */}
                <div className="mt-6 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4">
                  <h4 className="font-medium mb-2">🧠 Korean RAG 시스템 상태</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">활성</div>
                      <div className="text-gray-600">서비스 상태</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-600">jhgan/ko-sroberta</div>
                      <div className="text-gray-600">임베딩 모델</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-purple-600">768차원</div>
                      <div className="text-gray-600">벡터 차원</div>
                    </div>
                  </div>
                  <div className="mt-3 text-xs text-gray-600 text-center">
                    문서는 센텐스 청킹 → 한국어 임베딩 → Milvus 벡터 저장소 순서로 처리됩니다.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'arthur' && (
          <div className="space-y-6">
            {/* Arthur AI Service Info */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold flex items-center">
                    <span className="mr-2">🛡️</span>
                    Arthur AI Guardrails
                  </h2>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      arthurInfo?.service_name 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {arthurInfo?.service_name ? '🟢 서비스 정상' : '🔴 서비스 오류'}
                    </span>
                    <button
                      onClick={() => {
                        loadArthurInfo();
                        loadArthurRules();
                        loadArthurMetrics();
                      }}
                      disabled={arthurLoading}
                      className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 text-sm disabled:opacity-50"
                    >
                      {arthurLoading ? '새로고침 중...' : '🔄 새로고침'}
                    </button>
                  </div>
                </div>
              </div>
              <div className="p-6">
                {arthurInfo && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600 mb-1">모델 ID</div>
                      <div className="font-semibold">{arthurInfo.model_id}</div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600 mb-1">API 상태</div>
                      <div className="font-semibold">{arthurInfo.api_status}</div>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600 mb-1">서비스 포트</div>
                      <div className="font-semibold">8009</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Arthur AI Rules */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">Arthur AI 규칙 관리</h3>
                    <p className="text-sm text-gray-600 mt-1">한국어 특화 가드레일 규칙</p>
                  </div>
                  <button
                    onClick={() => setShowArthurRuleForm(true)}
                    className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 text-sm"
                  >
                    ➕ 새 규칙 추가
                  </button>
                </div>
              </div>
              <div className="p-6">
                {/* Arthur AI 필터링 UI */}
                {arthurRules.length > 0 && (
                  <div className="mb-6 space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-gray-900">규칙 필터</h4>
                      <div className="text-sm text-gray-600">
                        총 {getFilteredArthurRules().length}개 / {arthurRules.length}개 규칙
                      </div>
                    </div>
                    
                    {/* 검색 및 필터 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                      {/* 검색 */}
                      <div>
                        <input
                          type="text"
                          placeholder="규칙명 검색..."
                          value={arthurSearchText}
                          onChange={(e) => setArthurSearchText(e.target.value)}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                      
                      {/* 타입 필터 */}
                      <div>
                        <select
                          value={arthurFilterType}
                          onChange={(e) => setArthurFilterType(e.target.value)}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="all">모든 타입</option>
                          <option value="toxicity">독성 콘텐츠</option>
                          <option value="pii">개인정보</option>
                          <option value="bias">편견</option>
                          <option value="content_filter">콘텐츠 필터</option>
                          <option value="spam">스팸</option>
                        </select>
                      </div>
                      
                      {/* 상태 필터 */}
                      <div>
                        <select
                          value={arthurFilterStatus}
                          onChange={(e) => setArthurFilterStatus(e.target.value)}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="all">모든 상태</option>
                          <option value="active">활성</option>
                          <option value="inactive">비활성</option>
                        </select>
                      </div>
                      
                      {/* 액션 필터 */}
                      <div>
                        <select
                          value={arthurFilterAction}
                          onChange={(e) => setArthurFilterAction(e.target.value)}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="all">모든 액션</option>
                          <option value="block">차단</option>
                          <option value="flag">플래그</option>
                          <option value="modify">수정</option>
                          <option value="alert">알림</option>
                        </select>
                      </div>
                    </div>
                    
                    {/* 활성 필터 표시 */}
                    {(arthurFilterType !== 'all' || arthurFilterStatus !== 'all' || arthurFilterAction !== 'all' || arthurSearchText.trim()) && (
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-600">활성 필터:</span>
                        {arthurFilterType !== 'all' && (
                          <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs">
                            타입: {arthurFilterType}
                            <button
                              onClick={() => setArthurFilterType('all')}
                              className="ml-1 text-purple-600 hover:text-purple-800"
                            >
                              ×
                            </button>
                          </span>
                        )}
                        {arthurFilterStatus !== 'all' && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
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
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                            액션: {arthurFilterAction}
                            <button
                              onClick={() => setArthurFilterAction('all')}
                              className="ml-1 text-blue-600 hover:text-blue-800"
                            >
                              ×
                            </button>
                          </span>
                        )}
                        {arthurSearchText.trim() && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs">
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
                          className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800 underline"
                        >
                          모든 필터 초기화
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {arthurRules.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-gray-500 mb-4">Arthur AI 규칙이 없습니다.</div>
                    <button
                      onClick={async () => {
                        try {
                          setArthurLoading(true);
                          await axios.post('http://localhost:8009/api/v1/arthur/rules/samples');
                          alert('샘플 규칙이 생성되었습니다!');
                          loadArthurRules();
                        } catch (error) {
                          console.error('샘플 규칙 생성 실패:', error);
                          alert('샘플 규칙 생성에 실패했습니다.');
                        } finally {
                          setArthurLoading(false);
                        }
                      }}
                      disabled={arthurLoading}
                      className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50"
                    >
                      📋 샘플 규칙 생성
                    </button>
                  </div>
                ) : (
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
                          className="text-sm text-purple-600 hover:text-purple-800 underline"
                        >
                          필터 초기화
                        </button>
                      </div>
                    ) : (
                      getFilteredArthurRules().map((rule, index) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-3">
                            <span className="text-lg">
                              {rule.type === 'toxicity' ? '⚠️' : 
                               rule.type === 'pii' ? '🔒' :
                               rule.type === 'bias' ? '⚖️' : 
                               rule.type === 'hallucination' ? '🌀' : '🛡️'}
                            </span>
                            <div>
                              <h4 className="font-medium">{rule.name}</h4>
                              <p className="text-sm text-gray-600">{rule.description}</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              rule.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {rule.enabled ? '활성' : '비활성'}
                            </span>
                            <span className="text-sm text-gray-500">
                              임계값: {(rule.threshold * 100).toFixed(0)}%
                            </span>
                            <div className="flex space-x-1 ml-2">
                              <button
                                onClick={() => {
                                  setEditingArthurRule(rule);
                                  setNewArthurRule({
                                    name: rule.name,
                                    type: rule.type,
                                    description: rule.description,
                                    threshold: rule.threshold,
                                    action: rule.action,
                                    custom_patterns: rule.custom_patterns || [''],
                                    examples: rule.examples || ['']
                                  });
                                  setShowArthurRuleForm(true);
                                }}
                                className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded hover:bg-blue-200"
                                title="규칙 편집"
                              >
                                ✏️
                              </button>
                              <button
                                onClick={() => deleteArthurRule(rule.id, rule.name)}
                                className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200"
                                title="규칙 삭제"
                              >
                                🗑️
                              </button>
                            </div>
                          </div>
                        </div>
                        {rule.custom_patterns?.length > 0 && (
                          <div className="mt-2">
                            <div className="text-xs text-gray-500 mb-1">감지 패턴:</div>
                            <div className="flex flex-wrap gap-1">
                              {rule.custom_patterns.slice(0, 3).map((pattern, idx) => (
                                <span key={idx} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs font-mono">
                                  {pattern.length > 20 ? pattern.substring(0, 20) + '...' : pattern}
                                </span>
                              ))}
                              {rule.custom_patterns.length > 3 && (
                                <span className="bg-gray-100 text-gray-500 px-2 py-1 rounded text-xs">
                                  +{rule.custom_patterns.length - 3}개 더
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Arthur AI Text Evaluation */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <h3 className="text-lg font-semibold">텍스트 평가</h3>
                <p className="text-sm text-gray-600 mt-1">Arthur AI를 사용한 실시간 텍스트 분석</p>
              </div>
              <div className="p-6">
                <div className="mb-4">
                  <label htmlFor="arthur-test-input" className="block text-sm font-medium text-gray-700 mb-2">
                    평가할 텍스트를 입력하세요:
                  </label>
                  <textarea
                    id="arthur-test-input"
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    placeholder="예: 이것은 테스트 텍스트입니다..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    rows={4}
                  />
                </div>
                <button
                  onClick={async () => {
                    if (!testInput.trim()) {
                      alert('평가할 텍스트를 입력해주세요.');
                      return;
                    }
                    try {
                      setIsTestLoading(true);
                      const response = await axios.post('http://localhost:8009/api/v1/arthur/evaluate', {
                        text: testInput,
                        rule_types: ['toxicity', 'pii', 'bias', 'hallucination']
                      });
                      setTestResult(response.data);
                    } catch (error) {
                      console.error('텍스트 평가 실패:', error);
                      alert('텍스트 평가에 실패했습니다.');
                    } finally {
                      setIsTestLoading(false);
                    }
                  }}
                  disabled={isTestLoading || !testInput.trim()}
                  className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50"
                >
                  {isTestLoading ? '평가 중...' : '🛡️ Arthur AI 평가'}
                </button>

                {testResult && (
                  <div className="mt-6 p-4 border rounded-lg bg-gray-50">
                    <h4 className="font-medium mb-3">평가 결과:</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">전체 점수:</span>
                        <span className={`text-sm font-medium ${
                          testResult.overall_risk_score > 0.7 ? 'text-red-600' :
                          testResult.overall_risk_score > 0.4 ? 'text-orange-600' : 'text-green-600'
                        }`}>
                          {(testResult.overall_risk_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">위험도:</span>
                        <span className={`text-sm font-medium px-2 py-1 rounded ${
                          testResult.risk_level === 'high' ? 'bg-red-100 text-red-800' :
                          testResult.risk_level === 'medium' ? 'bg-orange-100 text-orange-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {testResult.risk_level === 'high' ? '높음' :
                           testResult.risk_level === 'medium' ? '보통' : '낮음'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">처리 액션:</span>
                        <span className="text-sm font-medium">{testResult.action}</span>
                      </div>
                      {testResult.triggered_rules?.length > 0 && (
                        <div className="mt-3">
                          <div className="text-sm text-gray-600 mb-2">감지된 규칙:</div>
                          <div className="space-y-1">
                            {testResult.triggered_rules.map((rule, idx) => (
                              <div key={idx} className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">
                                {rule}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {testResult.explanation && (
                        <div className="mt-3">
                          <div className="text-sm text-gray-600 mb-1">설명:</div>
                          <div className="text-sm text-gray-800">{testResult.explanation}</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Arthur AI Metrics */}
            {arthurMetrics && (
              <div className="bg-white rounded-lg shadow-sm border">
                <div className="px-6 py-4 border-b">
                  <h3 className="text-lg font-semibold">Arthur AI 메트릭</h3>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{arthurMetrics.total_evaluations}</div>
                      <div className="text-sm text-gray-600">총 평가 횟수</div>
                    </div>
                    <div className="bg-red-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">{arthurMetrics.high_risk_detections}</div>
                      <div className="text-sm text-gray-600">고위험 감지</div>
                    </div>
                    <div className="bg-orange-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">{arthurMetrics.medium_risk_detections}</div>
                      <div className="text-sm text-gray-600">중위험 감지</div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{arthurMetrics.avg_response_time_ms}ms</div>
                      <div className="text-sm text-gray-600">평균 응답시간</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Arthur AI 규칙 생성/편집 모달 */}
            {showArthurRuleForm && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold">
                      {editingArthurRule ? '규칙 편집' : '새 Arthur AI 규칙 추가'}
                    </h3>
                    <button
                      onClick={() => {
                        setShowArthurRuleForm(false);
                        setEditingArthurRule(null);
                        setNewArthurRule({
                          name: '',
                          type: 'toxicity',
                          description: '',
                          threshold: 0.8,
                          action: 'block',
                          custom_patterns: [''],
                          examples: ['']
                        });
                      }}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      ✕
                    </button>
                  </div>

                  <form onSubmit={(e) => {
                    e.preventDefault();
                    if (editingArthurRule) {
                      updateArthurRule(editingArthurRule.id, {
                        name: newArthurRule.name,
                        description: newArthurRule.description,
                        threshold: newArthurRule.threshold,
                        action: newArthurRule.action,
                        custom_patterns: newArthurRule.custom_patterns.filter(p => p.trim()),
                        examples: newArthurRule.examples.filter(e => e.trim())
                      });
                    } else {
                      createArthurRule();
                    }
                  }} className="space-y-4">

                    {/* 기본 정보 */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          규칙 이름 *
                        </label>
                        <input
                          type="text"
                          required
                          value={newArthurRule.name}
                          onChange={(e) => setNewArthurRule({...newArthurRule, name: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                          placeholder="예: 한국어 스팸 탐지"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          규칙 타입 *
                        </label>
                        <select
                          value={newArthurRule.type}
                          onChange={(e) => setNewArthurRule({...newArthurRule, type: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="toxicity">독성 콘텐츠</option>
                          <option value="pii">개인정보</option>
                          <option value="bias">편견</option>
                          <option value="hallucination">환각</option>
                          <option value="content_filter">콘텐츠 필터</option>
                          <option value="spam">스팸</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        설명
                      </label>
                      <textarea
                        value={newArthurRule.description}
                        onChange={(e) => setNewArthurRule({...newArthurRule, description: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                        rows={2}
                        placeholder="규칙에 대한 설명을 입력하세요"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          임계값 ({(newArthurRule.threshold * 100).toFixed(0)}%)
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.05"
                          value={newArthurRule.threshold}
                          onChange={(e) => setNewArthurRule({...newArthurRule, threshold: parseFloat(e.target.value)})}
                          className="w-full"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          액션
                        </label>
                        <select
                          value={newArthurRule.action}
                          onChange={(e) => setNewArthurRule({...newArthurRule, action: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="block">차단</option>
                          <option value="flag">플래그</option>
                          <option value="modify">수정</option>
                          <option value="alert">알림</option>
                        </select>
                      </div>
                    </div>

                    {/* 패턴 관리 */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        감지 패턴
                      </label>
                      {newArthurRule.custom_patterns.map((pattern, index) => (
                        <div key={index} className="flex items-center space-x-2 mb-2">
                          <input
                            type="text"
                            value={pattern}
                            onChange={(e) => updatePatternInArthurRule(index, e.target.value)}
                            placeholder="예: regex: (스팸|광고|무료)"
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                          <button
                            type="button"
                            onClick={() => removePatternFromArthurRule(index)}
                            className="text-red-600 hover:text-red-800 px-2 py-1"
                            title="패턴 삭제"
                          >
                            🗑️
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={() => addPatternToArthurRule()}
                        className="text-purple-600 hover:text-purple-800 text-sm"
                      >
                        ➕ 패턴 추가
                      </button>
                    </div>

                    {/* 예시 관리 */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        예시 텍스트
                      </label>
                      {newArthurRule.examples.map((example, index) => (
                        <div key={index} className="flex items-center space-x-2 mb-2">
                          <input
                            type="text"
                            value={example}
                            onChange={(e) => updatePatternInArthurRule(index, e.target.value, true)}
                            placeholder="예: 축하합니다! 1억원 당첨되셨습니다"
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                          <button
                            type="button"
                            onClick={() => removePatternFromArthurRule(index, true)}
                            className="text-red-600 hover:text-red-800 px-2 py-1"
                            title="예시 삭제"
                          >
                            🗑️
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={() => addPatternToArthurRule(true)}
                        className="text-purple-600 hover:text-purple-800 text-sm"
                      >
                        ➕ 예시 추가
                      </button>
                    </div>

                    {/* 버튼 */}
                    <div className="flex justify-end space-x-2 pt-4 border-t">
                      <button
                        type="button"
                        onClick={() => {
                          setShowArthurRuleForm(false);
                          setEditingArthurRule(null);
                          setNewArthurRule({
                            name: '',
                            type: 'toxicity',
                            description: '',
                            threshold: 0.8,
                            action: 'block',
                            custom_patterns: [''],
                            examples: ['']
                          });
                        }}
                        className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                      >
                        취소
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                      >
                        {editingArthurRule ? '수정' : '생성'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="space-y-6">
            {stats && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <div className="text-2xl font-bold text-blue-600">{stats.total_checks.toLocaleString()}</div>
                    <div className="text-sm text-gray-600">총 검사 횟수</div>
                  </div>
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <div className="text-2xl font-bold text-red-600">{stats.blocked_content}</div>
                    <div className="text-sm text-gray-600">차단된 콘텐츠</div>
                  </div>
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <div className="text-2xl font-bold text-orange-600">{stats.flagged_content}</div>
                    <div className="text-sm text-gray-600">플래그된 콘텐츠</div>
                  </div>
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <div className="text-2xl font-bold text-green-600">{stats.success_rate}%</div>
                    <div className="text-sm text-gray-600">성공률</div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow-sm border">
                  <div className="px-6 py-4 border-b">
                    <h2 className="text-lg font-semibold">주요 위반 규칙</h2>
                  </div>
                  <div className="p-6">
                    {stats.top_violations && stats.top_violations.length > 0 ? (
                      <div className="space-y-3">
                        {stats.top_violations.map((violation, index) => (
                          <div key={index} className="flex items-center justify-between">
                            <span className="font-medium">{violation.rule}</span>
                            <span className="bg-gray-100 px-2 py-1 rounded text-sm">{violation.count}건</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-center py-4">위반 내역이 없습니다.</p>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'rbac' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">RBAC 권한 관리</h2>
                  <button
                    onClick={loadRbacData}
                    disabled={rbacLoading}
                    className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 disabled:bg-gray-400 text-sm"
                  >
                    {rbacLoading ? '로딩 중...' : '🔄 새로고침'}
                  </button>
                </div>
              </div>
              
              <div className="p-6">
                <div className="flex space-x-1 mb-6">
                  {[
                    { id: 'users', name: '사용자 관리', icon: '👤' },
                    { id: 'roles', name: '역할 관리', icon: '🛡️' },
                    { id: 'policies', name: '정책 관리', icon: '📋' }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setRbacActiveTab(tab.id)}
                      className={`px-4 py-2 text-sm font-medium rounded-md ${
                        rbacActiveTab === tab.id
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <span className="mr-2">{tab.icon}</span>
                      {tab.name}
                    </button>
                  ))}
                </div>

                {rbacActiveTab === 'users' && (
                  <div className="space-y-6">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-medium mb-3">새 사용자 추가</h3>
                      <form onSubmit={handleCreateUser} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <input
                            type="text"
                            placeholder="사용자명"
                            value={newUser.username}
                            onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                          />
                          <input
                            type="email"
                            placeholder="이메일"
                            value={newUser.email}
                            onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                          />
                          <input
                            type="text"
                            placeholder="이름"
                            value={newUser.full_name}
                            onChange={(e) => setNewUser({...newUser, full_name: e.target.value})}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                          />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <select 
                            value={newUser.department}
                            onChange={(e) => setNewUser({...newUser, department: e.target.value})}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="">부서 선택</option>
                            <option value="IT">IT</option>
                            <option value="HR">HR</option>
                            <option value="FINANCE">FINANCE</option>
                            <option value="SECURITY">SECURITY</option>
                          </select>
                          <input
                            type="text"
                            placeholder="직책 (선택사항)"
                            value={newUser.job_title}
                            onChange={(e) => setNewUser({...newUser, job_title: e.target.value})}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          <select 
                            value={newUser.clearance_level}
                            onChange={(e) => setNewUser({...newUser, clearance_level: e.target.value})}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="public">Public (공개)</option>
                            <option value="internal">Internal (내부)</option>
                            <option value="confidential">Confidential (기밀)</option>
                            <option value="secret">Secret (비밀)</option>
                            <option value="top_secret">Top Secret (극비)</option>
                          </select>
                        </div>
                        <div className="flex justify-between items-center">
                          <div className="text-sm text-gray-500">
                            * 패스워드는 자동으로 생성됩니다 (기본값: defaultPassword123)
                          </div>
                          <button 
                            type="submit"
                            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
                          >
                            사용자 추가
                          </button>
                        </div>
                      </form>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="min-w-full border border-gray-200 rounded-lg overflow-hidden">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">사용자</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">이메일</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">부서</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">보안등급</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">역할</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">상태</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">작업</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {users.length === 0 ? (
                            <tr>
                              <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                                등록된 사용자가 없습니다.
                                <br />
                                <span className="text-xs text-gray-400">Permission Service가 실행 중인지 확인해주세요.</span>
                              </td>
                            </tr>
                          ) : (
                            users.map((user) => (
                              <tr key={user.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 text-sm">
                                  <div>
                                    <div className="font-medium">{user.username}</div>
                                    {user.full_name && <div className="text-gray-500 text-xs">{user.full_name}</div>}
                                  </div>
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600">{user.email}</td>
                                <td className="px-4 py-3 text-sm">{user.department || '-'}</td>
                                <td className="px-4 py-3 text-sm">
                                  <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 capitalize">
                                    {user.clearance_level}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  {user.roles.length > 0 ? (
                                    <div className="flex flex-wrap gap-1">
                                      {user.roles.map((role, idx) => (
                                        <span key={idx} className="px-2 py-1 text-xs rounded bg-green-100 text-green-800">
                                          {role}
                                        </span>
                                      ))}
                                    </div>
                                  ) : (
                                    <span className="text-gray-400">역할 없음</span>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  <span className={`px-2 py-1 text-xs rounded-full ${
                                    user.is_active 
                                      ? 'bg-green-100 text-green-800' 
                                      : 'bg-red-100 text-red-800'
                                  }`}>
                                    {user.is_active ? '활성' : '비활성'}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  <div className="flex space-x-2">
                                    <button className="text-blue-600 hover:text-blue-800 text-xs">편집</button>
                                    <button 
                                      onClick={() => deleteUser(user.id)}
                                      className="text-red-600 hover:text-red-800 text-xs"
                                    >
                                      삭제
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {rbacActiveTab === 'roles' && (
                  <div className="space-y-6">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-medium mb-3">새 역할 추가</h3>
                      <form onSubmit={handleCreateRole} className="space-y-3">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <input
                            type="text"
                            placeholder="역할 이름"
                            value={newRole.name}
                            onChange={(e) => setNewRole({...newRole, name: e.target.value})}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                          />
                          <input
                            type="text"
                            placeholder="설명"
                            value={newRole.description}
                            onChange={(e) => setNewRole({...newRole, description: e.target.value})}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">권한 선택</label>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                            {['document:read', 'document:write', 'document:delete', 'system:admin', 'user:manage', 'role:manage', 'policy:manage', 'system:config'].map((perm) => (
                              <label key={perm} className="flex items-center space-x-2">
                                <input 
                                  type="checkbox" 
                                  className="rounded"
                                  checked={newRole.permissions.includes(perm)}
                                  onChange={() => handlePermissionToggle(perm)}
                                />
                                <span className="text-sm">{perm}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                        <div className="flex justify-end">
                          <button 
                            type="submit"
                            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
                          >
                            역할 추가
                          </button>
                        </div>
                      </form>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {roles.length === 0 ? (
                        <div className="col-span-full text-center text-gray-500 py-8">
                          등록된 역할이 없습니다.
                          <br />
                          <span className="text-xs text-gray-400">Permission Service가 실행 중인지 확인해주세요.</span>
                        </div>
                      ) : (
                        roles.map((role) => (
                          <div key={role.id} className="bg-white border border-gray-200 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="font-medium">{role.name}</h4>
                              <div className="flex space-x-1">
                                <button className="text-blue-600 hover:text-blue-800 text-xs">편집</button>
                                <button 
                                  onClick={() => deleteRole(role.id)}
                                  className="text-red-600 hover:text-red-800 text-xs"
                                >
                                  삭제
                                </button>
                              </div>
                            </div>
                            <p className="text-sm text-gray-600 mb-3">{role.description}</p>
                            <div className="space-y-2">
                              <span className="text-xs font-medium text-gray-500">권한:</span>
                              <div className="flex flex-wrap gap-1">
                                {role.permissions.map((perm, idx) => (
                                  <span key={idx} className="px-2 py-1 text-xs rounded bg-purple-100 text-purple-800">
                                    {perm}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}

                {rbacActiveTab === 'policies' && (
                  <div className="space-y-6">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-medium mb-3">새 정책 추가</h3>
                      <form onSubmit={createPolicy} className="space-y-3">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <input
                            type="text"
                            placeholder="정책 이름"
                            value={newPolicy.name}
                            onChange={(e) => setNewPolicy({...newPolicy, name: e.target.value})}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                          />
                          <input
                            type="text"
                            placeholder="설명"
                            value={newPolicy.description}
                            onChange={(e) => setNewPolicy({...newPolicy, description: e.target.value})}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                          />
                        </div>
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <label className="block text-sm font-medium text-gray-700">정책 규칙 (JSON)</label>
                            <div className="flex items-center space-x-2">
                              <button
                                type="button"
                                onClick={() => setShowTemplateHelp(!showTemplateHelp)}
                                className="text-xs text-blue-600 hover:text-blue-800"
                              >
                                {showTemplateHelp ? '도움말 숨기기' : '템플릿 도움말'}
                              </button>
                              <select
                                onChange={(e) => e.target.value && applyTemplate(e.target.value as keyof typeof policyTemplates)}
                                className="text-xs px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                                defaultValue=""
                              >
                                <option value="">템플릿 선택</option>
                                <option value="basicAccess">🔍 기본 접근 권한</option>
                                <option value="adminAccess">👑 관리자 접근 권한</option>
                                <option value="departmentAccess">🏢 부서별 접근 권한</option>
                                <option value="fileAccess">📁 파일 접근 권한</option>
                                <option value="apiAccess">🔌 API 호출 제한</option>
                              </select>
                            </div>
                          </div>
                          
                          {showTemplateHelp && (
                            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-md text-xs">
                              <h4 className="font-medium text-blue-800 mb-2">📋 템플릿 설명</h4>
                              <div className="space-y-2 text-blue-700">
                                <div><strong>🔍 기본 접근 권한:</strong> 모든 리소스에 대한 읽기 권한</div>
                                <div><strong>👑 관리자 접근 권한:</strong> 전체 CRUD 권한 + IP 제한</div>
                                <div><strong>🏢 부서별 접근 권한:</strong> 부서별 리소스 + 시간 제한</div>
                                <div><strong>📁 파일 접근 권한:</strong> 개인 파일 + 파일 형식 제한</div>
                                <div><strong>🔌 API 호출 제한:</strong> API 속도 제한 + 인증 필수</div>
                              </div>
                              <div className="mt-2 pt-2 border-t border-blue-200">
                                <strong>JSON 구조:</strong> resource (리소스), action (동작), condition (조건)
                              </div>
                            </div>
                          )}
                          <textarea
                            rows={8}
                            placeholder='{"resource": "*", "action": "read", "condition": {"department": "IT"}}'
                            value={newPolicy.rules}
                            onChange={(e) => {
                              const value = e.target.value;
                              setNewPolicy({...newPolicy, rules: value});
                              validateJSON(value);
                            }}
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 font-mono text-sm ${
                              jsonError 
                                ? 'border-red-300 focus:ring-red-500 bg-red-50' 
                                : 'border-gray-300 focus:ring-blue-500'
                            }`}
                          />
                          {jsonError && (
                            <div className="mt-1 text-xs text-red-600 flex items-center">
                              <span className="mr-1">⚠️</span>
                              {jsonError}
                            </div>
                          )}
                          {!jsonError && newPolicy.rules.trim() && (
                            <div className="mt-1 text-xs text-green-600 flex items-center">
                              <span className="mr-1">✅</span>
                              올바른 JSON 형식입니다.
                            </div>
                          )}
                          <div className="mt-2 text-xs text-gray-500">
                            <strong>팁:</strong> 위의 템플릿을 선택하여 빠르게 시작하거나, 직접 JSON을 작성할 수 있습니다.
                          </div>
                        </div>
                        <div className="flex justify-between items-center">
                          <label className="flex items-center space-x-2">
                            <input 
                              type="checkbox" 
                              className="rounded"
                              checked={newPolicy.is_active}
                              onChange={(e) => setNewPolicy({...newPolicy, is_active: e.target.checked})}
                            />
                            <span className="text-sm">활성화</span>
                          </label>
                          <button 
                            type="submit"
                            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
                          >
                            정책 추가
                          </button>
                        </div>
                      </form>
                    </div>

                    <div className="space-y-4">
                      {policies.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                          등록된 정책이 없습니다.
                          <br />
                          <span className="text-xs text-gray-400">Permission Service가 실행 중인지 확인해주세요.</span>
                        </div>
                      ) : (
                        policies.map((policy) => (
                          <div key={policy.id} className="bg-white border border-gray-200 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center space-x-3">
                                <h4 className="font-medium">{policy.name}</h4>
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  policy.is_active 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-red-100 text-red-800'
                                }`}>
                                  {policy.is_active ? '활성' : '비활성'}
                                </span>
                              </div>
                              <div className="flex space-x-2">
                                <button className="text-blue-600 hover:text-blue-800 text-xs">편집</button>
                                <button 
                                  onClick={() => deletePolicy(policy.id)}
                                  className="text-red-600 hover:text-red-800 text-xs"
                                >
                                  삭제
                                </button>
                              </div>
                            </div>
                            <p className="text-sm text-gray-600 mb-3">{policy.description}</p>
                            <div>
                              <span className="text-xs font-medium text-gray-500">규칙:</span>
                              <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                                {JSON.stringify(policy.rules, null, 2)}
                              </pre>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Document Detail Modal */}
      {showDetailModal && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] w-full flex flex-col">
            <div className="flex items-center justify-between p-6 border-b">
              <div>
                <h2 className="text-xl font-semibold">📄 문서 상세보기</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {selectedDocument.filename || selectedDocument.title}
                </p>
              </div>
              <button
                onClick={closeDetailModal}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ✕
              </button>
            </div>
            
            <div className="flex-1 overflow-hidden p-6">
              {contentLoading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600">문서 내용을 불러오는 중...</span>
                </div>
              ) : (
                <div className="h-full">
                  <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">파일명:</span>
                      <span className="ml-2 text-gray-600">{selectedDocument.filename || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">업로드 날짜:</span>
                      <span className="ml-2 text-gray-600">
                        {selectedDocument.created_at 
                          ? new Date(selectedDocument.created_at).toLocaleString('ko-KR')
                          : 'N/A'
                        }
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">파일 크기:</span>
                      <span className="ml-2 text-gray-600">
                        {selectedDocument.file_size 
                          ? `${(selectedDocument.file_size / 1024).toFixed(1)} KB`
                          : 'N/A'
                        }
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">청크 수:</span>
                      <span className="ml-2 text-gray-600">{selectedDocument.chunk_count || 0}개</span>
                    </div>
                  </div>
                  
                  <div className="border-t pt-4 h-full">
                    <h3 className="font-medium mb-3">📝 문서 내용</h3>
                    <div className="bg-gray-50 rounded-lg p-4 h-96 overflow-y-auto">
                      <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
                        {documentContent || '내용을 불러올 수 없습니다.'}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Duplicate Warning Modal */}
      {showDuplicateModal && duplicateInfo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-yellow-100 rounded-full mb-4">
                <span className="text-2xl">⚠️</span>
              </div>
              
              <h2 className="text-lg font-semibold text-center mb-3">파일 중복 경고</h2>
              
              <div className="mb-4 p-4 bg-yellow-50 rounded-lg">
                <p className="text-sm text-gray-700 mb-2">
                  동일한 파일명의 문서가 이미 존재합니다:
                </p>
                <p className="font-medium text-gray-900">
                  📄 {duplicateInfo.filename}
                </p>
                {duplicateInfo.existing_document && (
                  <p className="text-xs text-gray-500 mt-2">
                    기존 파일 업로드 날짜: {new Date(duplicateInfo.existing_document.created_at).toLocaleString('ko-KR')}
                  </p>
                )}
              </div>
              
              <p className="text-sm text-gray-600 text-center mb-6">
                업로드를 중단하거나 파일명을 변경한 후 다시 시도해주세요.
              </p>
              
              <div className="flex justify-center">
                <button
                  onClick={closeDuplicateModal}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  확인
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chunk Viewer Modal */}
      {showChunkModal && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl max-h-[90vh] w-full flex flex-col">
            <div className="flex items-center justify-between p-6 border-b">
              <div>
                <h2 className="text-xl font-semibold">🧩 문서 청크 보기</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {selectedDocument.filename || selectedDocument.title}
                </p>
              </div>
              <button
                onClick={closeChunkModal}
                className="text-gray-400 hover:text-gray-600 text-xl font-bold"
              >
                ✕
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6">
              {chunksLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">청크를 불러오는 중...</p>
                </div>
              ) : documentChunks.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  이 문서에서 청크를 찾을 수 없습니다.
                  <br />
                  <span className="text-xs text-gray-400">문서가 아직 처리되지 않았거나 청크 정보가 없습니다.</span>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-blue-50 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between text-sm">
                      <div className="font-medium">
                        총 {documentChunks.length}개 청크
                      </div>
                      <div className="text-blue-600">
                        {selectedDocument.id.startsWith('doc_') ? 'Korean RAG 처리' : '일반 텍스트 처리'}
                      </div>
                    </div>
                  </div>
                  
                  {documentChunks.map((chunk, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4 border">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded">
                            청크 #{index + 1}
                          </span>
                          {chunk.similarity_score && (
                            <span className="bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded">
                              유사도: {(chunk.similarity_score * 100).toFixed(1)}%
                            </span>
                          )}
                          {chunk.chunk_id && (
                            <span className="bg-gray-100 text-gray-600 text-xs font-medium px-2 py-1 rounded">
                              ID: {chunk.chunk_id}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          {chunk.content ? `${chunk.content.length} 글자` : '내용 없음'}
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                        {chunk.content || chunk.text || '청크 내용을 불러올 수 없습니다.'}
                      </div>
                      
                      {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <div className="text-xs text-gray-600 mb-2">메타데이터:</div>
                          <div className="text-xs text-gray-500">
                            {JSON.stringify(chunk.metadata, null, 2)}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                  
                  <div className="text-center text-xs text-gray-500 mt-6 pt-4 border-t">
                    💡 이 청크들은 벡터 검색 시 유사도 기반으로 검색됩니다.
                    {selectedDocument.id.startsWith('doc_') && (
                      <div className="mt-1">
                        Korean RAG 서비스를 통해 KURE-v1 모델로 임베딩되어 Milvus에 저장됩니다.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex justify-end p-6 border-t bg-gray-50">
              <button
                onClick={closeChunkModal}
                className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Search Result Modal */}
      {showSearchResultModal && searchResultData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl max-h-[90vh] w-full flex flex-col">
            <div className="flex items-center justify-between p-6 border-b">
              <div>
                <h2 className="text-xl font-semibold">🔍 검색 결과 상세</h2>
                <p className="text-sm text-gray-600 mt-1">
                  "{searchResultData.query}" 검색 결과
                </p>
              </div>
              <button
                onClick={() => setShowSearchResultModal(false)}
                className="text-gray-400 hover:text-gray-600 text-xl font-bold"
              >
                ✕
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6">
              {/* Search Summary */}
              <div className="bg-blue-50 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">🎯</span>
                    <div>
                      <div className="font-semibold text-blue-800">
                        검색 완료
                      </div>
                      <div className="text-sm text-blue-600">
                        {searchResultData.has_context ? (
                          <>
                            <span className="font-medium">{searchResultData.context_chunks_count}개</span> 
                            관련 청크를 찾았습니다
                          </>
                        ) : (
                          '관련 문서를 찾지 못했습니다'
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    <div className="text-gray-600">유사도 임계값</div>
                    <div className="font-medium text-blue-800">
                      {(searchResultData.similarity_threshold * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
                
                {searchResultData.has_context && (
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <div className="text-xs text-blue-700 font-medium mb-2">
                      생성된 RAG 컨텍스트:
                    </div>
                    <div className="text-sm text-blue-800 bg-white p-3 rounded border max-h-32 overflow-y-auto">
                      {searchResultData.context}
                    </div>
                  </div>
                )}
              </div>

              {/* Relevant Chunks */}
              {searchResultData.has_context && searchResultData.relevant_chunks && searchResultData.relevant_chunks.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 mb-4">
                    <span className="text-lg">🧩</span>
                    <h3 className="text-lg font-semibold">관련 청크 상세</h3>
                    <span className="bg-gray-100 text-gray-800 text-sm px-2 py-1 rounded">
                      {searchResultData.relevant_chunks.length}개
                    </span>
                  </div>
                  
                  {searchResultData.relevant_chunks.map((chunk, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg border overflow-hidden">
                      {/* Chunk Header */}
                      <div className="bg-gradient-to-r from-blue-100 to-blue-50 p-4 border-b">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <span className="bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded">
                              #{index + 1}
                            </span>
                            <div>
                              <div className="font-medium text-gray-800">
                                📄 {
                                  chunk.metadata?.original_metadata?.title || 
                                  chunk.metadata?.filename || 
                                  chunk.metadata?.title || 
                                  '알 수 없는 파일'
                                }
                              </div>
                              {chunk.metadata?.document_id && (
                                <div className="text-xs text-gray-500 mt-1">
                                  ID: {chunk.metadata.document_id}
                                </div>
                              )}
                              {/* 유사 문구 표시 */}
                              <div className="text-xs text-blue-600 mt-1 font-medium">
                                📝 유사 문구: "{searchResultData.query}"와 관련된 내용
                              </div>
                            </div>
                          </div>
                          
                          {/* Similarity Score */}
                          {chunk.similarity_score !== undefined && (
                            <div className="text-right">
                              <div className="flex items-center space-x-2">
                                <span className="text-xs text-gray-600">유사도</span>
                                <div className="flex items-center space-x-1">
                                  <div className={`w-3 h-3 rounded-full ${
                                    chunk.similarity_score > 0.8 ? 'bg-green-500' :
                                    chunk.similarity_score > 0.6 ? 'bg-yellow-500' : 'bg-orange-500'
                                  }`}></div>
                                  <span className="font-bold text-sm">
                                    {(chunk.similarity_score * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Chunk Content */}
                      <div className="p-4">
                        <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                          {chunk.content}
                        </div>
                        
                        {/* Additional Metadata */}
                        {chunk.metadata && Object.keys(chunk.metadata).some(key => 
                          !['filename', 'title', 'document_id'].includes(key)
                        ) && (
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <div className="text-xs text-gray-600 mb-2 font-medium">추가 정보:</div>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              {Object.entries(chunk.metadata)
                                .filter(([key]) => !['filename', 'title', 'document_id'].includes(key))
                                .map(([key, value]) => (
                                <div key={key} className="flex">
                                  <span className="font-medium text-gray-600 w-20 capitalize">{key}:</span>
                                  <span className="text-gray-500 truncate">
                                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Action Buttons */}
                        <div className="mt-4 pt-3 border-t border-gray-200 flex space-x-2">
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(chunk.content);
                              alert('청크 내용이 클립보드에 복사되었습니다.');
                            }}
                            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded transition-colors"
                          >
                            📋 복사
                          </button>
                          {chunk.metadata?.document_id && (
                            <button
                              onClick={() => {
                                const input = document.querySelector('input[placeholder*="검색할 문서 ID"]') as HTMLInputElement;
                                if (input) {
                                  input.value = chunk.metadata.document_id;
                                }
                                setShowSearchResultModal(false);
                              }}
                              className="text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-1 rounded transition-colors"
                            >
                              📄 문서 보기
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {/* Search Tips */}
                  <div className="mt-6 bg-yellow-50 rounded-lg p-4">
                    <div className="flex items-start space-x-2">
                      <span className="text-yellow-600 mt-0.5">💡</span>
                      <div className="text-sm">
                        <div className="font-medium text-yellow-800 mb-2">검색 팁:</div>
                        <ul className="text-yellow-700 space-y-1 text-xs">
                          <li>• 더 구체적인 키워드를 사용하면 정확도가 향상됩니다</li>
                          <li>• 유사도 점수가 높을수록 질문과 더 관련성이 높은 내용입니다</li>
                          <li>• Korean RAG은 KURE-v1 모델을 사용하여 한국어에 최적화되어 있습니다</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🔍</div>
                  <div className="text-lg font-medium text-gray-700 mb-2">
                    관련 문서를 찾지 못했습니다
                  </div>
                  <div className="text-sm text-gray-500 max-w-md mx-auto">
                    다른 키워드로 검색해보시거나, 문서를 먼저 업로드한 후 다시 시도해보세요.
                  </div>
                </div>
              )}
            </div>
            
            {/* Modal Footer */}
            <div className="flex justify-between items-center p-6 border-t bg-gray-50">
              <div className="text-sm text-gray-600">
                🚀 Korean RAG Service를 통한 검색 결과
              </div>
              <button
                onClick={() => setShowSearchResultModal(false)}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rule Detail Modal */}
      {showRuleDetailModal && selectedRule && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] w-full flex flex-col">
              <div className="flex items-center justify-between p-6 border-b">
                <div>
                  <h2 className="text-xl font-semibold">⚙️ 규칙 상세 정보</h2>
                  <p className="text-sm text-gray-600 mt-1">
                    {selectedRule.name}
                  </p>
                </div>
                <button
                  onClick={() => setShowRuleDetailModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-xl font-bold"
                >
                  ✕
                </button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6">
                  <div className="space-y-6">
                    {/* Rule Overview */}
                    <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <div className="text-2xl">🛡️</div>
                          <div>
                            <h3 className="font-bold text-blue-800">{selectedRule.name}</h3>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className={`text-xs px-2 py-1 rounded ${
                                selectedRule.type === 'toxicity' ? 'bg-red-100 text-red-700' :
                                selectedRule.type === 'pii' ? 'bg-yellow-100 text-yellow-700' :
                                selectedRule.type === 'bias' ? 'bg-purple-100 text-purple-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {selectedRule.type === 'toxicity' ? '독성 콘텐츠' :
                                 selectedRule.type === 'pii' ? '개인정보' :
                                 selectedRule.type === 'bias' ? '편향성' : '콘텐츠 필터'}
                              </span>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                selectedRule.enabled
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-gray-100 text-gray-600'
                              }`}>
                                {selectedRule.enabled ? '🟢 활성화' : '🔴 비활성화'}
                              </span>
                              {ruleDetails && (
                                <span className={`text-xs px-2 py-1 rounded text-white ${
                                  ruleDetails.risk_level === 'high' ? 'bg-red-500' :
                                  ruleDetails.risk_level === 'medium' ? 'bg-orange-500' : 'bg-green-500'
                                }`}>
                                  위험도: {ruleDetails.risk_level === 'high' ? '높음' :
                                          ruleDetails.risk_level === 'medium' ? '보통' : '낮음'}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        {/* Rule Actions */}
                        <div className="flex space-x-2">
                          <button
                            onClick={() => {
                              setEditingRule(selectedRule);
                              setShowRuleDetailModal(false);
                            }}
                            className="bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 text-sm"
                          >
                            ✏️ 편집
                          </button>
                          <button
                            onClick={() => {
                              toggleRule(selectedRule.id, !selectedRule.enabled);
                              setSelectedRule({...selectedRule, enabled: !selectedRule.enabled});
                            }}
                            className={`px-3 py-1.5 rounded-md text-sm font-medium ${
                              selectedRule.enabled
                                ? 'bg-gray-600 text-white hover:bg-gray-700'
                                : 'bg-green-600 text-white hover:bg-green-700'
                            }`}
                          >
                            {selectedRule.enabled ? '⏸️ 비활성화' : '▶️ 활성화'}
                          </button>
                        </div>
                      </div>
                      
                      {/* Threshold Control */}
                      <div className="bg-white rounded-lg p-3 mt-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">임계값 설정</span>
                          <span className="text-sm font-bold text-blue-600">{selectedRule.threshold}</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.1"
                          value={selectedRule.threshold}
                          onChange={(e) => {
                            const newThreshold = parseFloat(e.target.value);
                            updateThreshold(selectedRule.id, newThreshold);
                            setSelectedRule({...selectedRule, threshold: newThreshold});
                          }}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>0.0 (관대함)</span>
                          <span>1.0 (엄격함)</span>
                        </div>
                      </div>
                    </div>

                    {/* Rule Description */}
                    {ruleDetails && (
                      <>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <h4 className="font-semibold mb-3 flex items-center">
                            <span className="mr-2">📋</span>
                            규칙 설명
                          </h4>
                          <p className="text-gray-700 leading-relaxed">
                            {ruleDetails.description}
                          </p>
                        </div>

                        {/* Detection Patterns */}
                        {ruleDetails.patterns && ruleDetails.patterns.length > 0 && (
                          <div className="bg-yellow-50 rounded-lg p-4">
                            <h4 className="font-semibold mb-3 flex items-center">
                              <span className="mr-2">🔍</span>
                              감지 패턴
                            </h4>
                            <div className="space-y-2">
                              {ruleDetails.patterns.map((pattern, index) => (
                                <div key={index} className="flex items-center space-x-2">
                                  <span className="w-2 h-2 bg-yellow-400 rounded-full"></span>
                                  <code className="bg-white px-2 py-1 rounded text-sm text-gray-800">
                                    {pattern}
                                  </code>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Examples */}
                        {ruleDetails.examples && ruleDetails.examples.length > 0 && (
                          <div className="bg-red-50 rounded-lg p-4">
                            <h4 className="font-semibold mb-3 flex items-center">
                              <span className="mr-2">⚠️</span>
                              차단 예시
                            </h4>
                            <div className="space-y-2">
                              {ruleDetails.examples.map((example, index) => (
                                <div key={index} className="bg-white p-3 rounded border-l-4 border-red-400">
                                  <div className="text-sm text-gray-700">
                                    {example}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}

                    {/* Rule Statistics */}
                    <div className="bg-green-50 rounded-lg p-4">
                      <h4 className="font-semibold mb-3 flex items-center">
                        <span className="mr-2">📊</span>
                        사용 통계
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">0</div>
                          <div className="text-xs text-gray-600">이번 달 차단</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">0</div>
                          <div className="text-xs text-gray-600">총 검증 수</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-orange-600">0%</div>
                          <div className="text-xs text-gray-600">차단율</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-purple-600">N/A</div>
                          <div className="text-xs text-gray-600">마지막 활성화</div>
                        </div>
                      </div>
                      <div className="mt-3 text-xs text-gray-500 text-center">
                        📌 통계 데이터는 향후 Guardrails 서비스와 연동되어 실시간으로 업데이트됩니다.
                      </div>
                    </div>

                    {/* Technical Details */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-semibold mb-3 flex items-center">
                        <span className="mr-2">🔧</span>
                        기술적 상세
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-700">규칙 ID:</span>
                          <span className="ml-2 font-mono bg-white px-2 py-1 rounded">{selectedRule.id}</span>
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">액션 타입:</span>
                          <span className="ml-2 text-gray-600">{selectedRule.action || 'block'}</span>
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">생성일:</span>
                          <span className="ml-2 text-gray-600">
                            {selectedRule.created_at ? new Date(selectedRule.created_at).toLocaleString('ko-KR') : 'N/A'}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">수정일:</span>
                          <span className="ml-2 text-gray-600">
                            {selectedRule.updated_at ? new Date(selectedRule.updated_at).toLocaleString('ko-KR') : 'N/A'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
              </div>
            
            {/* Modal Footer */}
            <div className="flex justify-between items-center p-6 border-t bg-gray-50">
              <div className="text-sm text-gray-600">
                🛡️ AI 안전 규칙 관리 시스템
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setEditingRule(selectedRule);
                    setShowRuleDetailModal(false);
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  편집하기
                </button>
                <button
                  onClick={() => setShowRuleDetailModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                >
                  닫기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Rule Edit Modal */}
      {editingRule && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-semibold">✏️ 규칙 편집</h2>
              <button
                onClick={() => setEditingRule(null)}
                className="text-gray-400 hover:text-gray-600 text-xl font-bold"
              >
                ✕
              </button>
            </div>
            
            <div className="p-6">
              <form onSubmit={(e) => {
                e.preventDefault();
                saveEditedRule();
              }} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">규칙 이름</label>
                    <input
                      type="text"
                      value={editingRule.name}
                      onChange={(e) => setEditingRule({ ...editingRule, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="규칙 이름을 입력하세요"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">규칙 유형</label>
                    <select
                      value={editingRule.type}
                      onChange={(e) => setEditingRule({ ...editingRule, type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="toxicity">독성 콘텐츠</option>
                      <option value="pii">개인정보</option>
                      <option value="bias">편향성</option>
                      <option value="content">콘텐츠 필터</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      임계값 ({editingRule.threshold})
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={editingRule.threshold}
                      onChange={(e) => setEditingRule({ ...editingRule, threshold: parseFloat(e.target.value) })}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>0.0 (관대함)</span>
                      <span>1.0 (엄격함)</span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">액션</label>
                    <select
                      value={editingRule.action || 'block'}
                      onChange={(e) => setEditingRule({ ...editingRule, action: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="block">차단</option>
                      <option value="flag">플래그</option>
                      <option value="modify">수정</option>
                    </select>
                  </div>
                </div>
                
                {/* 감지 패턴 섹션 */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">🔍 감지 패턴</label>
                    <div className="space-y-2">
                      {(editingRule.patterns || getRuleDetails(editingRule.name)?.patterns || []).map((pattern, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <input
                            type="text"
                            value={pattern}
                            onChange={(e) => {
                              const newPatterns = [...(editingRule.patterns || getRuleDetails(editingRule.name)?.patterns || [])];
                              newPatterns[index] = e.target.value;
                              setEditingRule({ ...editingRule, patterns: newPatterns });
                            }}
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                            placeholder="감지 패턴을 입력하세요 (예: regex: (욕설|비속어))"
                          />
                          <button
                            type="button"
                            onClick={() => {
                              const newPatterns = [...(editingRule.patterns || getRuleDetails(editingRule.name)?.patterns || [])];
                              newPatterns.splice(index, 1);
                              setEditingRule({ ...editingRule, patterns: newPatterns });
                            }}
                            className="px-2 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                          >
                            삭제
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={() => {
                          const newPatterns = [...(editingRule.patterns || getRuleDetails(editingRule.name)?.patterns || []), ''];
                          setEditingRule({ ...editingRule, patterns: newPatterns });
                        }}
                        className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                      >
                        + 패턴 추가
                      </button>
                    </div>
                  </div>

                  {/* 차단 예시 섹션 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">⚠️ 차단 예시</label>
                    <div className="space-y-2">
                      {(editingRule.examples || getRuleDetails(editingRule.name)?.examples || []).map((example, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <textarea
                            value={example}
                            onChange={(e) => {
                              const newExamples = [...(editingRule.examples || getRuleDetails(editingRule.name)?.examples || [])];
                              newExamples[index] = e.target.value;
                              setEditingRule({ ...editingRule, examples: newExamples });
                            }}
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                            placeholder="차단될 예시 텍스트를 입력하세요"
                            rows={2}
                          />
                          <button
                            type="button"
                            onClick={() => {
                              const newExamples = [...(editingRule.examples || getRuleDetails(editingRule.name)?.examples || [])];
                              newExamples.splice(index, 1);
                              setEditingRule({ ...editingRule, examples: newExamples });
                            }}
                            className="px-2 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                          >
                            삭제
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={() => {
                          const newExamples = [...(editingRule.examples || getRuleDetails(editingRule.name)?.examples || []), ''];
                          setEditingRule({ ...editingRule, examples: newExamples });
                        }}
                        className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                      >
                        + 예시 추가
                      </button>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input 
                    type="checkbox" 
                    checked={editingRule.enabled}
                    onChange={(e) => setEditingRule({ ...editingRule, enabled: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm font-medium">규칙 활성화</span>
                </div>
                
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setEditingRule(null)}
                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    저장
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}