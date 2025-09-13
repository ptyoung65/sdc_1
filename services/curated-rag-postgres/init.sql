-- Initialize Curated RAG PostgreSQL Database
-- This script sets up the database schema for the AI-Curated RAG system

-- Create database if not exists
-- (This is handled by the POSTGRES_DB environment variable)

-- Create tables for analytics and metrics
CREATE TABLE IF NOT EXISTS rag_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(255) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    mode VARCHAR(50) NOT NULL,
    optimization VARCHAR(50) NOT NULL,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS curation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES rag_sessions(id),
    strategy VARCHAR(50) NOT NULL,
    avg_relevance FLOAT,
    avg_quality FLOAT,
    avg_diversity FLOAT,
    coverage FLOAT,
    items_curated INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    request_count INTEGER DEFAULT 1,
    avg_latency_ms FLOAT,
    avg_tokens INTEGER,
    avg_confidence FLOAT,
    cost_estimate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_mode VARCHAR(50) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    duration_ms INTEGER,
    error_message TEXT,
    session_id UUID REFERENCES rag_sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_rag_sessions_created_at ON rag_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_rag_sessions_user_id ON rag_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_curation_metrics_strategy ON curation_metrics(strategy);
CREATE INDEX IF NOT EXISTS idx_model_performance_model_name ON model_performance(model_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_analytics_mode ON pipeline_analytics(pipeline_mode);

-- Insert sample data for testing
INSERT INTO rag_sessions (request_id, query, mode, optimization, processing_time_ms, user_id) 
VALUES 
    ('sample-001', 'What is machine learning?', 'curated', 'balanced', 1250, 'user-001'),
    ('sample-002', 'Explain deep learning algorithms', 'hybrid', 'quality_optimized', 2100, 'user-002'),
    ('sample-003', 'Computer vision applications', 'standard', 'latency_optimized', 850, 'user-001')
ON CONFLICT (request_id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO curated_rag_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO curated_rag_user;