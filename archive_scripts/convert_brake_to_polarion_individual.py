#!/usr/bin/env python3
"""
Convert brake_system_requirements to individual Polarion work items
Each requirement becomes a separate work item with links to matching headings
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class PolarionIndividualConverter:
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
    
    def extract_requirements_with_context(self, brake_data: Dict) -> List[Tuple[Dict, str, str]]:
        """
        Extract all requirements with their chapter context
        Returns list of tuples: (requirement, chapter_heading, subchapter_heading)
        """
        requirements_with_context = []
        document = brake_data.get("document", {})
        
        for chapter in document.get("chapters", []):
            chapter_heading = chapter.get("heading", "")
            
            # Process direct workitems in chapter
            if "workitems" in chapter:
                for req in chapter["workitems"]:
                    requirements_with_context.append((req, chapter_heading, None))
            
            # Process subchapter workitems
            for subchapter in chapter.get("subchapters", []):
                subchapter_heading = subchapter.get("heading", "")
                if "workitems" in subchapter:
                    for req in subchapter["workitems"]:
                        requirements_with_context.append((req, chapter_heading, subchapter_heading))
        
        return requirements_with_context
    
    def match_heading_to_workitem(self, chapter: str, subchapter: Optional[str] = None) -> str:
        """
        Match a chapter/subchapter heading to the most appropriate existing work item
        """
        # Clean chapter/subchapter titles (remove numbering)
        import re
        chapter_clean = re.sub(r'^\d+\.?\d*\s+', '', chapter).lower()
        subchapter_clean = re.sub(r'^\d+\.?\d*\s+', '', subchapter).lower() if subchapter else ""
        
        # Mapping rules based on chapter content
        heading_map = {
            # Functional chapters
            "functional": ["Python/FCTS-9156", "Python/FCTS-9157", "Python/FCTS-9158"],
            "primary": ["Python/FCTS-9157"],  # Proto-Server for primary functions
            "advanced": ["Python/FCTS-9158"],  # Composite-Server for advanced
            "brake function": ["Python/FCTS-9156", "Python/FCTS-9157"],
            
            # Performance chapters
            "performance": ["Python/FCTS-9175", "Python/FCTS-9178"],
            "stopping": ["Python/FCTS-9175"],
            "response": ["Python/FCTS-9178"],
            "durability": ["Python/FCTS-9175"],
            
            # Safety chapters
            "safety": ["Python/FCTS-9155"],
            "redundancy": ["Python/FCTS-9155"],
            "monitoring": ["Python/FCTS-9155"],
            "warning": ["Python/FCTS-9155"],
            
            # Interface chapters
            "interface": ["Python/FCTS-9173", "Python/FCTS-9158"],
            "communication": ["Python/FCTS-9173"],
            "integration": ["Python/FCTS-9158", "Python/FCTS-9173"],
            "sensor": ["Python/FCTS-9173"],
            
            # Environmental chapters
            "environmental": ["Python/FCTS-9181", "Python/FCTS-9178"],
            "temperature": ["Python/FCTS-9181"],
            "corrosion": ["Python/FCTS-9181"],
            
            # Maintenance chapters
            "maintenance": ["Python/FCTS-9167", "Python/FCTS-9168"],
            "service": ["Python/FCTS-9167"],
            "diagnostic": ["Python/FCTS-9168"],
            
            # Regulatory chapters
            "regulatory": ["Python/FCTS-9156", "Python/FCTS-9155"],
            "compliance": ["Python/FCTS-9156"],
            "standard": ["Python/FCTS-9156"],
            
            # Testing chapters
            "testing": ["Python/FCTS-9159", "Python/FCTS-9160", "Python/FCTS-9179", "Python/FCTS-9180"],
            "verification": ["Python/FCTS-9159", "Python/FCTS-9179"],
            "validation": ["Python/FCTS-9160", "Python/FCTS-9180"],
            "test": ["Python/FCTS-9159", "Python/FCTS-9160"]
        }
        
        # Try to match based on subchapter first (more specific)
        if subchapter_clean:
            for keyword, workitem_ids in heading_map.items():
                if keyword in subchapter_clean:
                    for wid in workitem_ids:
                        if wid in self.existing_workitems:
                            return wid
        
        # Then try chapter
        for keyword, workitem_ids in heading_map.items():
            if keyword in chapter_clean:
                for wid in workitem_ids:
                    if wid in self.existing_workitems:
                        return wid
        
        # Default fallback - use parent requirement
        return "Python/FCTS-9156"
    
    def create_workitem_format(self, requirement: Dict, parent_id: str, 
                               chapter: str, subchapter: Optional[str]) -> Dict:
        """Create a single work item in exact Polarion format"""
        
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
        
        # Build description for linking context
        link_description = f"Links to {subchapter if subchapter else chapter}"
        parent_title = self.existing_workitems.get(parent_id, {}).get('title', 'parent requirement')
        
        workitem = {
            "work_item": {
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
            },
            "links": [
                {
                    "target_id": parent_id,
                    "role": "has_parent",
                    "description": f"{link_description} - {parent_title}"
                }
            ],
            "children": []  # No children, each requirement is standalone
        }
        
        # Add additional links based on category
        category = requirement.get("category", "")
        
        if category == "Safety" and parent_id != "Python/FCTS-9155":
            workitem["links"].append({
                "target_id": "Python/FCTS-9155",
                "role": "relates_to",
                "description": "Related to MCP Safety Goal"
            })
        elif category == "Testing":
            # Add verification link
            test_items = ["Python/FCTS-9159", "Python/FCTS-9160", "Python/FCTS-9179", "Python/FCTS-9180"]
            for test_id in test_items:
                if test_id != parent_id and test_id in self.existing_workitems:
                    workitem["links"].append({
                        "target_id": test_id,
                        "role": "verifies",
                        "description": f"Verifies {self.existing_workitems[test_id]['title']}"
                    })
                    break
        
        return workitem
    
    def convert_requirements(self, brake_data: Dict) -> List[Dict]:
        """Convert all brake requirements to individual Polarion work items"""
        output_items = []
        
        # Extract all requirements with their context
        requirements_with_context = self.extract_requirements_with_context(brake_data)
        
        print(f"\n📋 Processing {len(requirements_with_context)} requirements...")
        
        # Process each requirement individually
        for req, chapter, subchapter in requirements_with_context:
            # Find matching work item for this requirement's context
            parent_id = self.match_heading_to_workitem(chapter, subchapter)
            
            # Create individual work item
            workitem = self.create_workitem_format(req, parent_id, chapter, subchapter)
            output_items.append(workitem)
            
            # Debug output
            context = f"{chapter} > {subchapter}" if subchapter else chapter
            print(f"   ✅ {req['id']}: {req['title'][:30]}... → {parent_id}")
        
        return output_items
    
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
        
        print("🔄 Converting requirements to individual Polarion work items...")
        output_items = self.convert_requirements(brake_data)
        
        # Create output structure - array of individual work items
        output = {
            "work_items": output_items,
            "metadata": {
                "total_items": len(output_items),
                "document_id": self.document_id,
                "conversion_timestamp": self.timestamp,
                "note": "Each requirement is an individual work item with parent links"
            }
        }
        
        # Save output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Output saved to: {output_path}")
        print(f"📊 Statistics:")
        print(f"   - Total work items: {len(output_items)}")
        
        # Count links by target
        link_targets = {}
        for item in output_items:
            for link in item.get("links", []):
                target = link["target_id"]
                link_targets[target] = link_targets.get(target, 0) + 1
        
        print(f"\n🔗 Link distribution:")
        for target, count in sorted(link_targets.items(), key=lambda x: x[1], reverse=True)[:5]:
            target_title = self.existing_workitems.get(target, {}).get('title', 'Unknown')
            print(f"   - {target}: {count} links ({target_title[:40]}...)")
        
        # Validate format
        self.validate_output_format(output_items)
    
    def validate_output_format(self, output_items: List[Dict]):
        """Validate that each output item matches exact format"""
        print("\n🔍 Validating output format...")
        
        if not output_items:
            print("   ❌ No work items generated")
            return
        
        # Check first item structure
        first_item = output_items[0]
        required_keys = ["work_item", "links", "children"]
        
        for key in required_keys:
            if key not in first_item:
                print(f"   ❌ Missing required key: {key}")
            else:
                print(f"   ✅ Has key: {key}")
        
        # Validate work_item structure
        if "work_item" in first_item and first_item["work_item"]:
            wi_keys = ["type", "title", "description", "status", "severity", "priority", "relationships"]
            for key in wi_keys:
                if key in first_item["work_item"]:
                    print(f"   ✅ Work item has: {key}")
                else:
                    print(f"   ⚠️  Work item missing: {key}")
        
        # Check that all items are individual (no children)
        items_with_children = sum(1 for item in output_items if item.get("children", []))
        if items_with_children == 0:
            print(f"   ✅ All items are individual (no children)")
        else:
            print(f"   ❌ {items_with_children} items have children (should be 0)")
        
        # Check that all items have parent links
        items_with_links = sum(1 for item in output_items if item.get("links", []))
        print(f"   ✅ {items_with_links}/{len(output_items)} items have parent links")
        
        print("\n✅ Format validation complete!")

def main():
    """Main entry point"""
    
    print("=" * 60)
    print("🚀 Brake Requirements to Individual Polarion Work Items")
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
    output_file = "Docs/Output/brake_requirements_polarion_individual.json"
    
    # Create converter and run
    converter = PolarionIndividualConverter()
    converter.document_id = doc_id
    converter.run(project_analysis, brake_requirements, output_file)

if __name__ == "__main__":
    main()