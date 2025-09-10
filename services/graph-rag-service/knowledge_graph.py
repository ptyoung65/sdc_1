"""
Knowledge Graph Builder for Korean RAG System
한국어 문서로부터 지식 그래프를 구축하는 시스템 - MSA 버전
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
import networkx as nx
import json
import uuid
from datetime import datetime
import re
import os
import pickle
from pathlib import Path
from kiwipiepy import Kiwi
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:
    """한국어 문서로부터 지식 그래프를 구축하는 MSA용 클래스"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 3):
        """지식 그래프 빌더 초기화"""
        self.kiwi = Kiwi()
        self.graph = nx.MultiDiGraph()
        self.entity_types = {
            'PERSON': '인물',
            'ORGANIZATION': '조직',
            'LOCATION': '장소',
            'DATE': '날짜',
            'CONCEPT': '개념',
            'PRODUCT': '제품',
            'EVENT': '사건'
        }
        
        # Redis 연결 설정 (그래프 캐싱용)
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=redis_db, 
                decode_responses=False,  # Binary 데이터 저장을 위해
                health_check_interval=30
            )
            self.redis_client.ping()  # 연결 테스트
            logger.info("Redis 연결 성공")
        except RedisError as e:
            logger.warning(f"Redis 연결 실패: {e}, 메모리 모드로 동작")
            self.redis_client = None
        
        # 관계 패턴 정의 (한국어 특화)
        self.relation_patterns = [
            (r'(.+)는 (.+)이다', 'IS_A'),
            (r'(.+)가 (.+)이다', 'IS_A'),
            (r'(.+)의 (.+)', 'HAS_ATTRIBUTE'),
            (r'(.+)에서 (.+)', 'LOCATED_IN'),
            (r'(.+)와 (.+)', 'RELATED_TO'),
            (r'(.+)과 (.+)', 'RELATED_TO'),
            (r'(.+)를 (.+)', 'ACTS_ON'),
            (r'(.+)을 (.+)', 'ACTS_ON'),
            (r'(.+)에 의해 (.+)', 'CAUSED_BY'),
            (r'(.+)로 인해 (.+)', 'CAUSED_BY'),
            (r'(.+)보다 (.+)', 'COMPARED_TO')
        ]
        
        # 로컬 저장소 설정
        self.storage_dir = Path("/tmp/graph_rag_storage")
        self.storage_dir.mkdir(exist_ok=True)
        
        self._load_graph_from_storage()
        logger.info("Knowledge Graph Builder 초기화 완료")
    
    def _save_graph_to_storage(self):
        """그래프를 로컬 저장소에 저장"""
        try:
            graph_file = self.storage_dir / "knowledge_graph.pkl"
            with open(graph_file, 'wb') as f:
                pickle.dump(self.graph, f)
            
            # Redis에도 백업 (가능한 경우)
            if self.redis_client:
                try:
                    graph_data = pickle.dumps(self.graph)
                    self.redis_client.set("knowledge_graph", graph_data, ex=3600*24)  # 24시간 캐시
                except RedisError as e:
                    logger.warning(f"Redis 저장 실패: {e}")
            
            logger.debug("그래프를 저장소에 저장 완료")
            
        except Exception as e:
            logger.error(f"그래프 저장 중 오류: {e}")
    
    def _load_graph_from_storage(self):
        """저장소에서 그래프 로드"""
        try:
            # Redis에서 먼저 시도
            if self.redis_client:
                try:
                    graph_data = self.redis_client.get("knowledge_graph")
                    if graph_data:
                        self.graph = pickle.loads(graph_data)
                        logger.info("Redis에서 그래프 로드 완료")
                        return
                except RedisError as e:
                    logger.warning(f"Redis 로드 실패: {e}")
            
            # 로컬 파일에서 로드
            graph_file = self.storage_dir / "knowledge_graph.pkl"
            if graph_file.exists():
                with open(graph_file, 'rb') as f:
                    self.graph = pickle.load(f)
                logger.info("로컬 파일에서 그래프 로드 완료")
            else:
                logger.info("저장된 그래프가 없어 새로 시작")
                
        except Exception as e:
            logger.error(f"그래프 로드 중 오류: {e}, 새로운 그래프로 시작")
            self.graph = nx.MultiDiGraph()
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """텍스트에서 개체 추출"""
        try:
            # Kiwi를 사용한 형태소 분석
            result = self.kiwi.analyze(text)
            entities = []
            
            # Kiwi 결과 처리 (tuple 형태: (tokens, score))
            for item in result:
                tokens = item[0] if isinstance(item, tuple) else item
                
                for morph in tokens:
                    word = morph.form
                    pos = morph.tag
                    
                    # 명사류 추출 (고유명사, 일반명사, 복합명사)
                    if pos in ['NNP', 'NNG', 'NNB']:
                        if len(word) > 1:  # 단일 문자 제외
                            entity_type = self._classify_entity(word, pos)
                            entities.append({
                                'text': word,
                                'type': entity_type,
                                'pos': pos,
                                'confidence': 0.8
                            })
            
            # 중복 제거 및 정규화
            unique_entities = []
            seen = set()
            for entity in entities:
                key = (entity['text'].lower(), entity['type'])
                if key not in seen:
                    seen.add(key)
                    unique_entities.append(entity)
            
            logger.debug(f"추출된 개체 수: {len(unique_entities)}")
            return unique_entities
            
        except Exception as e:
            logger.error(f"개체 추출 중 오류: {e}")
            return []
    
    def _classify_entity(self, word: str, pos: str) -> str:
        """개체 유형 분류"""
        # 간단한 규칙 기반 분류
        if pos == 'NNP':  # 고유명사
            if any(char in word for char in '회사|기업|그룹|㈜|주식회사'):
                return 'ORGANIZATION'
            elif any(char in word for char in '시|도|구|군|동|로|길'):
                return 'LOCATION'
            elif len(word) <= 3 and any(char in '김이박최정'):
                return 'PERSON'
            else:
                return 'CONCEPT'
        else:  # 일반명사
            if any(char in word for char in '기술|방법|시스템|알고리즘|모델'):
                return 'CONCEPT'
            elif any(char in word for char in '제품|서비스|프로그램|앱|소프트웨어'):
                return 'PRODUCT'
            else:
                return 'CONCEPT'
    
    def extract_relations(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """텍스트에서 관계 추출"""
        try:
            relations = []
            sentences = self._split_sentences(text)
            
            for sentence in sentences:
                # 패턴 기반 관계 추출
                for pattern, relation_type in self.relation_patterns:
                    matches = re.finditer(pattern, sentence)
                    for match in matches:
                        subject = match.group(1).strip()
                        object_text = match.group(2).strip()
                        
                        # 개체가 실제로 추출된 개체 목록에 있는지 확인
                        if self._is_valid_entity(subject, entities) and self._is_valid_entity(object_text, entities):
                            relations.append({
                                'subject': subject,
                                'predicate': relation_type,
                                'object': object_text,
                                'sentence': sentence,
                                'confidence': 0.7
                            })
                
                # 동시 출현 기반 관계 추출
                sentence_entities = [e['text'] for e in entities if e['text'] in sentence]
                if len(sentence_entities) >= 2:
                    for i, entity1 in enumerate(sentence_entities):
                        for entity2 in sentence_entities[i+1:]:
                            relations.append({
                                'subject': entity1,
                                'predicate': 'CO_OCCURS',
                                'object': entity2,
                                'sentence': sentence,
                                'confidence': 0.5
                            })
            
            logger.debug(f"추출된 관계 수: {len(relations)}")
            return relations
            
        except Exception as e:
            logger.error(f"관계 추출 중 오류: {e}")
            return []
    
    def _split_sentences(self, text: str) -> List[str]:
        """텍스트를 문장으로 분할"""
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _is_valid_entity(self, text: str, entities: List[Dict[str, Any]]) -> bool:
        """개체가 유효한지 확인"""
        return any(entity['text'] == text for entity in entities)
    
    def build_graph_from_document(self, document_id: str, title: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """문서로부터 지식 그래프 구축"""
        try:
            # 개체 추출
            entities = self.extract_entities(content)
            
            # 관계 추출
            relations = self.extract_relations(content, entities)
            
            # 그래프에 노드 추가
            nodes_added = 0
            for entity in entities:
                node_id = f"{document_id}_{entity['text']}"
                if not self.graph.has_node(node_id):
                    self.graph.add_node(
                        node_id,
                        text=entity['text'],
                        type=entity['type'],
                        document_id=document_id,
                        document_title=title,
                        created_at=datetime.now().isoformat(),
                        confidence=entity['confidence'],
                        metadata=metadata or {}
                    )
                    nodes_added += 1
                else:
                    # 기존 노드 업데이트
                    existing_data = self.graph.nodes[node_id]
                    existing_data['last_updated'] = datetime.now().isoformat()
            
            # 그래프에 엣지 추가
            edges_added = 0
            for relation in relations:
                subject_id = f"{document_id}_{relation['subject']}"
                object_id = f"{document_id}_{relation['object']}"
                
                if self.graph.has_node(subject_id) and self.graph.has_node(object_id):
                    edge_id = f"{subject_id}_{relation['predicate']}_{object_id}_{uuid.uuid4().hex[:8]}"
                    self.graph.add_edge(
                        subject_id,
                        object_id,
                        key=edge_id,
                        predicate=relation['predicate'],
                        sentence=relation['sentence'],
                        document_id=document_id,
                        confidence=relation['confidence'],
                        created_at=datetime.now().isoformat()
                    )
                    edges_added += 1
            
            # 저장
            self._save_graph_to_storage()
            
            result = {
                'status': 'success',
                'document_id': document_id,
                'entities_extracted': len(entities),
                'relations_extracted': len(relations),
                'nodes_added': nodes_added,
                'edges_added': edges_added,
                'graph_stats': {
                    'total_nodes': self.graph.number_of_nodes(),
                    'total_edges': self.graph.number_of_edges()
                }
            }
            
            logger.info(f"문서 {document_id}의 지식 그래프 구축 완료: {nodes_added}개 노드, {edges_added}개 엣지 추가")
            return result
            
        except Exception as e:
            logger.error(f"지식 그래프 구축 중 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def query_graph(self, query: str, max_hops: int = 2, max_results: int = 10) -> List[Dict[str, Any]]:
        """지식 그래프에서 쿼리 수행"""
        try:
            # 쿼리에서 개체 추출
            query_entities = self.extract_entities(query)
            query_terms = [e['text'] for e in query_entities]
            
            if not query_terms:
                return []
            
            relevant_subgraphs = []
            
            # 각 쿼리 개체에 대해 서브그래프 탐색
            for term in query_terms:
                matching_nodes = []
                
                # 정확 매칭 노드 찾기
                for node_id, node_data in self.graph.nodes(data=True):
                    if node_data['text'] == term:
                        matching_nodes.append(node_id)
                
                # 부분 매칭 노드 찾기
                if not matching_nodes:
                    for node_id, node_data in self.graph.nodes(data=True):
                        if term in node_data['text'] or node_data['text'] in term:
                            matching_nodes.append(node_id)
                
                # 각 매칭 노드에서 서브그래프 추출
                for node_id in matching_nodes[:max_results]:
                    subgraph = self._extract_subgraph(node_id, max_hops)
                    if subgraph:
                        relevant_subgraphs.append({
                            'central_node': node_id,
                            'central_entity': self.graph.nodes[node_id]['text'],
                            'subgraph': subgraph,
                            'relevance_score': self._calculate_relevance(subgraph, query_terms)
                        })
            
            # 관련성 점수로 정렬
            relevant_subgraphs.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return relevant_subgraphs[:max_results]
            
        except Exception as e:
            logger.error(f"그래프 쿼리 중 오류: {e}")
            return []
    
    def _extract_subgraph(self, central_node: str, max_hops: int) -> Dict[str, Any]:
        """중심 노드를 기준으로 서브그래프 추출"""
        try:
            if not self.graph.has_node(central_node):
                return {}
            
            # BFS로 최대 홉 수만큼 탐색
            visited = set()
            queue = [(central_node, 0)]
            subgraph_nodes = set()
            subgraph_edges = []
            
            while queue:
                current_node, hop = queue.pop(0)
                
                if hop > max_hops or current_node in visited:
                    continue
                
                visited.add(current_node)
                subgraph_nodes.add(current_node)
                
                # 이웃 노드들 탐색
                for neighbor in self.graph.neighbors(current_node):
                    if hop < max_hops:
                        queue.append((neighbor, hop + 1))
                    
                    # 엣지 정보 수집
                    for key, edge_data in self.graph[current_node][neighbor].items():
                        subgraph_edges.append({
                            'source': current_node,
                            'target': neighbor,
                            'relation': edge_data['predicate'],
                            'sentence': edge_data.get('sentence', ''),
                            'confidence': edge_data.get('confidence', 0.5)
                        })
            
            # 노드 정보 수집
            nodes_info = []
            for node_id in subgraph_nodes:
                node_data = self.graph.nodes[node_id]
                nodes_info.append({
                    'id': node_id,
                    'text': node_data['text'],
                    'type': node_data['type'],
                    'document_id': node_data['document_id'],
                    'document_title': node_data.get('document_title', ''),
                    'confidence': node_data.get('confidence', 0.5)
                })
            
            return {
                'nodes': nodes_info,
                'edges': subgraph_edges,
                'central_node': central_node
            }
            
        except Exception as e:
            logger.error(f"서브그래프 추출 중 오류: {e}")
            return {}
    
    def _calculate_relevance(self, subgraph: Dict[str, Any], query_terms: List[str]) -> float:
        """서브그래프의 쿼리 관련성 점수 계산"""
        try:
            if not subgraph.get('nodes'):
                return 0.0
            
            relevance = 0.0
            total_nodes = len(subgraph['nodes'])
            
            # 노드 매칭 점수
            for node in subgraph['nodes']:
                for term in query_terms:
                    if term in node['text'] or node['text'] in term:
                        relevance += node['confidence']
            
            # 엣지 밀도 보너스
            total_edges = len(subgraph['edges'])
            if total_nodes > 1:
                edge_density = total_edges / (total_nodes * (total_nodes - 1))
                relevance += edge_density * 0.5
            
            # 정규화
            return relevance / max(total_nodes, 1)
            
        except Exception as e:
            logger.error(f"관련성 점수 계산 중 오류: {e}")
            return 0.0
    
    def generate_graph_context(self, subgraphs: List[Dict[str, Any]], max_length: int = 1000) -> str:
        """서브그래프들로부터 컨텍스트 문자열 생성"""
        try:
            context_parts = []
            current_length = 0
            
            for i, subgraph_info in enumerate(subgraphs):
                subgraph = subgraph_info['subgraph']
                
                if not subgraph.get('nodes'):
                    continue
                
                # 서브그래프 요약 생성
                central_entity = subgraph_info['central_entity']
                context_part = f"[지식 그래프 {i+1}] {central_entity}와 관련된 정보:\n"
                
                # 관련 개체들 나열
                related_entities = []
                for node in subgraph['nodes']:
                    if node['text'] != central_entity:
                        related_entities.append(f"{node['text']}({node['type']})")
                
                if related_entities:
                    context_part += f"- 관련 개체: {', '.join(related_entities[:5])}\n"
                
                # 주요 관계들 나열
                relations = []
                for edge in subgraph['edges'][:3]:  # 상위 3개 관계만
                    source_text = next(n['text'] for n in subgraph['nodes'] if n['id'] == edge['source'])
                    target_text = next(n['text'] for n in subgraph['nodes'] if n['id'] == edge['target'])
                    relations.append(f"{source_text} → {edge['relation']} → {target_text}")
                
                if relations:
                    context_part += f"- 주요 관계: {' | '.join(relations)}\n"
                
                context_part += "\n"
                
                # 길이 제한 확인
                if current_length + len(context_part) <= max_length:
                    context_parts.append(context_part)
                    current_length += len(context_part)
                else:
                    break
            
            return "".join(context_parts)
            
        except Exception as e:
            logger.error(f"그래프 컨텍스트 생성 중 오류: {e}")
            return ""
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """지식 그래프 통계 반환"""
        try:
            stats = {
                'total_nodes': self.graph.number_of_nodes(),
                'total_edges': self.graph.number_of_edges(),
                'entity_types': {},
                'relation_types': {},
                'documents_processed': len(set(data.get('document_id', '') for _, data in self.graph.nodes(data=True)))
            }
            
            # 개체 유형별 통계
            for _, data in self.graph.nodes(data=True):
                entity_type = data.get('type', 'UNKNOWN')
                stats['entity_types'][entity_type] = stats['entity_types'].get(entity_type, 0) + 1
            
            # 관계 유형별 통계
            for _, _, data in self.graph.edges(data=True):
                relation_type = data.get('predicate', 'UNKNOWN')
                stats['relation_types'][relation_type] = stats['relation_types'].get(relation_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"그래프 통계 계산 중 오류: {e}")
            return {}
    
    def delete_document_from_graph(self, document_id: str) -> bool:
        """특정 문서의 그래프 데이터 삭제"""
        try:
            # 해당 문서의 노드들 찾기
            nodes_to_remove = []
            for node_id, data in self.graph.nodes(data=True):
                if data.get('document_id') == document_id:
                    nodes_to_remove.append(node_id)
            
            # 노드들 삭제 (연결된 엣지도 자동 삭제됨)
            for node_id in nodes_to_remove:
                self.graph.remove_node(node_id)
            
            # 저장
            self._save_graph_to_storage()
            
            logger.info(f"문서 {document_id}의 그래프 데이터 삭제 완료: {len(nodes_to_remove)}개 노드 삭제")
            return True
            
        except Exception as e:
            logger.error(f"문서 그래프 삭제 중 오류: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        try:
            redis_status = "connected" if (self.redis_client and self.redis_client.ping()) else "disconnected"
            
            return {
                "status": "healthy",
                "graph_nodes": self.graph.number_of_nodes(),
                "graph_edges": self.graph.number_of_edges(),
                "redis_status": redis_status,
                "storage_available": self.storage_dir.exists()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 전역 지식 그래프 빌더 인스턴스
_graph_builder = None

def get_knowledge_graph_builder() -> KnowledgeGraphBuilder:
    """지식 그래프 빌더 인스턴스 반환"""
    global _graph_builder
    if _graph_builder is None:
        _graph_builder = KnowledgeGraphBuilder()
    return _graph_builder