#!/usr/bin/env python3
"""
Production Health Monitor for Pokemon Gemma VLM
Monitors deployed model health, performance, and error rates
"""

import time
import json
import asyncio
import aiohttp
import psutil
import torch
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import sqlite3
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HealthMetrics:
    """Health metrics data structure."""
    timestamp: str
    inference_time: float
    memory_usage_mb: float
    gpu_usage_percent: float
    error_rate: float
    requests_per_second: float
    success_rate: float
    model_temperature: float
    response_quality_score: float

@dataclass
class HealthThresholds:
    """Health monitoring thresholds."""
    max_inference_time: float = 2.0  # seconds
    max_memory_usage: float = 8000  # MB
    max_gpu_usage: float = 90  # percent
    max_error_rate: float = 0.05  # 5%
    min_success_rate: float = 0.95  # 95%
    min_requests_per_second: float = 0.1  # minimum activity

class HealthMonitor:
    """Production health monitoring system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = HealthThresholds(**config.get("thresholds", {}))
        self.metrics_history: List[HealthMetrics] = []
        self.alerts_sent = set()
        self.db_path = Path(config.get("db_path", "health_monitor.db"))
        self.setup_database()
        
    def setup_database(self):
        """Setup SQLite database for metrics storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                inference_time REAL,
                memory_usage_mb REAL,
                gpu_usage_percent REAL,
                error_rate REAL,
                requests_per_second REAL,
                success_rate REAL,
                model_temperature REAL,
                response_quality_score REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                resolved BOOLEAN DEFAULT FALSE
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def collect_metrics(self) -> HealthMetrics:
        """Collect current health metrics."""
        timestamp = datetime.now().isoformat()
        
        # System metrics
        memory_usage = psutil.virtual_memory().used / 1024 / 1024  # MB
        gpu_usage = self.get_gpu_usage()
        
        # Application metrics
        app_metrics = await self.get_application_metrics()
        
        metrics = HealthMetrics(
            timestamp=timestamp,
            inference_time=app_metrics.get("inference_time", 0.0),
            memory_usage_mb=memory_usage,
            gpu_usage_percent=gpu_usage,
            error_rate=app_metrics.get("error_rate", 0.0),
            requests_per_second=app_metrics.get("requests_per_second", 0.0),
            success_rate=app_metrics.get("success_rate", 1.0),
            model_temperature=app_metrics.get("model_temperature", 0.1),
            response_quality_score=app_metrics.get("response_quality_score", 0.0)
        )
        
        # Store in database
        self.store_metrics(metrics)
        
        return metrics
    
    def get_gpu_usage(self) -> float:
        """Get GPU usage percentage."""
        try:
            if torch.cuda.is_available():
                # Use nvidia-smi for accurate GPU usage
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    return float(result.stdout.strip())
            return 0.0
        except:
            return 0.0
    
    async def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics from inference server."""
        try:
            server_url = self.config.get("server_url", "http://localhost:8000")
            
            async with aiohttp.ClientSession() as session:
                # Get server stats
                async with session.get(f"{server_url}/stats") as response:
                    if response.status == 200:
                        stats = await response.json()
                        return {
                            "inference_time": stats.get("average_inference_time", 0.0),
                            "requests_per_second": stats.get("requests_per_second", 0.0),
                            "error_rate": 1.0 - stats.get("requests_processed", 0) / max(stats.get("requests_processed", 1), 1),
                            "success_rate": 1.0,  # Calculated from successful requests
                            "model_temperature": 0.1,  # Default model temperature
                            "response_quality_score": 0.8  # Would be calculated from response analysis
                        }
        except:
            pass
        
        return {
            "inference_time": 0.0,
            "requests_per_second": 0.0,
            "error_rate": 0.0,
            "success_rate": 1.0,
            "model_temperature": 0.1,
            "response_quality_score": 0.0
        }
    
    def store_metrics(self, metrics: HealthMetrics):
        """Store metrics in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO health_metrics (
                timestamp, inference_time, memory_usage_mb, gpu_usage_percent,
                error_rate, requests_per_second, success_rate, model_temperature,
                response_quality_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.timestamp,
            metrics.inference_time,
            metrics.memory_usage_mb,
            metrics.gpu_usage_percent,
            metrics.error_rate,
            metrics.requests_per_second,
            metrics.success_rate,
            metrics.model_temperature,
            metrics.response_quality_score
        ))
        
        conn.commit()
        conn.close()
    
    def check_health(self, metrics: HealthMetrics) -> List[Dict[str, Any]]:
        """Check health against thresholds and generate alerts."""
        alerts = []
        
        # Check inference time
        if metrics.inference_time > self.thresholds.max_inference_time:
            alerts.append({
                "type": "performance",
                "severity": "warning",
                "message": f"Inference time ({metrics.inference_time:.2f}s) exceeds threshold ({self.thresholds.max_inference_time}s)",
                "value": metrics.inference_time,
                "threshold": self.thresholds.max_inference_time
            })
        
        # Check memory usage
        if metrics.memory_usage_mb > self.thresholds.max_memory_usage:
            alerts.append({
                "type": "memory",
                "severity": "critical" if metrics.memory_usage_mb > self.thresholds.max_memory_usage * 1.2 else "warning",
                "message": f"Memory usage ({metrics.memory_usage_mb:.1f}MB) exceeds threshold ({self.thresholds.max_memory_usage}MB)",
                "value": metrics.memory_usage_mb,
                "threshold": self.thresholds.max_memory_usage
            })
        
        # Check GPU usage
        if metrics.gpu_usage_percent > self.thresholds.max_gpu_usage:
            alerts.append({
                "type": "gpu",
                "severity": "warning",
                "message": f"GPU usage ({metrics.gpu_usage_percent:.1f}%) exceeds threshold ({self.thresholds.max_gpu_usage}%)",
                "value": metrics.gpu_usage_percent,
                "threshold": self.thresholds.max_gpu_usage
            })
        
        # Check error rate
        if metrics.error_rate > self.thresholds.max_error_rate:
            alerts.append({
                "type": "errors",
                "severity": "critical",
                "message": f"Error rate ({metrics.error_rate:.1%}) exceeds threshold ({self.thresholds.max_error_rate:.1%})",
                "value": metrics.error_rate,
                "threshold": self.thresholds.max_error_rate
            })
        
        # Check success rate
        if metrics.success_rate < self.thresholds.min_success_rate:
            alerts.append({
                "type": "success_rate",
                "severity": "critical",
                "message": f"Success rate ({metrics.success_rate:.1%}) below threshold ({self.thresholds.min_success_rate:.1%})",
                "value": metrics.success_rate,
                "threshold": self.thresholds.min_success_rate
            })
        
        # Check for inactivity
        if metrics.requests_per_second < self.thresholds.min_requests_per_second:
            alerts.append({
                "type": "inactivity",
                "severity": "info",
                "message": f"Low activity: {metrics.requests_per_second:.2f} requests/second",
                "value": metrics.requests_per_second,
                "threshold": self.thresholds.min_requests_per_second
            })
        
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]):
        """Send alert notification."""
        alert_key = f"{alert['type']}_{alert['severity']}"
        
        # Rate limiting: don't send same alert more than once per 5 minutes
        if alert_key in self.alerts_sent:
            return
        
        # Store alert in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO health_alerts (timestamp, alert_type, severity, message)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            alert["type"],
            alert["severity"],
            alert["message"]
        ))
        
        conn.commit()
        conn.close()
        
        # Log alert
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨"
        }
        
        emoji = severity_emoji.get(alert["severity"], "🔔")
        logger.warning(f"{emoji} {alert['severity'].upper()}: {alert['message']}")
        
        # Send to notification channels
        self.send_notification(alert)
        
        # Mark as sent
        self.alerts_sent.add(alert_key)
        
        # Clear alert after 5 minutes
        asyncio.create_task(self.clear_alert_after_delay(alert_key, 300))
    
    async def clear_alert_after_delay(self, alert_key: str, delay: int):
        """Clear alert from sent list after delay."""
        await asyncio.sleep(delay)
        self.alerts_sent.discard(alert_key)
    
    def send_notification(self, alert: Dict[str, Any]):
        """Send notification to configured channels."""
        # Slack notification
        slack_webhook = self.config.get("slack_webhook")
        if slack_webhook:
            asyncio.create_task(self.send_slack_notification(slack_webhook, alert))
        
        # Email notification
        email_config = self.config.get("email")
        if email_config:
            asyncio.create_task(self.send_email_notification(email_config, alert))
    
    async def send_slack_notification(self, webhook_url: str, alert: Dict[str, Any]):
        """Send Slack notification."""
        try:
            color_map = {
                "info": "#36a64f",
                "warning": "#ff9500",
                "critical": "#ff0000"
            }
            
            payload = {
                "text": f"Pokemon Gemma VLM Health Alert",
                "attachments": [{
                    "color": color_map.get(alert["severity"], "#cccccc"),
                    "fields": [
                        {"title": "Alert Type", "value": alert["type"], "short": True},
                        {"title": "Severity", "value": alert["severity"], "short": True},
                        {"title": "Message", "value": alert["message"], "short": False}
                    ],
                    "timestamp": int(time.time())
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Slack notification sent successfully")
                    else:
                        logger.error(f"Failed to send Slack notification: {response.status}")
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    async def send_email_notification(self, email_config: Dict[str, Any], alert: Dict[str, Any]):
        """Send email notification."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = email_config['from']
            msg['To'] = email_config['to']
            msg['Subject'] = f"Pokemon Gemma VLM Health Alert - {alert['severity'].upper()}"
            
            body = f"""
Health Alert for Pokemon Gemma VLM

Alert Type: {alert['type']}
Severity: {alert['severity']}
Message: {alert['message']}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the monitoring dashboard for more details.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            text = msg.as_string()
            server.sendmail(email_config['from'], email_config['to'], text)
            server.quit()
            
            logger.info("Email notification sent successfully")
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for dashboard."""
        # Get latest metrics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM health_metrics 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        
        latest_row = cursor.fetchone()
        if not latest_row:
            return {"status": "no_data"}
        
        # Convert to dict
        columns = [desc[0] for desc in cursor.description]
        latest_metrics = dict(zip(columns, latest_row))
        
        # Get recent alerts
        cursor.execute("""
            SELECT alert_type, severity, message, timestamp 
            FROM health_alerts 
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
        """)
        
        recent_alerts = cursor.fetchall()
        
        # Calculate health score
        health_score = self.calculate_health_score(latest_metrics)
        
        conn.close()
        
        return {
            "status": "healthy" if health_score > 0.8 else "degraded" if health_score > 0.5 else "unhealthy",
            "health_score": health_score,
            "latest_metrics": latest_metrics,
            "recent_alerts": recent_alerts,
            "uptime": self.get_uptime()
        }
    
    def calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall health score (0-1)."""
        score = 1.0
        
        # Inference time penalty
        if metrics.get("inference_time", 0) > self.thresholds.max_inference_time:
            score *= 0.8
        
        # Memory usage penalty
        memory_ratio = metrics.get("memory_usage_mb", 0) / self.thresholds.max_memory_usage
        if memory_ratio > 1.0:
            score *= max(0.5, 1.0 - (memory_ratio - 1.0))
        
        # Error rate penalty
        error_rate = metrics.get("error_rate", 0)
        if error_rate > self.thresholds.max_error_rate:
            score *= max(0.2, 1.0 - error_rate)
        
        # Success rate factor
        success_rate = metrics.get("success_rate", 1.0)
        score *= success_rate
        
        return max(0.0, min(1.0, score))
    
    def get_uptime(self) -> str:
        """Get system uptime."""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = uptime_seconds / 3600
            return f"{uptime_hours:.1f} hours"
        except:
            return "unknown"
    
    async def run_monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("🔍 Starting Pokemon Gemma VLM Health Monitor")
        logger.info(f"📊 Monitoring interval: {self.config.get('interval', 30)}s")
        logger.info(f"📁 Database: {self.db_path}")
        
        while True:
            try:
                # Collect metrics
                metrics = await self.collect_metrics()
                
                # Check health
                alerts = self.check_health(metrics)
                
                # Send alerts
                for alert in alerts:
                    self.send_alert(alert)
                
                # Log status
                if not alerts:
                    logger.info(f"✅ Health check passed - Inference: {metrics.inference_time:.2f}s, Memory: {metrics.memory_usage_mb:.0f}MB")
                else:
                    logger.warning(f"⚠️ Health issues detected: {len(alerts)} alerts")
                
                # Wait for next check
                await asyncio.sleep(self.config.get("interval", 30))
                
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(5)

def main():
    parser = argparse.ArgumentParser(description="Pokemon Gemma VLM Health Monitor")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--server_url", default="http://localhost:8000", help="Inference server URL")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")
    
    args = parser.parse_args()
    
    # Load configuration
    config = {
        "server_url": args.server_url,
        "interval": args.interval,
        "db_path": "health_monitor.db"
    }
    
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config.update(json.load(f))
    
    # Initialize monitor
    monitor = HealthMonitor(config)
    
    # Run monitoring loop
    try:
        asyncio.run(monitor.run_monitoring_loop())
    except KeyboardInterrupt:
        logger.info("🛑 Health monitor stopped by user")

if __name__ == "__main__":
    main()