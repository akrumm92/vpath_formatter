#!/usr/bin/env python3
"""
Convert brake_system_requirements_structured.json to Polarion format
with proper heading links using has_parent relationships.
Each requirement links to its chapter/subchapter heading via has_parent.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class PolarionHeadingConverter:
    def __init__(self, document_id: Optional[str] = None):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Allow overriding the document ID via CLI; keep a sensible default
        self.document_id = document_id or "Python/_default/Functional Concept - Template"
        self.work_items = []
        
    def load_brake_requirements(self, file_path: str) -> Dict:
        """Load the structured brake requirements with heading IDs"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_discovered_documents(self, file_path: str) -> Dict[str, str]:
        """Load discovered documents to get heading titles"""
        heading_map = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Extract heading information
        for doc in data.get("documents", []):
            if "structure" in doc and "headers" in doc["structure"]:
                for header in doc["structure"]["headers"]:
                    heading_id = header.get("id")
                    title = header.get("title", "")
                    outline = header.get("outlineNumber", "")
                    if outline:
                        heading_map[heading_id] = f"{outline} {title}"
                    else:
                        heading_map[heading_id] = title
                        
        return heading_map
    
    def create_workitem_format(self, requirement: Dict, parent_heading_id: str, 
                               parent_heading_title: str) -> Dict:
        """Create a work item in exact Polarion format with heading link"""
        
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
                    "target_id": parent_heading_id,
                    "role": "has_parent",
                    "description": f"Links to {parent_heading_title}"
                }
            ],
            "children": []  # Empty children array as per template
        }
        
        # Note: Do not add any hardcoded cross-links to fixed heading IDs.
        # The only required relationship is the has_parent link to the heading
        # provided by the structured input/discovered documents mapping.
        
        return workitem
    
    def process_requirements(self, brake_data: Dict, heading_map: Dict[str, str]) -> List[Dict]:
        """Process all requirements and create work items with proper heading links"""
        output_items = []
        document = brake_data.get("document", {})
        
        print(f"\n📋 Processing chapters and requirements...")
        
        # Process each chapter
        for chapter in document.get("chapters", []):
            chapter_heading = chapter.get("heading", "")
            chapter_heading_id = chapter.get("heading_id", "")
            chapter_outline = chapter.get("outlineNumber", "")
            
            # Get full chapter title from heading map
            chapter_title = heading_map.get(chapter_heading_id, chapter_heading)
            
            print(f"\n📂 Chapter: {chapter_title}")
            
            # Process direct chapter workitems (if any)
            if "workitems" in chapter and chapter["workitems"]:
                print(f"   Processing {len(chapter['workitems'])} direct requirements...")
                for req in chapter["workitems"]:
                    workitem = self.create_workitem_format(req, chapter_heading_id, chapter_title)
                    output_items.append(workitem)
                    print(f"      ✅ {req['id']}: {req['title'][:40]}... → {chapter_heading_id}")
            
            # Process subchapters
            for subchapter in chapter.get("subchapters", []):
                subchapter_heading = subchapter.get("heading", "")
                subchapter_heading_id = subchapter.get("heading_id", "")
                subchapter_outline = subchapter.get("outlineNumber", "")
                
                # Get full subchapter title from heading map
                subchapter_title = heading_map.get(subchapter_heading_id, subchapter_heading)
                
                print(f"   📁 Subchapter: {subchapter_title}")
                
                # Process subchapter workitems
                if "workitems" in subchapter and subchapter["workitems"]:
                    print(f"      Processing {len(subchapter['workitems'])} requirements...")
                    for req in subchapter["workitems"]:
                        # Link to the subchapter heading
                        workitem = self.create_workitem_format(req, subchapter_heading_id, subchapter_title)
                        output_items.append(workitem)
                        print(f"         ✅ {req['id']}: {req['title'][:35]}... → {subchapter_heading_id}")
        
        return output_items
    
    def run(self, brake_requirements_path: str, discovered_docs_path: str, output_path: str):
        """Main execution method"""
        print("=" * 60)
        print("🚀 Brake Requirements to Polarion with Heading Links")
        print("=" * 60)
        
        # Load discovered documents for heading titles
        print(f"\n📋 Loading discovered documents from: {discovered_docs_path}")
        heading_map = self.load_discovered_documents(discovered_docs_path)
        print(f"✅ Loaded {len(heading_map)} heading definitions")
        
        # Load brake requirements
        print(f"\n📋 Loading brake requirements from: {brake_requirements_path}")
        brake_data = self.load_brake_requirements(brake_requirements_path)
        
        # Process requirements
        print("\n🔄 Converting requirements with heading links...")
        output_items = self.process_requirements(brake_data, heading_map)
        
        # Create output structure
        output = {
            "work_items": output_items,
            "metadata": {
                "total_items": len(output_items),
                "document_id": self.document_id,
                "conversion_timestamp": self.timestamp,
                "note": "Each requirement links to its chapter/subchapter heading via has_parent"
            }
        }
        
        # Save output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Output saved to: {output_path}")
        print(f"\n📊 Statistics:")
        print(f"   - Total work items created: {len(output_items)}")
        
        # Count unique parent headings
        parent_headings = {}
        for item in output_items:
            for link in item.get("links", []):
                if link.get("role") == "has_parent":
                    target = link["target_id"]
                    parent_headings[target] = parent_headings.get(target, 0) + 1
        
        print(f"   - Unique parent headings used: {len(parent_headings)}")
        print(f"\n🔗 Heading link distribution:")
        for heading_id, count in sorted(parent_headings.items(), key=lambda x: x[1], reverse=True):
            heading_title = heading_map.get(heading_id, "Unknown")
            print(f"   - {heading_id}: {count} requirements ({heading_title})")
        
        # Validate output format
        self.validate_output_format(output_items)
    
    def validate_output_format(self, output_items: List[Dict]):
        """Validate that output matches exact format of workitem_with_links.json"""
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
            missing = []
            for key in wi_keys:
                if key not in first_item["work_item"]:
                    missing.append(key)
            
            if missing:
                print(f"   ⚠️  Work item missing keys: {', '.join(missing)}")
            else:
                print(f"   ✅ Work item has all required keys")
        
        # Check that all items have has_parent links
        items_with_parent = 0
        for item in output_items:
            has_parent = False
            for link in item.get("links", []):
                if link.get("role") == "has_parent":
                    has_parent = True
                    break
            if has_parent:
                items_with_parent += 1
        
        print(f"   ✅ {items_with_parent}/{len(output_items)} items have has_parent links")
        
        if items_with_parent == len(output_items):
            print("   ✅ All requirements properly linked to headings!")
        else:
            print(f"   ⚠️  {len(output_items) - items_with_parent} items missing parent links")
        
        print("\n✅ Format validation complete!")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert structured brake requirements to Polarion items linked to existing headings"
    )
    parser.add_argument(
        "-i",
        "--input",
        default="Docs/Input/brake_system_requirements_structured.json",
        help="Path to structured brake requirements JSON",
    )
    parser.add_argument(
        "-d",
        "--discovered",
        default="Docs/Input/discovered_documents.json",
        help="Path to discovered documents JSON (provides heading map)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="Docs/Output/brake_requirements_polarion_headings.json",
        help="Path to write Polarion-compatible output JSON",
    )
    parser.add_argument(
        "--document-id",
        default=None,
        help="Override Polarion document/module ID to associate items with",
    )

    args = parser.parse_args()

    brake_requirements = args.input
    discovered_docs = args.discovered
    output_file = args.output

    # Check if input files exist
    if not Path(brake_requirements).exists():
        print(f"❌ Input file not found: {brake_requirements}")
        sys.exit(1)

    if not Path(discovered_docs).exists():
        print(f"❌ Discovered documents file not found: {discovered_docs}")
        sys.exit(1)

    # Create output directory if needed
    output_dir = Path(output_file).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create converter and run
    converter = PolarionHeadingConverter(document_id=args.document_id)
    converter.run(brake_requirements, discovered_docs, output_file)

if __name__ == "__main__":
    main()
