#!/usr/bin/env python3
"""
Neo4j Database Explorer Script
Recursively explores Neo4j database through Cypher queries for 5 turns
"""

import os
import sys
from neo4j import GraphDatabase
import json
from typing import Dict, List, Any, Optional
import time

class Neo4jExplorer:
    def __init__(self, uri: str = "neo4j://localhost:7687", username: str = "neo4j", password: str = "password"):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.exploration_history = []
        self.discovered_schemas = set()
        self.turn_count = 0
        
    def close(self):
        if self.driver:
            self.driver.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                records = []
                for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        if hasattr(value, '_properties'):
                            record_dict[key] = dict(value._properties)
                            record_dict[key]['_labels'] = list(value._labels) if hasattr(value, '_labels') else []
                            record_dict[key]['_id'] = value.element_id if hasattr(value, 'element_id') else str(value.id)
                        elif hasattr(value, 'type'):
                            record_dict[key] = {
                                'type': value.type,
                                'start': value.start_node.element_id if hasattr(value.start_node, 'element_id') else str(value.start_node.id),
                                'end': value.end_node.element_id if hasattr(value.end_node, 'element_id') else str(value.end_node.id),
                                'properties': dict(value._properties) if hasattr(value, '_properties') else {}
                            }
                        else:
                            record_dict[key] = value
                    records.append(record_dict)
                return records
        except Exception as e:
            print(f"Query failed: {query}")
            print(f"Error: {str(e)}")
            return []
    
    def print_results(self, query: str, results: List[Dict], turn: int):
        """Pretty print query results"""
        print(f"\n{'='*80}")
        print(f"TURN {turn}: QUERY EXPLORATION")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"Results count: {len(results)}")
        print(f"{'='*80}")
        
        if not results:
            print("No results found.")
            return
            
        for i, record in enumerate(results[:10]):  # Limit to first 10 results
            print(f"\nRecord {i+1}:")
            for key, value in record.items():
                if isinstance(value, dict):
                    print(f"  {key}: {json.dumps(value, indent=4, default=str)}")
                else:
                    print(f"  {key}: {value}")
        
        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more records")
    
    def discover_schema(self) -> Dict:
        """Discover database schema"""
        print(f"\n🔍 DISCOVERING DATABASE SCHEMA...")
        
        # Get node labels
        labels_query = "CALL db.labels()"
        labels = self.execute_query(labels_query)
        node_labels = [record['label'] for record in labels]
        
        # Get relationship types
        rel_types_query = "CALL db.relationshipTypes()"
        rel_types = self.execute_query(rel_types_query)
        relationship_types = [record['relationshipType'] for record in rel_types]
        
        # Get property keys
        prop_keys_query = "CALL db.propertyKeys()"
        prop_keys = self.execute_query(prop_keys_query)
        property_keys = [record['propertyKey'] for record in prop_keys]
        
        schema = {
            'node_labels': node_labels,
            'relationship_types': relationship_types,
            'property_keys': property_keys
        }
        
        print(f"📊 SCHEMA DISCOVERY RESULTS:")
        print(f"  Node Labels ({len(node_labels)}): {node_labels}")
        print(f"  Relationship Types ({len(relationship_types)}): {relationship_types}")
        print(f"  Property Keys ({len(property_keys)}): {property_keys[:20]}{'...' if len(property_keys) > 20 else ''}")
        
        return schema
    
    def generate_exploration_queries(self, schema: Dict, turn: int) -> List[str]:
        """Generate queries based on discovered schema and turn number"""
        queries = []
        
        if turn == 1:
            # Basic exploration - count nodes and relationships
            queries.extend([
                "MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC LIMIT 10",
                "MATCH ()-[r]->() RETURN type(r) as relationship_type, count(r) as count ORDER BY count DESC LIMIT 10"
            ])
        
        elif turn == 2:
            # Explore specific node types
            for label in schema['node_labels'][:3]:  # First 3 labels
                queries.append(f"MATCH (n:{label}) RETURN n LIMIT 5")
        
        elif turn == 3:
            # Explore relationships between nodes
            for rel_type in schema['relationship_types'][:3]:  # First 3 relationship types
                queries.append(f"MATCH (a)-[r:{rel_type}]->(b) RETURN a, r, b LIMIT 5")
        
        elif turn == 4:
            # Complex patterns and subgraphs
            queries.extend([
                "MATCH (n)-[r1]->(m)-[r2]->(o) RETURN n, r1, m, r2, o LIMIT 5",
                "MATCH (n) WHERE size((n)--()) > 3 RETURN n, size((n)--()) as degree ORDER BY degree DESC LIMIT 5"
            ])
        
        elif turn == 5:
            # Advanced analytics
            queries.extend([
                "MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n, count(r) as out_degree ORDER BY out_degree DESC LIMIT 10",
                "CALL apoc.meta.graph() YIELD nodes, relationships RETURN nodes, relationships",
                "MATCH path = shortestPath((a)-[*..5]-(b)) WHERE id(a) < id(b) RETURN path LIMIT 3"
            ])
        
        return queries
    
    def explore_turn(self, schema: Dict, turn: int):
        """Execute exploration for a single turn"""
        print(f"\n🚀 STARTING TURN {turn}")
        queries = self.generate_exploration_queries(schema, turn)
        
        for query in queries:
            try:
                results = self.execute_query(query)
                self.print_results(query, results, turn)
                
                # Store exploration history
                self.exploration_history.append({
                    'turn': turn,
                    'query': query,
                    'result_count': len(results),
                    'timestamp': time.time()
                })
                
                # Brief pause between queries
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Failed to execute query in turn {turn}: {query}")
                print(f"Error: {str(e)}")
    
    def run_full_exploration(self):
        """Run the complete 5-turn exploration"""
        print("🎯 STARTING NEO4J DATABASE EXPLORATION")
        print("=" * 80)
        
        try:
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✅ Connected to Neo4j successfully!")
            
            # Discover schema first
            schema = self.discover_schema()
            
            # Run 5 turns of exploration
            for turn in range(1, 6):
                self.explore_turn(schema, turn)
                self.turn_count = turn
            
            # Final summary
            self.print_exploration_summary()
            
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {str(e)}")
            print("Make sure Neo4j is running on neo4j://localhost:7687")
            return False
        
        return True
    
    def print_exploration_summary(self):
        """Print summary of the exploration"""
        print(f"\n{'='*80}")
        print("🎉 EXPLORATION COMPLETE - SUMMARY")
        print(f"{'='*80}")
        print(f"Total turns completed: {self.turn_count}")
        print(f"Total queries executed: {len(self.exploration_history)}")
        
        total_results = sum(entry['result_count'] for entry in self.exploration_history)
        print(f"Total records discovered: {total_results}")
        
        print(f"\nQuery execution summary:")
        for entry in self.exploration_history:
            print(f"  Turn {entry['turn']}: {entry['result_count']} results - {entry['query'][:60]}...")

def main():
    """Main execution function"""
    # Environment variables with defaults
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
    neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
    
    print(f"Connecting to Neo4j at: {neo4j_uri}")
    print(f"Username: {neo4j_username}")
    
    explorer = Neo4jExplorer(neo4j_uri, neo4j_username, neo4j_password)
    
    try:
        success = explorer.run_full_exploration()
        if success:
            print("\n✅ Exploration completed successfully!")
        else:
            print("\n❌ Exploration failed!")
            sys.exit(1)
    finally:
        explorer.close()

if __name__ == "__main__":
    main()