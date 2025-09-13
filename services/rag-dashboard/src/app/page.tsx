"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Activity,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  BarChart3,
  PieChart,
  Target,
  Gauge,
  Brain,
  Search,
  MessageSquare,
  Shield
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, PieChart as RechartsPieChart, Cell } from 'recharts';
import axios from 'axios';

// Types for RAG metrics
interface RAGMetrics {
  context_relevance: number;
  context_sufficiency: number;
  answer_relevance: number;
  answer_correctness: number;
  hallucination_rate: number;
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  total_latency_ms: number;
  overall_quality_score: number;
}

interface MetricsAggregation {
  period: string;
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
  quality_distribution: Record<string, number>;
}

interface RealtimeMetrics {
  timestamp: string;
  current_throughput: number;
  avg_latency_1min: number;
  active_sessions: number;
  success_rate: number;
  recent_quality_scores: number[];
  status: string;
}

export default function RAGDashboard() {
  const [aggregatedMetrics, setAggregatedMetrics] = useState<MetricsAggregation | null>(null);
  const [realtimeMetrics, setRealtimeMetrics] = useState<RealtimeMetrics | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<string>("1h");
  const [loading, setLoading] = useState(true);
  
  const RAG_EVALUATOR_API = process.env.NEXT_PUBLIC_RAG_EVALUATOR_API || 'http://localhost:8002';

  // Fetch data
  useEffect(() => {
    fetchAggregatedMetrics();
    fetchRealtimeMetrics();
    
    // Set up real-time updates
    const interval = setInterval(fetchRealtimeMetrics, 10000); // Update every 10s
    return () => clearInterval(interval);
  }, [selectedPeriod]);

  const fetchAggregatedMetrics = async () => {
    try {
      const response = await axios.get(`${RAG_EVALUATOR_API}/api/v1/rag/metrics/aggregated`, {
        params: { period: selectedPeriod }
      });
      setAggregatedMetrics(response.data);
    } catch (error) {
      console.error('Failed to fetch aggregated metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRealtimeMetrics = async () => {
    try {
      const response = await axios.get(`${RAG_EVALUATOR_API}/api/v1/rag/metrics/realtime`);
      setRealtimeMetrics(response.data);
    } catch (error) {
      console.error('Failed to fetch realtime metrics:', error);
    }
  };

  // Chart data preparation
  const qualityRadarData = aggregatedMetrics ? [
    {
      metric: 'Context Relevance',
      value: aggregatedMetrics.avg_context_relevance * 100,
      fullMark: 100
    },
    {
      metric: 'Context Sufficiency',
      value: aggregatedMetrics.avg_context_sufficiency * 100,
      fullMark: 100
    },
    {
      metric: 'Answer Relevance',
      value: aggregatedMetrics.avg_answer_relevance * 100,
      fullMark: 100
    },
    {
      metric: 'Answer Correctness',
      value: aggregatedMetrics.avg_answer_correctness * 100,
      fullMark: 100
    },
    {
      metric: 'No Hallucination',
      value: (1 - aggregatedMetrics.avg_hallucination_rate) * 100,
      fullMark: 100
    }
  ] : [];

  const latencyData = aggregatedMetrics ? [
    {
      stage: 'Retrieval',
      latency: aggregatedMetrics.avg_retrieval_latency_ms,
      color: '#3b82f6'
    },
    {
      stage: 'Generation',
      latency: aggregatedMetrics.avg_generation_latency_ms,
      color: '#ef4444'
    }
  ] : [];

  const qualityDistributionData = aggregatedMetrics ? 
    Object.entries(aggregatedMetrics.quality_distribution).map(([key, value], index) => ({
      name: key.charAt(0).toUpperCase() + key.slice(1),
      value: value,
      color: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'][index]
    })) : [];

  const performanceTimelineData = [
    { time: '00:00', quality: 0.82, latency: 2100 },
    { time: '04:00', quality: 0.85, latency: 1950 },
    { time: '08:00', quality: 0.79, latency: 2300 },
    { time: '12:00', quality: 0.88, latency: 1800 },
    { time: '16:00', quality: 0.76, latency: 2500 },
    { time: '20:00', quality: 0.83, latency: 2000 }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-3">
              <Brain className="h-8 w-8 text-purple-600" />
              <h1 className="text-3xl font-bold text-gray-900">RAG Performance Dashboard</h1>
            </div>
            <div className="flex items-center gap-4">
              <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">Last 1h</SelectItem>
                  <SelectItem value="24h">Last 24h</SelectItem>
                  <SelectItem value="7d">Last 7d</SelectItem>
                  <SelectItem value="30d">Last 30d</SelectItem>
                </SelectContent>
              </Select>
              <Badge 
                variant={realtimeMetrics?.status === 'healthy' ? 'default' : 'destructive'}
                className="flex items-center gap-2"
              >
                <div className={`w-2 h-2 rounded-full ${realtimeMetrics?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
                {realtimeMetrics?.status || 'Unknown'}
              </Badge>
            </div>
          </div>
          <p className="text-gray-600">RAG 시스템의 성능, 품질 및 효율성을 종합적으로 모니터링합니다</p>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="quality" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              Quality Metrics
            </TabsTrigger>
            <TabsTrigger value="performance" className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Performance
            </TabsTrigger>
            <TabsTrigger value="realtime" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Real-time
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Key Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
                  <MessageSquare className="h-4 w-4 text-blue-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{aggregatedMetrics?.total_queries.toLocaleString()}</div>
                  <p className="text-xs text-gray-600">in selected period</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Average Quality Score</CardTitle>
                  <Target className="h-4 w-4 text-green-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {((aggregatedMetrics?.avg_quality_score || 0) * 100).toFixed(1)}%
                  </div>
                  <Progress value={(aggregatedMetrics?.avg_quality_score || 0) * 100} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
                  <Clock className="h-4 w-4 text-orange-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{aggregatedMetrics?.avg_total_latency_ms}ms</div>
                  <p className="text-xs text-gray-600">P95: {aggregatedMetrics?.p95_latency_ms}ms</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Throughput</CardTitle>
                  <TrendingUp className="h-4 w-4 text-purple-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {aggregatedMetrics?.throughput_per_second.toFixed(1)} QPS
                  </div>
                  <p className="text-xs text-gray-600">queries per second</p>
                </CardContent>
              </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Quality Radar Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Quality Metrics Overview</CardTitle>
                  <CardDescription>Comprehensive quality assessment across all dimensions</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={qualityRadarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="metric" />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} />
                      <Radar
                        name="Quality"
                        dataKey="value"
                        stroke="#8b5cf6"
                        fill="#8b5cf6"
                        fillOpacity={0.3}
                        strokeWidth={2}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Quality Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Quality Distribution</CardTitle>
                  <CardDescription>Distribution of response quality ratings</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <RechartsPieChart>
                      <Pie
                        data={qualityDistributionData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {qualityDistributionData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center space-x-4 mt-4">
                    {qualityDistributionData.map((entry, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-sm">{entry.name}: {entry.value}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Quality Metrics Tab */}
          <TabsContent value="quality" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Context Relevance */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="h-5 w-5" />
                    Context Relevance
                  </CardTitle>
                  <CardDescription>검색된 문서가 질의에 얼마나 관련성 있는지</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold mb-2">
                    {((aggregatedMetrics?.avg_context_relevance || 0) * 100).toFixed(1)}%
                  </div>
                  <Progress value={(aggregatedMetrics?.avg_context_relevance || 0) * 100} />
                  <p className="text-sm text-gray-600 mt-2">
                    Higher relevance leads to better answer quality
                  </p>
                </CardContent>
              </Card>

              {/* Answer Correctness */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5" />
                    Answer Correctness
                  </CardTitle>
                  <CardDescription>답변이 정답과 얼마나 일치하는지</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold mb-2">
                    {((aggregatedMetrics?.avg_answer_correctness || 0) * 100).toFixed(1)}%
                  </div>
                  <Progress value={(aggregatedMetrics?.avg_answer_correctness || 0) * 100} />
                  <p className="text-sm text-gray-600 mt-2">
                    Measured against ground truth when available
                  </p>
                </CardContent>
              </Card>

              {/* Hallucination Rate */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    Hallucination Rate
                  </CardTitle>
                  <CardDescription>허위 정보를 생성하는 비율</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold mb-2 text-red-600">
                    {((aggregatedMetrics?.avg_hallucination_rate || 0) * 100).toFixed(1)}%
                  </div>
                  <Progress 
                    value={(aggregatedMetrics?.avg_hallucination_rate || 0) * 100} 
                    className="[&>div]:bg-red-500"
                  />
                  <p className="text-sm text-gray-600 mt-2">
                    Lower is better - indicates factual accuracy
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Detailed Quality Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Quality Metrics Breakdown</CardTitle>
                <CardDescription>Detailed analysis of all quality dimensions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {aggregatedMetrics && [
                    { name: 'Context Relevance', value: aggregatedMetrics.avg_context_relevance, description: 'How relevant are retrieved documents to the query' },
                    { name: 'Context Sufficiency', value: aggregatedMetrics.avg_context_sufficiency, description: 'Whether retrieved context is sufficient for answering' },
                    { name: 'Answer Relevance', value: aggregatedMetrics.avg_answer_relevance, description: 'How well the answer addresses the query' },
                    { name: 'Answer Correctness', value: aggregatedMetrics.avg_answer_correctness, description: 'Factual accuracy compared to ground truth' },
                    { name: 'Hallucination Prevention', value: 1 - aggregatedMetrics.avg_hallucination_rate, description: 'Ability to avoid generating false information' }
                  ].map((metric, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-medium">{metric.name}</p>
                          <p className="text-sm text-gray-600">{metric.description}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold">{(metric.value * 100).toFixed(1)}%</div>
                          <Badge variant={metric.value >= 0.8 ? 'default' : metric.value >= 0.6 ? 'secondary' : 'destructive'}>
                            {metric.value >= 0.8 ? 'Excellent' : metric.value >= 0.6 ? 'Good' : 'Needs Improvement'}
                          </Badge>
                        </div>
                      </div>
                      <Progress value={metric.value * 100} />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Latency Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>Latency Breakdown</CardTitle>
                  <CardDescription>Response time by processing stage</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={latencyData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="stage" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="latency" fill={(entry) => entry.color} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Performance Timeline */}
              <Card>
                <CardHeader>
                  <CardTitle>Performance Over Time</CardTitle>
                  <CardDescription>Quality and latency trends</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={performanceTimelineData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis yAxisId="left" domain={[0, 1]} />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Line 
                        yAxisId="left" 
                        type="monotone" 
                        dataKey="quality" 
                        stroke="#10b981" 
                        strokeWidth={2}
                        name="Quality Score"
                      />
                      <Line 
                        yAxisId="right" 
                        type="monotone" 
                        dataKey="latency" 
                        stroke="#f59e0b" 
                        strokeWidth={2}
                        name="Latency (ms)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Performance Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Latency Statistics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span>Average:</span>
                    <span className="font-bold">{aggregatedMetrics?.avg_total_latency_ms}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>95th Percentile:</span>
                    <span className="font-bold">{aggregatedMetrics?.p95_latency_ms}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>99th Percentile:</span>
                    <span className="font-bold">{aggregatedMetrics?.p99_latency_ms}ms</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Stage Breakdown</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span>Retrieval:</span>
                    <span className="font-bold">{aggregatedMetrics?.avg_retrieval_latency_ms}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Generation:</span>
                    <span className="font-bold">{aggregatedMetrics?.avg_generation_latency_ms}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total:</span>
                    <span className="font-bold">{aggregatedMetrics?.avg_total_latency_ms}ms</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Throughput</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold">{aggregatedMetrics?.throughput_per_second.toFixed(2)}</div>
                    <p className="text-sm text-gray-600">Queries Per Second</p>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Queries:</span>
                    <span className="font-bold">{aggregatedMetrics?.total_queries}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Real-time Tab */}
          <TabsContent value="realtime" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Current Throughput</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{realtimeMetrics?.current_throughput} QPS</div>
                  <div className="flex items-center mt-2">
                    <TrendingUp className="h-4 w-4 text-green-500 mr-2" />
                    <span className="text-sm text-green-600">Live</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Active Sessions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{realtimeMetrics?.active_sessions}</div>
                  <div className="text-sm text-gray-600">concurrent users</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Success Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{((realtimeMetrics?.success_rate || 0) * 100).toFixed(1)}%</div>
                  <Progress value={(realtimeMetrics?.success_rate || 0) * 100} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Avg Latency (1min)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{realtimeMetrics?.avg_latency_1min}ms</div>
                  <div className="text-sm text-gray-600">rolling average</div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Quality Scores */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Quality Scores</CardTitle>
                <CardDescription>Quality scores from the last few queries</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {realtimeMetrics?.recent_quality_scores.map((score, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm">Query #{realtimeMetrics.recent_quality_scores.length - index}</span>
                      <div className="flex items-center gap-3">
                        <Progress value={score * 100} className="w-32" />
                        <span className="font-mono text-sm w-12">{(score * 100).toFixed(0)}%</span>
                        <Badge variant={score >= 0.8 ? 'default' : score >= 0.6 ? 'secondary' : 'destructive'}>
                          {score >= 0.8 ? 'Great' : score >= 0.6 ? 'Good' : 'Poor'}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* System Status */}
            <Card>
              <CardHeader>
                <CardTitle>System Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-6 w-6 text-green-600" />
                      <span>RAG Evaluator Service</span>
                    </div>
                    <Badge className="bg-green-100 text-green-800">Healthy</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Activity className="h-6 w-6 text-blue-600" />
                      <span>Metrics Collection</span>
                    </div>
                    <Badge className="bg-blue-100 text-blue-800">Active</Badge>
                  </div>
                </div>
                
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">
                    Last Updated: {realtimeMetrics?.timestamp && new Date(realtimeMetrics.timestamp).toLocaleString()}
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}