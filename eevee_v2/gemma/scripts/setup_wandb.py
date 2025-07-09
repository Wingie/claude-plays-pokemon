#!/usr/bin/env python3
"""
Weights & Biases Setup Script for Pokemon Gemma VLM Training
Configures wandb for experiment tracking and monitoring
"""

import argparse
import os
import yaml
from pathlib import Path
import wandb
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_wandb_config(config_path: str = "wandb_config.yaml") -> dict:
    """Load wandb configuration from YAML file."""
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return {}
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def setup_wandb_environment(wandb_config: dict) -> None:
    """Setup wandb environment variables."""
    
    # Set project and entity
    if 'project' in wandb_config:
        os.environ['WANDB_PROJECT'] = wandb_config['project']
    
    if 'entity' in wandb_config:
        os.environ['WANDB_ENTITY'] = wandb_config['entity']
    
    # Set logging configuration
    logging_config = wandb_config.get('logging', {})
    
    if logging_config.get('log_code', True):
        os.environ['WANDB_LOG_CODE'] = 'true'
    
    if not logging_config.get('log_graph', False):
        os.environ['WANDB_LOG_MODEL'] = 'false'
    
    # System monitoring
    if logging_config.get('track_system', True):
        os.environ['WANDB_MONITOR_GPU'] = 'true'
    
    logger.info("✅ Wandb environment configured")


def initialize_wandb_run(run_config: dict, wandb_config: dict) -> wandb.run:
    """Initialize a new wandb run with proper configuration."""
    
    # Extract experiment defaults
    defaults = wandb_config.get('experiment_defaults', {})
    
    # Generate run name
    name_template = wandb_config.get('run_name_template', 'pokemon-gemma-{timestamp}')
    
    # Format run name with config values
    run_name = name_template.format(
        model_size=run_config.get('model_size', '4b'),
        batch_size=run_config.get('batch_size', 1),
        learning_rate=run_config.get('learning_rate', '2e-4'),
        lora_r=run_config.get('lora_r', 64),
        timestamp=wandb.util.generate_id()
    )
    
    # Initialize run
    run = wandb.init(
        project=wandb_config.get('project', 'pokemon-gemma-vlm'),
        entity=wandb_config.get('entity'),
        name=run_name,
        tags=defaults.get('tags', []),
        group=defaults.get('group'),
        notes=defaults.get('notes'),
        config=run_config
    )
    
    logger.info(f"🚀 Wandb run initialized: {run.name}")
    return run


def setup_model_watching(model, wandb_config: dict) -> None:
    """Setup model watching for gradient and parameter logging."""
    
    watch_config = wandb_config.get('logging', {}).get('watch_model', {})
    
    if watch_config:
        wandb.watch(
            model,
            log=watch_config.get('log', 'all'),
            log_freq=watch_config.get('log_freq', 100),
            log_graph=watch_config.get('log_graph', False)
        )
        
        logger.info("👁️ Model watching enabled")


def log_sample_predictions(samples: list, predictions: list, epoch: int) -> None:
    """Log sample predictions as wandb media."""
    
    prediction_table = wandb.Table(columns=["Epoch", "Context", "Question", "Prediction", "Ground Truth"])
    
    for i, (sample, pred) in enumerate(zip(samples[:8], predictions[:8])):  # Limit to 8 samples
        prediction_table.add_data(
            epoch,
            sample.get('context', '')[:200] + '...',  # Truncate long context
            sample.get('question', ''),
            pred,
            sample.get('output', '')
        )
    
    wandb.log({"predictions": prediction_table})


