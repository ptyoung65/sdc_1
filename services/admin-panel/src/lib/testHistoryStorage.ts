import { TestResult, TestHistoryFilters } from '../types/TestHistory';

// 인메모리 스토리지 (실제 구현에서는 데이터베이스 사용)
let testHistory: TestResult[] = [];

export class TestHistoryStorage {
  static saveTestResult(result: Omit<TestResult, 'id' | 'timestamp'>): TestResult {
    const testResult: TestResult = {
      ...result,
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
    };
    
    testHistory.unshift(testResult); // 최신순으로 추가
    
    // 최대 1000개까지만 저장 (메모리 관리)
    if (testHistory.length > 1000) {
      testHistory = testHistory.slice(0, 1000);
    }
    
    return testResult;
  }

  static getTestHistory(filters?: TestHistoryFilters): TestResult[] {
    let filteredHistory = [...testHistory];

    if (filters) {
      // 날짜 필터링
      if (filters.dateFrom) {
        const fromDate = new Date(filters.dateFrom);
        filteredHistory = filteredHistory.filter(
          test => new Date(test.timestamp) >= fromDate
        );
      }

      if (filters.dateTo) {
        const toDate = new Date(filters.dateTo);
        toDate.setHours(23, 59, 59, 999); // 해당 날짜 끝까지
        filteredHistory = filteredHistory.filter(
          test => new Date(test.timestamp) <= toDate
        );
      }

      // 쿼리 필터링
      if (filters.query) {
        const searchQuery = filters.query.toLowerCase();
        filteredHistory = filteredHistory.filter(
          test => test.query.toLowerCase().includes(searchQuery)
        );
      }

      // 상태 필터링
      if (filters.status && filters.status !== 'all') {
        filteredHistory = filteredHistory.filter(
          test => test.status === filters.status
        );
      }
    }

    return filteredHistory;
  }

  static getTestById(id: string): TestResult | undefined {
    return testHistory.find(test => test.id === id);
  }

  static clearHistory(): void {
    testHistory = [];
  }

  static getStatistics() {
    const total = testHistory.length;
    const successful = testHistory.filter(test => test.status === 'success').length;
    const failed = testHistory.filter(test => test.status === 'error').length;
    
    const avgProcessingTime = total > 0 
      ? testHistory.reduce((sum, test) => sum + test.processing_time, 0) / total 
      : 0;

    return {
      total,
      successful,
      failed,
      successRate: total > 0 ? (successful / total) * 100 : 0,
      avgProcessingTime,
    };
  }
}