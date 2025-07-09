#!/usr/bin/env python3
"""
Model Registry for Pokemon Gemma VLM
Manages model versions, deployment tracking, and rollback capabilities
"""

import json
import time
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelVersion:
    """Model version information."""
    version_id: str
    model_name: str
    version_number: str
    checkpoint_path: str
    training_config: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    deployment_formats: List[str]
    created_at: str
    deployed_at: Optional[str] = None
    status: str = "training"  # training, ready, deployed, retired
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class DeploymentRecord:
    """Deployment record information."""
    deployment_id: str
    model_version_id: str
    environment: str
    deployment_config: Dict[str, Any]
    deployed_at: str
    status: str  # active, inactive, failed
    performance_data: Dict[str, Any]
    rollback_info: Optional[Dict[str, Any]] = None

class ModelRegistry:
    """Production model registry and versioning system."""
    
    def __init__(self, registry_path: str = "model_registry.db"):
        self.registry_path = Path(registry_path)
        self.setup_database()
        
    def setup_database(self):
        """Setup SQLite database for model registry."""
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        # Model versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_versions (
                version_id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                version_number TEXT NOT NULL,
                checkpoint_path TEXT NOT NULL,
                training_config TEXT,
                performance_metrics TEXT,
                deployment_formats TEXT,
                created_at TEXT NOT NULL,
                deployed_at TEXT,
                status TEXT NOT NULL DEFAULT 'training',
                tags TEXT,
                UNIQUE(model_name, version_number)
            )
        """)
        
        # Deployments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                deployment_id TEXT PRIMARY KEY,
                model_version_id TEXT NOT NULL,
                environment TEXT NOT NULL,
                deployment_config TEXT,
                deployed_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                performance_data TEXT,
                rollback_info TEXT,
                FOREIGN KEY (model_version_id) REFERENCES model_versions (version_id)
            )
        """)
        
        # Model artifacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_artifacts (
                artifact_id TEXT PRIMARY KEY,
                model_version_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                artifact_path TEXT NOT NULL,
                size_mb REAL,
                checksum TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (model_version_id) REFERENCES model_versions (version_id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"📁 Model registry initialized: {self.registry_path}")
    
    def register_model(self, 
                      model_name: str,
                      checkpoint_path: str,
                      training_config: Dict[str, Any],
                      performance_metrics: Dict[str, Any],
                      version_number: Optional[str] = None,
                      tags: Optional[List[str]] = None) -> str:
        """
        Register a new model version.
        
        Args:
            model_name: Name of the model
            checkpoint_path: Path to model checkpoint
            training_config: Training configuration used
            performance_metrics: Performance metrics from evaluation
            version_number: Version number (auto-generated if not provided)
            tags: Optional tags for categorization
            
        Returns:
            Version ID of registered model
        """
        
        # Generate version number if not provided
        if version_number is None:
            version_number = self.generate_version_number(model_name)
        
        # Generate version ID
        version_id = self.generate_version_id(model_name, version_number)
        
        # Create model version record
        model_version = ModelVersion(
            version_id=version_id,
            model_name=model_name,
            version_number=version_number,
            checkpoint_path=checkpoint_path,
            training_config=training_config,
            performance_metrics=performance_metrics,
            deployment_formats=[],
            created_at=datetime.now().isoformat(),
            tags=tags or []
        )
        
        # Store in database
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO model_versions (
                    version_id, model_name, version_number, checkpoint_path,
                    training_config, performance_metrics, deployment_formats,
                    created_at, status, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version_id,
                model_name,
                version_number,
                checkpoint_path,
                json.dumps(training_config),
                json.dumps(performance_metrics),
                json.dumps([]),
                model_version.created_at,
                "ready",
                json.dumps(tags or [])
            ))
            
            conn.commit()
            logger.info(f"✅ Model registered: {model_name} v{version_number} ({version_id})")
            
            return version_id
            
        except sqlite3.IntegrityError:
            logger.error(f"❌ Model version already exists: {model_name} v{version_number}")
            raise ValueError(f"Model version already exists: {model_name} v{version_number}")
        finally:
            conn.close()
    
    def add_deployment_format(self, version_id: str, format_type: str, artifact_path: str) -> str:
        """
        Add a deployment format to existing model version.
        
        Args:
            version_id: Model version ID
            format_type: Format type (pytorch, gguf, mlx, etc.)
            artifact_path: Path to format artifact
            
        Returns:
            Artifact ID
        """
        
        # Calculate artifact info
        artifact_path = Path(artifact_path)
        size_mb = self.calculate_artifact_size(artifact_path)
        checksum = self.calculate_checksum(artifact_path)
        
        # Generate artifact ID
        artifact_id = f"{version_id}_{format_type}_{int(time.time())}"
        
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        try:
            # Add artifact record
            cursor.execute("""
                INSERT INTO model_artifacts (
                    artifact_id, model_version_id, artifact_type, artifact_path,
                    size_mb, checksum, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                artifact_id,
                version_id,
                format_type,
                str(artifact_path),
                size_mb,
                checksum,
                datetime.now().isoformat()
            ))
            
            # Update model version deployment formats
            cursor.execute("""
                SELECT deployment_formats FROM model_versions WHERE version_id = ?
            """, (version_id,))
            
            result = cursor.fetchone()
            if result:
                current_formats = json.loads(result[0])
                if format_type not in current_formats:
                    current_formats.append(format_type)
                    
                    cursor.execute("""
                        UPDATE model_versions 
                        SET deployment_formats = ? 
                        WHERE version_id = ?
                    """, (json.dumps(current_formats), version_id))
            
            conn.commit()
            logger.info(f"✅ Added {format_type} format to model {version_id}")
            
            return artifact_id
            
        finally:
            conn.close()
    
    def deploy_model(self, 
                    version_id: str,
                    environment: str,
                    deployment_config: Dict[str, Any]) -> str:
        """
        Deploy a model version to an environment.
        
        Args:
            version_id: Model version ID to deploy
            environment: Deployment environment (staging, production, etc.)
            deployment_config: Deployment configuration
            
        Returns:
            Deployment ID
        """
        
        # Generate deployment ID
        deployment_id = f"deploy_{version_id}_{environment}_{int(time.time())}"
        
        # Create deployment record
        deployment = DeploymentRecord(
            deployment_id=deployment_id,
            model_version_id=version_id,
            environment=environment,
            deployment_config=deployment_config,
            deployed_at=datetime.now().isoformat(),
            status="active",
            performance_data={}
        )
        
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        try:
            # Deactivate previous deployments in same environment
            cursor.execute("""
                UPDATE deployments 
                SET status = 'inactive' 
                WHERE environment = ? AND status = 'active'
            """, (environment,))
            
            # Add new deployment
            cursor.execute("""
                INSERT INTO deployments (
                    deployment_id, model_version_id, environment, deployment_config,
                    deployed_at, status, performance_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                deployment_id,
                version_id,
                environment,
                json.dumps(deployment_config),
                deployment.deployed_at,
                "active",
                json.dumps({})
            ))
            
            # Update model version status
            cursor.execute("""
                UPDATE model_versions 
                SET status = 'deployed', deployed_at = ?
                WHERE version_id = ?
            """, (deployment.deployed_at, version_id))
            
            conn.commit()
            logger.info(f"🚀 Model deployed: {version_id} → {environment} ({deployment_id})")
            
            return deployment_id
            
        finally:
            conn.close()
    
    def rollback_deployment(self, deployment_id: str, target_version_id: str) -> bool:
        """
        Rollback deployment to a previous version.
        
        Args:
            deployment_id: Current deployment ID
            target_version_id: Target version ID to rollback to
            
        Returns:
            True if rollback successful
        """
        
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        try:
            # Get current deployment info
            cursor.execute("""
                SELECT environment, deployment_config FROM deployments
                WHERE deployment_id = ?
            """, (deployment_id,))
            
            result = cursor.fetchone()
            if not result:
                logger.error(f"❌ Deployment not found: {deployment_id}")
                return False
            
            environment, deployment_config = result
            deployment_config = json.loads(deployment_config)
            
            # Create rollback deployment
            rollback_deployment_id = self.deploy_model(
                target_version_id,
                environment,
                deployment_config
            )
            
            # Update original deployment with rollback info
            cursor.execute("""
                UPDATE deployments 
                SET rollback_info = ?, status = 'inactive'
                WHERE deployment_id = ?
            """, (
                json.dumps({
                    "rollback_to": target_version_id,
                    "rollback_deployment_id": rollback_deployment_id,
                    "rollback_at": datetime.now().isoformat()
                }),
                deployment_id
            ))
            
            conn.commit()
            logger.info(f"🔄 Rollback completed: {deployment_id} → {target_version_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False
        finally:
            conn.close()
    
    def get_model_versions(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get model versions, optionally filtered by model name."""
        
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        if model_name:
            cursor.execute("""
                SELECT * FROM model_versions 
                WHERE model_name = ? 
                ORDER BY created_at DESC
            """, (model_name,))
        else:
            cursor.execute("""
                SELECT * FROM model_versions 
                ORDER BY created_at DESC
            """)
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            version_dict = dict(zip(columns, row))
            # Parse JSON fields
            version_dict["training_config"] = json.loads(version_dict["training_config"])
            version_dict["performance_metrics"] = json.loads(version_dict["performance_metrics"])
            version_dict["deployment_formats"] = json.loads(version_dict["deployment_formats"])
            version_dict["tags"] = json.loads(version_dict["tags"])
            results.append(version_dict)
        
        conn.close()
        return results
    
    def get_deployments(self, environment: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get deployments, optionally filtered by environment."""
        
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        if environment:
            cursor.execute("""
                SELECT d.*, mv.model_name, mv.version_number
                FROM deployments d
                JOIN model_versions mv ON d.model_version_id = mv.version_id
                WHERE d.environment = ?
                ORDER BY d.deployed_at DESC
            """, (environment,))
        else:
            cursor.execute("""
                SELECT d.*, mv.model_name, mv.version_number
                FROM deployments d
                JOIN model_versions mv ON d.model_version_id = mv.version_id
                ORDER BY d.deployed_at DESC
            """)
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            deployment_dict = dict(zip(columns, row))
            # Parse JSON fields
            deployment_dict["deployment_config"] = json.loads(deployment_dict["deployment_config"])
            deployment_dict["performance_data"] = json.loads(deployment_dict["performance_data"])
            if deployment_dict["rollback_info"]:
                deployment_dict["rollback_info"] = json.loads(deployment_dict["rollback_info"])
            results.append(deployment_dict)
        
        conn.close()
        return results
    
    def get_model_artifacts(self, version_id: str) -> List[Dict[str, Any]]:
        """Get artifacts for a model version."""
        
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM model_artifacts 
            WHERE model_version_id = ?
            ORDER BY created_at DESC
        """, (version_id,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    
    def update_deployment_performance(self, deployment_id: str, performance_data: Dict[str, Any]):
        """Update deployment performance data."""
        
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE deployments 
            SET performance_data = ?
            WHERE deployment_id = ?
        """, (json.dumps(performance_data), deployment_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📊 Updated performance data for deployment {deployment_id}")
    
    def retire_model(self, version_id: str):
        """Retire a model version."""
        
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE model_versions 
            SET status = 'retired'
            WHERE version_id = ?
        """, (version_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🏁 Model version retired: {version_id}")
    
    def generate_version_number(self, model_name: str) -> str:
        """Generate next version number for model."""
        
        conn = sqlite3.connect(self.registry_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT version_number FROM model_versions 
            WHERE model_name = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (model_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Parse version number and increment
            last_version = result[0]
            try:
                # Assume semantic versioning (e.g., "1.0.0")
                parts = last_version.split(".")
                patch = int(parts[2]) + 1
                return f"{parts[0]}.{parts[1]}.{patch}"
            except:
                # Fallback to timestamp
                return f"1.0.{int(time.time())}"
        else:
            return "1.0.0"
    
    def generate_version_id(self, model_name: str, version_number: str) -> str:
        """Generate unique version ID."""
        content = f"{model_name}_{version_number}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def calculate_artifact_size(self, path: Path) -> float:
        """Calculate artifact size in MB."""
        if path.is_file():
            return path.stat().st_size / 1024 / 1024
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1024 / 1024
        return 0.0
    
    def calculate_checksum(self, path: Path) -> str:
        """Calculate artifact checksum."""
        if path.is_file():
            hash_md5 = hashlib.md5()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        elif path.is_dir():
            # For directories, hash the list of files and their checksums
            files = sorted(path.rglob("*"))
            hash_md5 = hashlib.md5()
            for file in files:
                if file.is_file():
                    hash_md5.update(str(file.relative_to(path)).encode())
                    with open(file, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
            return hash_md5.hexdigest()
        return ""
    
    def export_registry(self, output_path: str):
        """Export registry to JSON file."""
        
        export_data = {
            "models": self.get_model_versions(),
            "deployments": self.get_deployments(),
            "exported_at": datetime.now().isoformat()
        }
        
        # Add artifacts for each model
        for model in export_data["models"]:
            model["artifacts"] = self.get_model_artifacts(model["version_id"])
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"📤 Registry exported to: {output_path}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate registry summary report."""
        
        models = self.get_model_versions()
        deployments = self.get_deployments()
        
        # Statistics
        model_stats = {}
        for model in models:
            name = model["model_name"]
            if name not in model_stats:
                model_stats[name] = {"versions": 0, "deployed": 0}
            model_stats[name]["versions"] += 1
            if model["status"] == "deployed":
                model_stats[name]["deployed"] += 1
        
        deployment_stats = {}
        for deployment in deployments:
            env = deployment["environment"]
            if env not in deployment_stats:
                deployment_stats[env] = {"active": 0, "inactive": 0}
            deployment_stats[env][deployment["status"]] += 1
        
        return {
            "summary": {
                "total_models": len(models),
                "total_deployments": len(deployments),
                "active_deployments": len([d for d in deployments if d["status"] == "active"])
            },
            "model_stats": model_stats,
            "deployment_stats": deployment_stats,
            "recent_models": models[:5],
            "recent_deployments": deployments[:5]
        }

def main():
    parser = argparse.ArgumentParser(description="Pokemon Gemma VLM Model Registry")
    parser.add_argument("--registry", default="model_registry.db", help="Registry database path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Register command
    register_parser = subparsers.add_parser("register", help="Register new model")
    register_parser.add_argument("--name", required=True, help="Model name")
    register_parser.add_argument("--checkpoint", required=True, help="Checkpoint path")
    register_parser.add_argument("--config", required=True, help="Training config JSON file")
    register_parser.add_argument("--metrics", required=True, help="Performance metrics JSON file")
    register_parser.add_argument("--version", help="Version number")
    register_parser.add_argument("--tags", nargs="*", help="Model tags")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List models")
    list_parser.add_argument("--model", help="Filter by model name")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy model")
    deploy_parser.add_argument("--version-id", required=True, help="Version ID to deploy")
    deploy_parser.add_argument("--environment", required=True, help="Deployment environment")
    deploy_parser.add_argument("--config", required=True, help="Deployment config JSON file")
    
    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback deployment")
    rollback_parser.add_argument("--deployment-id", required=True, help="Deployment ID")
    rollback_parser.add_argument("--target-version", required=True, help="Target version ID")
    
    # Report command
    subparsers.add_parser("report", help="Generate registry report")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export registry")
    export_parser.add_argument("--output", required=True, help="Output file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize registry
    registry = ModelRegistry(args.registry)
    
    if args.command == "register":
        # Load config and metrics
        with open(args.config) as f:
            config = json.load(f)
        with open(args.metrics) as f:
            metrics = json.load(f)
        
        version_id = registry.register_model(
            args.name,
            args.checkpoint,
            config,
            metrics,
            args.version,
            args.tags
        )
        print(f"✅ Model registered: {version_id}")
    
    elif args.command == "list":
        models = registry.get_model_versions(args.model)
        
        print(f"\n📋 Model Versions {'for ' + args.model if args.model else ''}")
        print("=" * 60)
        
        for model in models:
            print(f"ID: {model['version_id']}")
            print(f"Name: {model['model_name']} v{model['version_number']}")
            print(f"Status: {model['status']}")
            print(f"Created: {model['created_at']}")
            print(f"Formats: {', '.join(model['deployment_formats'])}")
            print(f"Tags: {', '.join(model['tags'])}")
            print("-" * 40)
    
    elif args.command == "deploy":
        with open(args.config) as f:
            config = json.load(f)
        
        deployment_id = registry.deploy_model(
            args.version_id,
            args.environment,
            config
        )
        print(f"✅ Model deployed: {deployment_id}")
    
    elif args.command == "rollback":
        success = registry.rollback_deployment(
            args.deployment_id,
            args.target_version
        )
        if success:
            print("✅ Rollback completed successfully")
        else:
            print("❌ Rollback failed")
    
    elif args.command == "report":
        report = registry.generate_report()
        print("\n📊 Registry Report")
        print("=" * 40)
        print(f"Total Models: {report['summary']['total_models']}")
        print(f"Total Deployments: {report['summary']['total_deployments']}")
        print(f"Active Deployments: {report['summary']['active_deployments']}")
        print("\nModel Statistics:")
        for model_name, stats in report['model_stats'].items():
            print(f"  {model_name}: {stats['versions']} versions, {stats['deployed']} deployed")
    
    elif args.command == "export":
        registry.export_registry(args.output)
        print(f"✅ Registry exported to: {args.output}")

if __name__ == "__main__":
    main()