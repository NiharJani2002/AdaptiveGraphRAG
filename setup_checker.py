"""
Setup Checker and Environment Verifier for AdaptiveGraphRAG
Validates all dependencies and configurations
"""

import sys
import subprocess
import importlib
from typing import Tuple, List, Dict
from pathlib import Path
import os


class AdaptiveRAGSetupChecker:
    """Comprehensive setup verification"""
    
    def __init__(self):
        """Initialize checker"""
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
    
    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80)
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"✓ {text}")
        self.checks_passed.append(text)
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"✗ {text}")
        self.checks_failed.append(text)
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"⚠ {text}")
        self.warnings.append(text)
    
    def check_python_version(self) -> bool:
        """Check Python version"""
        self.print_header("PYTHON VERSION CHECK")
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        print(f"Python version: {version_str}")
        
        if version.major >= 3 and version.minor >= 10:
            self.print_success(f"Python {version_str} meets requirements (≥3.10)")
            return True
        else:
            self.print_error(
                f"Python {version_str} is too old. "
                f"Required: ≥3.10"
            )
            return False
    
    def check_dependencies(self) -> bool:
        """Check all required dependencies"""
        self.print_header("DEPENDENCY CHECK")
        
        # Required packages with version constraints
        dependencies = {
            "langchain": "0.3.0",
            "neo4j": "5.25.0",
            "sentence_transformers": "3.0.1",
            "torch": "2.2.0",
            "fastapi": "0.110.0",
            "pydantic": "2.6.0",
            "pandas": "2.2.0",
            "numpy": "1.24.3",
        }
        
        all_installed = True
        
        for package, required_version in dependencies.items():
            try:
                imported = importlib.import_module(package)
                
                # Try to get version
                try:
                    version = imported.__version__
                except AttributeError:
                    version = "unknown"
                
                self.print_success(
                    f"{package} {version} installed "
                    f"(required: ≥{required_version})"
                )
            except ImportError:
                self.print_error(
                    f"{package} NOT installed "
                    f"(required: ≥{required_version}). "
                    f"Run: pip install -r requirements.txt"
                )
                all_installed = False
        
        return all_installed
    
    def check_neo4j_connection(self) -> bool:
        """Check Neo4j connectivity"""
        self.print_header("NEO4J CONNECTION CHECK")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        
        print(f"Attempting connection to: {uri}")
        
        try:
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(
                uri,
                auth=(username, password),
                encrypted=False
            )
            
            with driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            
            driver.close()
            self.print_success("Neo4j connection successful")
            return True
        
        except Exception as e:
            self.print_error(f"Neo4j connection failed: {e}")
            self.print_warning(
                "Ensure Neo4j is running. "
                "Start with: docker run -d -p 7687:7687 neo4j:latest"
            )
            return False
    
    def check_directories(self) -> bool:
        """Check and create required directories"""
        self.print_header("DIRECTORY STRUCTURE CHECK")
        
        required_dirs = ["data", "logs", "data/rot_storage"]
        all_created = True
        
        for directory in required_dirs:
            path = Path(directory)
            try:
                path.mkdir(parents=True, exist_ok=True)
                self.print_success(f"Directory '{directory}' ready")
            except Exception as e:
                self.print_error(f"Failed to create '{directory}': {e}")
                all_created = False
        
        return all_created
    
    def check_env_file(self) -> bool:
        """Check environment file"""
        self.print_header("ENVIRONMENT FILE CHECK")
        
        env_file = Path(".env")
        
        if env_file.exists():
            self.print_success(".env file found")
            
            # Check required keys
            from dotenv import load_dotenv
            load_dotenv()
            
            required_keys = [
                "NEO4J_URI",
                "NEO4J_USERNAME",
                "NEO4J_PASSWORD",
                "API_PORT"
            ]
            
            missing = []
            for key in required_keys:
                if not os.getenv(key):
                    missing.append(key)
            
            if missing:
                self.print_warning(
                    f"Missing keys in .env: {', '.join(missing)}"
                )
                return False
            
            self.print_success("All required environment variables set")
            return True
        else:
            self.print_warning(
                ".env file not found. "
                "Run: cp .env.example .env (or create manually)"
            )
            return False
    
    def check_memory(self) -> bool:
        """Check available memory"""
        self.print_header("SYSTEM MEMORY CHECK")
        
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024 ** 3)
            total_gb = memory.total / (1024 ** 3)
            
            print(f"Total memory: {total_gb:.1f}GB")
            print(f"Available memory: {available_gb:.1f}GB")
            
            if available_gb >= 2:
                self.print_success(
                    f"Sufficient memory available ({available_gb:.1f}GB ≥ 2GB)"
                )
                return True
            else:
                self.print_warning(
                    f"Low memory: {available_gb:.1f}GB available. "
                    f"Recommended: ≥2GB"
                )
                return False
        
        except ImportError:
            self.print_warning(
                "psutil not installed. "
                "Install with: pip install psutil"
            )
            return True  # Don't fail, just warn
    
    def check_imports(self) -> bool:
        """Test actual imports"""
        self.print_header("IMPORT TEST")
        
        test_imports = [
            ("config", "AdaptiveGraphRAGConfig"),
            ("models", "AdaptiveMetaGraph"),
            ("retrieval_outcome_tracker", "RetrievalOutcomeTracker"),
            ("graph_edge_reweighting", "GraphEdgeReweightingEngine"),
            ("latent_relationship_discovery", "LatentRelationshipDiscovery"),
            ("meta_query_router", "MetaAgentQueryRouter"),
            ("embeddings_manager", "EmbeddingsManager"),
            ("neo4j_manager", "Neo4jManager"),
        ]
        
        all_imported = True
        
        for module_name, class_name in test_imports:
            try:
                module = importlib.import_module(module_name)
                getattr(module, class_name)
                self.print_success(
                    f"Successfully imported {class_name} from {module_name}"
                )
            except Exception as e:
                self.print_error(
                    f"Failed to import {class_name} "
                    f"from {module_name}: {e}"
                )
                all_imported = False
        
        return all_imported
    
    def run_all_checks(self) -> bool:
        """Run all checks"""
        print("\n")
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "AdaptiveGraphRAG Setup Verification".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "=" * 78 + "╝")
        
        checks = [
            self.check_python_version(),
            self.check_dependencies(),
            self.check_directories(),
            self.check_env_file(),
            self.check_memory(),
            self.check_neo4j_connection(),
            self.check_imports(),
        ]
        
        self.print_summary()
        
        return all(checks)
    
    def print_summary(self):
        """Print summary of checks"""
        self.print_header("SUMMARY")
        
        passed = len(self.checks_passed)
        failed = len(self.checks_failed)
        warnings = len(self.warnings)
        
        print(f"\n✓ Checks passed: {passed}")
        print(f"✗ Checks failed: {failed}")
        print(f"⚠ Warnings: {warnings}")
        
        if self.checks_failed:
            print("\n" + "-" * 80)
            print("FAILED CHECKS:")
            for i, failure in enumerate(self.checks_failed, 1):
                print(f"{i}. {failure}")
        
        if self.warnings:
            print("\n" + "-" * 80)
            print("WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {warning}")
        
        print("\n" + "-" * 80)
        
        if failed == 0:
            print("\n🎉 ALL CHECKS PASSED! Ready to run AdaptiveGraphRAG.\n")
            print("Next steps:")
            print("1. python demo_script.py          # Run demo")
            print("2. python api_server.py           # Start API server")
            print("3. curl http://localhost:8000/docs  # API documentation")
        else:
            print("\n⚠️  SETUP INCOMPLETE - Fix failed checks above\n")


if __name__ == "__main__":
    checker = AdaptiveRAGSetupChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)