def create_sweep(wandb_config: dict, sweep_name: str = None) -> str:
    """Create a wandb sweep for hyperparameter optimization."""
    
    sweep_config = wandb_config.get('sweep_defaults', {})
    
    if not sweep_config:
        logger.error("No sweep configuration found in wandb_config.yaml")
        return None
    
    # Add program to sweep config
    sweep_config['program'] = 'scripts/sft_pokemon_gemma3.py'
    
    # Create sweep
    sweep_id = wandb.sweep(
        sweep=sweep_config,
        project=wandb_config.get('project', 'pokemon-gemma-vlm'),
        entity=wandb_config.get('entity')
    )
    
    logger.info(f"🔄 Sweep created: {sweep_id}")
    logger.info(f"Run with: wandb agent {sweep_id}")
    
    return sweep_id


def setup_alerts(wandb_config: dict) -> None:
    """Setup wandb alerts for monitoring."""
    
    alerts_config = wandb_config.get('alerts', {})
    
    if not alerts_config:
        return
    
    # GPU utilization alert
    gpu_threshold = alerts_config.get('gpu_utilization_threshold', 0.8)
    if gpu_threshold:
        wandb.alert(
            title="Low GPU Utilization",
            text=f"GPU utilization below {gpu_threshold*100}%",
            level=wandb.AlertLevel.WARN
        )
    
    # Memory usage alert
    memory_threshold = alerts_config.get('memory_threshold', 0.9)
    if memory_threshold:
        wandb.alert(
            title="High Memory Usage",
            text=f"Memory usage above {memory_threshold*100}%",
            level=wandb.AlertLevel.WARN
        )
    
    logger.info("🚨 Alerts configured")


def validate_wandb_setup() -> bool:
    """Validate that wandb is properly configured."""
    
    try:
        # Check if wandb is logged in
        api = wandb.Api()
        user = api.viewer
        
        logger.info(f"✅ Wandb authenticated as: {user.username}")
        
        # Test project access
        if 'WANDB_PROJECT' in os.environ:
            project_name = os.environ['WANDB_PROJECT']
            entity_name = os.environ.get('WANDB_ENTITY', user.username)
            
            try:
                project = api.project(name=project_name, entity=entity_name)
                logger.info(f"✅ Project accessible: {project.name}")
            except Exception as e:
                logger.warning(f"⚠️ Project access issue: {e}")
                # Project might not exist yet, which is okay
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Wandb validation failed: {e}")
        logger.error("Run 'wandb login' to authenticate")
        return False


def main():
    parser = argparse.ArgumentParser(description="Setup Weights & Biases for Pokemon Gemma VLM training")
    parser.add_argument("--config", default="wandb_config.yaml", help="Wandb config file")
    parser.add_argument("--create-sweep", action="store_true", help="Create hyperparameter sweep")
    parser.add_argument("--validate", action="store_true", help="Validate wandb setup")
    parser.add_argument("--test-run", action="store_true", help="Create test run")
    
    args = parser.parse_args()
    
    # Load configuration
    wandb_config = load_wandb_config(args.config)
    
    if args.validate:
        # Validate setup
        if validate_wandb_setup():
            logger.info("🎉 Wandb setup is valid!")
        else:
            logger.error("❌ Wandb setup validation failed")
            return 1
    
    if args.create_sweep:
        # Create hyperparameter sweep
        sweep_id = create_sweep(wandb_config)
        if sweep_id:
            logger.info(f"Sweep created: {sweep_id}")
    
    if args.test_run:
        # Create test run
        setup_wandb_environment(wandb_config)
        
        test_config = {
            "model_name": "google/gemma-3-4b-it",
            "batch_size": 1,
            "learning_rate": 2e-4,
            "lora_r": 64,
            "test_run": True
        }
        
        run = initialize_wandb_run(test_config, wandb_config)
        
        # Log some test metrics
        for step in range(10):
            wandb.log({
                "test/loss": 2.0 - step * 0.1,
                "test/accuracy": step * 0.05,
                "step": step
            })
        
        run.finish()
        logger.info("✅ Test run completed")
    
    # Setup environment for future runs
    setup_wandb_environment(wandb_config)
    
    logger.info("🎮 Wandb setup complete! Ready for Pokemon Gemma VLM training.")


if __name__ == "__main__":
    main()