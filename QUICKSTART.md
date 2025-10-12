# 🚀 AdaptiveGraphRAG - 5-Minute Quick Start

## TL;DR Setup (Copy-Paste Ready)

### 1. Prerequisites Check (30 seconds)

```bash
# Verify Python 3.10+
python --version

# Verify you have ~4GB free memory
free -h  # Linux/Mac
wmic OS get TotalVisibleMemorySize  # Windows
```

### 2. Clone and Environment (1 minute)

```bash
# Create project
mkdir adaptive-rag && cd adaptive-rag

# Create virtual environment
python -m venv venv

# Activate (choose your OS)
source venv/bin/activate           # Linux/Mac
venv\Scripts\activate              # Windows
```

### 3. Install Dependencies (2 minutes)

```bash
# Install all at once
pip install -r requirements.txt

# Verify critical packages
python -c "import langchain, neo4j, sentence_transformers; print('✓ Ready')"
```

### 4. Setup Neo4j (1 minute - Docker)

```bash
# Option A: Docker (Fastest)
docker run -d -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["graph-data-science"]' \
  neo4j:latest

# Option B: Without Docker
# Download from https://neo4j.com/download/
# Run: neo4j start
```

### 5. Quick Configuration (30 seconds)

```bash
# Create .env file (copy-paste this exactly)
cat > .env << 'EOF'
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
LOG_LEVEL=INFO
EOF
```

### 6. Run Demo (30 seconds)

```bash
# Create data directories
mkdir -p data logs

# Run the demo
python demo_script.py

# Expected output: "✓ Demo completed successfully"
```

### 7. Start API Server (continuous)

```bash
# In a new terminal (keep venv activated)
python api_server.py

# You should see: "Uvicorn running on http://0.0.0.0:8000"
```

## Verify Installation (Test Your Setup)

### Test 1: Health Check
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

### Test 2: Process a Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is artificial intelligence?"}'

# Should return JSON with answer and confidence
```

### Test 3: Check System Status
```bash
curl http://localhost:8000/status | python -m json.tool

# Should show all components initialized
```

## Minimal Python Integration (Copy-Paste)

```python
from adaptive_orchestrator import get_orchestrator

# Initialize
orchestrator = get_orchestrator()

# Process query
response = orchestrator.process_query("What is machine learning?")

# Print results
print(f"Answer: {response.answer}")
print(f"Confidence: {response.confidence_score:.1%}")
print(f"Method: {response.retrieval_method_used.value}")
print(f"Time: {response.execution_time_ms:.0f}ms")

# Cleanup
orchestrator.cleanup()
```

## Project Structure (Created Automatically)

```
adaptive-rag/
├── venv/                          # Virtual environment
├── data/
│   └── rot_storage/
├── logs/
├── .env                           # Your config
├── config.py                      # Core config
├── models.py                      # Data models
├── retrieval_outcome_tracker.py   # ROT
├── graph_edge_reweighting.py      # GERE
├── latent_relationship_discovery.py  # LRD
├── meta_query_router.py           # MQR
├── embeddings_manager.py          # Embeddings
├── neo4j_manager.py              # Database
├── adaptive_orchestrator.py       # Main
├── api_server.py                 # API
└── demo_script.py                # Demo
```

## Common Commands Reference

```bash
# Activate environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Run demo
python demo_script.py

# Start server
python api_server.py

# Run tests
python -m pytest tests/ -v

# Export data
curl http://localhost:8000/save-state/backup.json

# Check Neo4j
neo4j-admin dbms info  # or visit http://localhost:7474
```

## Troubleshooting (Copy-Paste Solutions)

### ❌ "ModuleNotFoundError: No module named 'langchain'"
```bash
# Solution: Activate venv and reinstall
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### ❌ "Connection refused: Neo4j on port 7687"
```bash
# Solution: Start Neo4j
docker ps  # Check if running
docker start <container_id>  # If stopped

# Or manually:
# Download from neo4j.com and run ./bin/neo4j start
```

### ❌ "Out of memory" error
```bash
# Solution: Use smaller embedding model
# In config.py, change:
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# to:
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L12-v1"
```

### ❌ "Port 8000 already in use"
```bash
# Solution: Kill process on that port
lsof -i :8000  # Find process
kill -9 <PID>  # Kill it

# Or use different port:
# Edit .env: API_PORT=8001
```

### ❌ "Neo4j authentication failed"
```bash
# Solution: Reset Neo4j password
docker exec <container_id> cypher-shell
# Then run: ALTER USER neo4j SET PASSWORD 'newpassword'
# Update .env with new password
```

## Next Steps

### 1. Try the API
```bash
# Create a test script
cat > test_queries.sh << 'EOF'
#!/bin/bash
QUERIES=("What is deep learning?" "Tell me about neural networks" "Explain transformers")
for q in "${QUERIES[@]}"; do
  curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$q\"}"
done
EOF

chmod +x test_queries.sh
./test_queries.sh
```

### 2. Monitor Performance
```bash
# Check routing recommendations
curl http://localhost:8000/routing/recommendations | python -m json.tool

# Check performance
curl http://localhost:8000/performance/summary?days=1 | python -m json.tool

# View discovered relationships
curl http://localhost:8000/relationships/high-confidence | python -m json.tool
```

### 3. Integrate with Your App
```python
# Add to your FastAPI/Flask app
from fastapi import FastAPI
from adaptive_orchestrator import get_orchestrator

app = FastAPI()
orchestrator = get_orchestrator()

@app.post("/my-rag-endpoint")
async def my_rag_query(query: str):
    response = orchestrator.process_query(query)
    return response.dict()
```

### 4. Advanced Configuration
```python
# config.py - Tune parameters
config.adaptive_meta.positive_weight_delta = 0.2    # Learn faster
config.adaptive_meta.min_historical_queries = 3     # Route sooner
config.embedding.cache_embeddings = True            # Faster
config.retriever.vector_search_top_k = 10           # More results
```

## Performance Expectations

- **First query**: 500-1000ms (model loading)
- **Subsequent queries**: 100-300ms
- **Embedding cache hit**: 20-50ms
- **API response**: <500ms average

## Cleanup

```bash
# Stop server (Ctrl+C in terminal)

# Deactivate venv
deactivate

# Clean up (optional)
rm -rf venv data logs
rm .env

# Stop Neo4j
docker stop <container_id>
docker rm <container_id>  # Remove container
```

## What's Happening Under the Hood?

1. **Query comes in** → Classified by type
2. **Routing decision** → Best method selected based on history
3. **Retrieval executed** → Vector search, graph traversal, or logical filtering
4. **Learning updates**:
   - Edge weights updated in graph
   - Method effectiveness tracked
   - Relationships discovered
   - Routing optimized for next time

## Key Metrics to Monitor

- **Success Rate**: Should improve over time
- **Average Latency**: Should stabilize
- **Confidence Scores**: Should increase
- **Edge Weights**: Should diverge (useful paths heavier)

## Get Help

```bash
# Check logs
tail -f logs/adaptive_rag.log

# Debug mode
DEBUG=True python api_server.py

# Run with verbose logging
python -c "import logging; logging.basicConfig(level=logging.DEBUG)" && python demo_script.py
```

---

**You're all set! Your AdaptiveGraphRAG system is now running.** 🎉