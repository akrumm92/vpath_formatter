#!/usr/bin/env python3
"""
Convert brake_system_requirements to exact Polarion format matching workitem_with_links.json
Maps requirements to existing work items in Python/_default/Functional Concept - Template
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class PolarionExactConverter:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.document_id = "Python/_default/Functional Concept - Template"
        self.existing_workitems = {}
        self.work_items = []
        
    def load_project_analysis(self, file_path: str) -> Dict:
        """Load the project analysis to get existing work items"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Find the Functional Concept Template document
        for doc in data.get("documents", []):
            if doc.get("id") == self.document_id:
                # Extract work items from structure_analysis
                if "structure_analysis" in doc and "work_items" in doc["structure_analysis"]:
                    for item in doc["structure_analysis"]["work_items"]["data"]:
                        item_id = item.get("id")
                        item_type = item.get("attributes", {}).get("type")
                        item_title = item.get("attributes", {}).get("title", "")
                        
                        self.existing_workitems[item_id] = {
                            "type": item_type,
                            "title": item_title,
                            "attributes": item.get("attributes", {})
                        }
                return doc
        return None
    
    def load_brake_requirements(self, file_path: str) -> Dict:
        """Load the structured brake requirements"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def map_requirement_to_parent(self, requirement: Dict) -> str:
        """
        Map a brake requirement to the most appropriate existing work item
        Based on category and content matching
        """
        category = requirement.get("category", "").lower()
        title = requirement.get("title", "").lower()
        
        # Define mapping rules based on category and keywords
        mapping_rules = {
            "functional": {
                "keywords": ["mcp", "framework", "integration", "server", "composite"],
                "preferred": ["Python/FCTS-9156", "Python/FCTS-9157", "Python/FCTS-9158"]
            },
            "safety": {
                "keywords": ["safety", "goal", "critical"],
                "preferred": ["Python/FCTS-9155"]
            },
            "testing": {
                "keywords": ["test", "validation", "verification"],
                "preferred": ["Python/FCTS-9159", "Python/FCTS-9160", "Python/FCTS-9179", "Python/FCTS-9180"]
            },
            "interface": {
                "keywords": ["interface", "communication", "integration"],
                "preferred": ["Python/FCTS-9158", "Python/FCTS-9173"]
            },
            "performance": {
                "keywords": ["performance", "response", "efficiency"],
                "preferred": ["Python/FCTS-9175", "Python/FCTS-9178"]
            }
        }
        
        # Try to find best match based on category
        if category in mapping_rules:
            rule = mapping_rules[category]
            # Check if any keyword matches in title
            for keyword in rule["keywords"]:
                if keyword in title:
                    # Return first available preferred parent
                    for parent_id in rule["preferred"]:
                        if parent_id in self.existing_workitems:
                            return parent_id
        
        # Default fallback - use the parent requirement
        if "Python/FCTS-9156" in self.existing_workitems:
            return "Python/FCTS-9156"
        
        # Ultimate fallback - use first available requirement
        for item_id, item_data in self.existing_workitems.items():
            if item_data["type"] == "requirement":
                return item_id
        
        return "Python/FCTS-9156"  # Default if nothing found
    
    def create_workitem_exact_format(self, requirement: Dict, parent_id: str) -> Dict:
        """Create work item in exact format matching workitem_with_links.json"""
        
        # Map priority and severity
        priority_map = {
            "Critical": "high",
            "High": "high", 
            "Medium": "medium",
            "Low": "low"
        }
        
        severity_map = {
            "Safety": "safety_critical" if requirement.get("priority") == "Critical" else "must_have",
            "Functional": "must_have",
            "Performance": "must_have",
            "Interface": "should_have",
            "Environmental": "should_have",
            "Maintenance": "could_have",
            "Regulatory": "must_have",
            "Testing": "should_have"
        }
        
        workitem = {
            "type": "requirement",
            "title": f"{requirement['title']} {self.timestamp}",
            "description": {
                "type": "text/html",
                "value": f"<p>{requirement['description']}</p>"
            },
            "status": "draft",
            "severity": severity_map.get(requirement.get("category", "Functional"), "must_have"),
            "priority": priority_map.get(requirement.get("priority", "Medium"), "medium"),
            "relationships": {
                "module": {
                    "data": {
                        "type": "documents",
                        "id": self.document_id
                    }
                }
            }
        }
        
        return workitem
    
    def create_links(self, requirement: Dict, parent_id: str) -> List[Dict]:
        """Create links array in exact format"""
        links = [
            {
                "target_id": parent_id,
                "role": "has_parent",
                "description": f"Links to {self.existing_workitems.get(parent_id, {}).get('title', 'parent requirement')}"
            }
        ]
        
        # Add additional links based on category
        category = requirement.get("category", "")
        
        # Add related links for specific categories
        if category == "Safety":
            links.append({
                "target_id": "Python/FCTS-9155",
                "role": "relates_to",
                "description": "Related to MCP Safety Goal"
            })
        elif category == "Testing":
            links.append({
                "target_id": "Python/FCTS-9160",
                "role": "verifies",
                "description": "Verifies MCP Test Case"
            })
        
        return links
    
    def convert_requirements(self, brake_data: Dict) -> Dict:
        """Convert all brake requirements to Polarion format"""
        output = {
            "work_item": None,
            "links": [],
            "children": []
        }
        
        document = brake_data.get("document", {})
        all_requirements = []
        
        # Extract all requirements from chapters
        for chapter in document.get("chapters", []):
            # Process direct workitems
            if "workitems" in chapter:
                all_requirements.extend(chapter["workitems"])
            
            # Process subchapter workitems
            for subchapter in chapter.get("subchapters", []):
                if "workitems" in subchapter:
                    all_requirements.extend(subchapter["workitems"])
        
        # Group requirements by category for better organization
        categorized = {}
        for req in all_requirements:
            category = req.get("category", "Uncategorized")
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(req)
        
        # Create main parent work item (first requirement acts as parent)
        if all_requirements:
            first_req = all_requirements[0]
            parent_id = self.map_requirement_to_parent(first_req)
            
            # Create main work item
            output["work_item"] = self.create_workitem_exact_format(first_req, parent_id)
            output["links"] = self.create_links(first_req, parent_id)
            
            # Add rest as children
            for req in all_requirements[1:]:
                child_parent_id = self.map_requirement_to_parent(req)
                child_workitem = self.create_workitem_exact_format(req, child_parent_id)
                output["children"].append(child_workitem)
        
        return output
    
    def run(self, project_analysis_path: str, brake_requirements_path: str, output_path: str):
        """Main execution method"""
        print(f"📋 Loading project analysis from: {project_analysis_path}")
        doc = self.load_project_analysis(project_analysis_path)
        
        if not doc:
            print(f"❌ Could not find document: {self.document_id}")
            sys.exit(1)
        
        print(f"✅ Found document with {len(self.existing_workitems)} existing work items")
        
        # Show existing work items
        print("\n📌 Existing work items in document:")
        for item_id, item_data in list(self.existing_workitems.items())[:5]:
            print(f"   - {item_id}: {item_data['title']} ({item_data['type']})")
        if len(self.existing_workitems) > 5:
            print(f"   ... and {len(self.existing_workitems) - 5} more")
        
        print(f"\n📋 Loading brake requirements from: {brake_requirements_path}")
        brake_data = self.load_brake_requirements(brake_requirements_path)
        
        print("🔄 Converting requirements to Polarion format...")
        output = self.convert_requirements(brake_data)
        
        # Save output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Output saved to: {output_path}")
        print(f"📊 Statistics:")
        print(f"   - Main work item: 1")
        print(f"   - Child work items: {len(output.get('children', []))}")
        print(f"   - Links created: {len(output.get('links', []))}")
        
        # Validate format
        self.validate_output_format(output)
    
    def validate_output_format(self, output: Dict):
        """Validate that output matches exact format of workitem_with_links.json"""
        print("\n🔍 Validating output format...")
        
        required_keys = ["work_item", "links", "children"]
        for key in required_keys:
            if key not in output:
                print(f"   ❌ Missing required key: {key}")
            else:
                print(f"   ✅ Has key: {key}")
        
        # Validate work_item structure
        if "work_item" in output and output["work_item"]:
            wi_keys = ["type", "title", "description", "status", "severity", "priority", "relationships"]
            for key in wi_keys:
                if key in output["work_item"]:
                    print(f"   ✅ Work item has: {key}")
                else:
                    print(f"   ⚠️  Work item missing: {key}")
        
        # Validate links structure
        if "links" in output and output["links"]:
            for link in output["links"]:
                if all(k in link for k in ["target_id", "role", "description"]):
                    print(f"   ✅ Link valid: {link['target_id']} ({link['role']})")
                else:
                    print(f"   ❌ Invalid link structure")
        
        print("\n✅ Format validation complete!")

def main():
    """Main entry point with interactive document selection"""
    
    print("=" * 60)
    print("🚀 Brake Requirements to Polarion Converter")
    print("=" * 60)
    
    # Ask user for document selection
    print("\n📄 Which Polarion document should be used for linking?")
    print("Available: Python/_default/Functional Concept - Template")
    doc_input = input("Enter document ID (or press Enter for default): ").strip()
    
    if not doc_input:
        doc_id = "Python/_default/Functional Concept - Template"
        print(f"✅ Using default document: {doc_id}")
    else:
        doc_id = doc_input
        print(f"✅ Using document: {doc_id}")
    
    # File paths
    project_analysis = "Docs/Input/project_analysis_Python_20250809_114945.json"
    brake_requirements = "Docs/Input/brake_system_requirements_structured.json"
    output_file = "Docs/Output/brake_requirements_polarion_exact.json"
    
    # Create converter and run
    converter = PolarionExactConverter()
    converter.document_id = doc_id
    converter.run(project_analysis, brake_requirements, output_file)

if __name__ == "__main__":
    main()