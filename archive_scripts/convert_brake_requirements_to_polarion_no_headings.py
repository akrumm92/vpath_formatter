#!/usr/bin/env python3
"""
Convert brake_system_requirements_structured.json to Polarion-compatible format
This script transforms the hierarchical document structure into work items that link to existing headings
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    
try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    
try:
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

class BrakeRequirementsConverter:
    def __init__(self, input_file: str, output_file: str, heading_map_file: Optional[str] = None):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.heading_map_file = Path(heading_map_file) if heading_map_file else None
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.work_items = []
        self.document_id = "Python/_default/Functional Concept - Brake System"
        
        # Default heading IDs - these should map to existing headings in Polarion
        self.heading_ids = {
            "root": "Python/FCTS-ROOT",  # Root document heading
            "1. Introduction and Scope": "Python/FCTS-INTRO",
            "2. System Overview and Architecture": "Python/FCTS-ARCH",
            "3. Functional Requirements": "Python/FCTS-FUNC",
            "3.1 Primary Brake Functions": "Python/FCTS-FUNC-PRIM",
            "3.2 Advanced Brake Functions": "Python/FCTS-FUNC-ADV",
            "4. Performance Requirements": "Python/FCTS-PERF",
            "4.1 Stopping Performance": "Python/FCTS-PERF-STOP",
            "4.2 Response Time Performance": "Python/FCTS-PERF-RESP",
            "4.3 Durability Performance": "Python/FCTS-PERF-DUR",
            "5. Safety Requirements": "Python/FCTS-SAFE",
            "5.1 System Redundancy": "Python/FCTS-SAFE-RED",
            "5.2 Monitoring and Warnings": "Python/FCTS-SAFE-MON",
            "6. Interface Requirements": "Python/FCTS-INTF",
            "6.1 System Communication": "Python/FCTS-INTF-COMM",
            "6.2 Control System Integration": "Python/FCTS-INTF-CTRL",
            "6.3 Sensor Integration": "Python/FCTS-INTF-SENS",
            "7. Environmental Requirements": "Python/FCTS-ENV",
            "7.1 Temperature and Climate": "Python/FCTS-ENV-TEMP",
            "7.2 Corrosion and Protection": "Python/FCTS-ENV-CORR",
            "7.3 Mechanical Stress": "Python/FCTS-ENV-MECH",
            "8. Maintenance and Serviceability": "Python/FCTS-MAINT",
            "8.1 Wear Monitoring": "Python/FCTS-MAINT-WEAR",
            "8.2 Service Intervals": "Python/FCTS-MAINT-SERV",
            "8.3 Diagnostics and Accessibility": "Python/FCTS-MAINT-DIAG",
            "9. Regulatory Compliance": "Python/FCTS-REG",
            "9.1 International Standards": "Python/FCTS-REG-INT",
            "9.2 Safety Standards": "Python/FCTS-REG-SAFE",
            "9.3 Environmental Standards": "Python/FCTS-REG-ENV",
            "10. Verification and Validation": "Python/FCTS-TEST",
            "10.1 Performance Testing": "Python/FCTS-TEST-PERF",
            "10.2 Durability Testing": "Python/FCTS-TEST-DUR",
            "10.3 Environmental Testing": "Python/FCTS-TEST-ENV",
            "10.4 System Testing": "Python/FCTS-TEST-SYS"
        }
        
        # Load custom heading map if provided
        if self.heading_map_file and self.heading_map_file.exists():
            self.load_heading_map()
    
    def load_heading_map(self):
        """Load custom heading ID mappings from file"""
        try:
            with open(self.heading_map_file, 'r', encoding='utf-8') as f:
                custom_map = json.load(f)
                self.heading_ids.update(custom_map)
                self.print_info(f"Loaded custom heading mappings from {self.heading_map_file}")
        except Exception as e:
            self.print_error(f"Failed to load heading map: {e}")
    
    def load_structured_requirements(self) -> Dict:
        """Load the structured brake requirements JSON"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_heading_id(self, heading_title: str) -> str:
        """Get the heading ID for a given heading title"""
        # First try exact match
        if heading_title in self.heading_ids:
            return self.heading_ids[heading_title]
        
        # Try without numbering (e.g., "3. Functional Requirements" -> "Functional Requirements")
        import re
        cleaned_title = re.sub(r'^\d+\.?\d*\s+', '', heading_title)
        for key, value in self.heading_ids.items():
            if cleaned_title in key:
                return value
        
        # Default fallback - generate a warning
        self.print_warning(f"No heading ID found for '{heading_title}', using default")
        return "Python/FCTS-UNKNOWN"
    
    def map_priority(self, priority: str) -> str:
        """Map priority strings to Polarion priority values"""
        priority_map = {
            "Critical": "100.0",
            "High": "90.0",
            "Medium": "50.0",
            "Low": "30.0"
        }
        return priority_map.get(priority, "50.0")
    
    def map_severity(self, category: str, priority: str) -> str:
        """Map category and priority to severity"""
        if category == "Safety" and priority == "Critical":
            return "safety_critical"
        elif priority == "Critical":
            return "must_have"
        elif priority == "High":
            return "should_have"
        elif priority == "Medium":
            return "could_have"
        else:
            return "nice_to_have"
    
    def map_status(self, category: str) -> str:
        """Map category to appropriate status"""
        status_map = {
            "Regulatory": "approved",
            "Safety": "in_review",
            "Functional": "draft",
            "Performance": "draft",
            "Interface": "draft",
            "Environmental": "draft",
            "Maintenance": "draft",
            "Testing": "draft"
        }
        return status_map.get(category, "draft")
    
    def create_requirement_workitem(self, req: Dict, parent_heading_title: str, outline_number: str) -> Dict:
        """Create a requirement work item with proper linking to existing headings"""
        parent_heading_id = self.get_heading_id(parent_heading_title)
        
        workitem = {
            "id": f"Python/{req['id']}",
            "type": "requirement",
            "title": req["title"],
            "description": {
                "type": "text/html",
                "value": f"<p>{req['description']}</p>"
            },
            "status": self.map_status(req["category"]),
            "severity": self.map_severity(req["category"], req["priority"]),
            "priority": self.map_priority(req["priority"]),
            "categories": [req["category"].lower()],
            "custom_fields": {
                "requirement_id": req["id"],
                "category": req["category"],
                "original_priority": req["priority"]
            },
            "relationships": {
                "module": {
                    "data": {
                        "type": "documents",
                        "id": self.document_id
                    }
                }
            },
            "outlineNumber": outline_number,
            "links": [
                {
                    "target_id": parent_heading_id,
                    "role": "has_parent",
                    "description": f"Links to {parent_heading_title}"
                }
            ]
        }
        
        return workitem
    
    def process_chapter(self, chapter: Dict, chapter_num: int) -> List[Dict]:
        """Process a chapter and extract only work items (no headings)"""
        items = []
        chapter_title = chapter["heading"]
        
        # Process direct work items in chapter
        if "workitems" in chapter and chapter["workitems"]:
            for idx, workitem in enumerate(chapter["workitems"], 1):
                outline = f"{chapter_num}.{idx}"
                items.append(self.create_requirement_workitem(workitem, chapter_title, outline))
        
        # Process subchapters
        if "subchapters" in chapter:
            for sub_idx, subchapter in enumerate(chapter["subchapters"], 1):
                items.extend(self.process_subchapter(
                    subchapter, 
                    chapter_num, 
                    sub_idx
                ))
        
        return items
    
    def process_subchapter(self, subchapter: Dict, chapter_num: int, sub_num: int) -> List[Dict]:
        """Process a subchapter and extract only work items"""
        items = []
        subchapter_title = subchapter["heading"]
        
        # Process work items in subchapter
        if "workitems" in subchapter:
            for idx, workitem in enumerate(subchapter["workitems"], 1):
                outline = f"{chapter_num}.{sub_num}.{idx}"
                items.append(self.create_requirement_workitem(workitem, subchapter_title, outline))
        
        return items
    
    def print_success(self, message: str):
        """Print success message with color if available"""
        if COLORS_AVAILABLE:
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        else:
            print(f"✅ {message}")
    
    def print_info(self, message: str):
        """Print info message with color if available"""
        if COLORS_AVAILABLE:
            print(f"{Fore.CYAN}ℹ️  {message}{Style.RESET_ALL}")
        else:
            print(f"ℹ️  {message}")
    
    def print_error(self, message: str):
        """Print error message with color if available"""
        if COLORS_AVAILABLE:
            print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
        else:
            print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """Print warning message with color if available"""
        if COLORS_AVAILABLE:
            print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
        else:
            print(f"⚠️  {message}")
    
    def validate_input(self, data: Dict) -> bool:
        """Validate input data structure"""
        if "document" not in data:
            self.print_error("Missing 'document' key in input JSON")
            return False
        
        doc = data["document"]
        required_keys = ["id", "title", "project", "space", "chapters"]
        for key in required_keys:
            if key not in doc:
                self.print_error(f"Missing required key '{key}' in document")
                return False
        
        if not isinstance(doc["chapters"], list):
            self.print_error("'chapters' must be a list")
            return False
        
        return True
    
    def save_heading_map(self):
        """Save the current heading map to a file for reference"""
        map_file = self.output_file.parent / "heading_map.json"
        with open(map_file, 'w', encoding='utf-8') as f:
            json.dump(self.heading_ids, f, indent=2, ensure_ascii=False)
        self.print_info(f"Heading map saved to {map_file}")
    
    def convert(self):
        """Main conversion method"""
        try:
            # Check if input file exists
            if not self.input_file.exists():
                self.print_error(f"Input file not found: {self.input_file}")
                sys.exit(1)
            
            # Load input data
            self.print_info(f"Loading input file: {self.input_file}")
            data = self.load_structured_requirements()
            
            # Validate input
            if not self.validate_input(data):
                sys.exit(1)
            
            document = data["document"]
            
            # Process all chapters (only extracting work items, no headings)
            for chapter_num, chapter in enumerate(document["chapters"], 1):
                self.work_items.extend(self.process_chapter(chapter, chapter_num))
            
            # Create output structure
            output = {
                "document": {
                    "id": self.document_id,
                    "title": document["title"],
                    "type": "Functional Concept",
                    "project": document["project"],
                    "space": document["space"],
                    "version": document["version"],
                    "created": self.timestamp
                },
                "work_items": self.work_items,
                "metadata": {
                    "total_items": len(self.work_items),
                    "total_requirements": len([w for w in self.work_items if w["type"] == "requirement"]),
                    "conversion_timestamp": self.timestamp,
                    "note": "Work items only - headings must exist in Polarion document"
                }
            }
            
            # Save output
            self.print_info(f"Saving output to: {self.output_file}")
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            # Save heading map for reference
            self.save_heading_map()
            
            self.print_success("Conversion completed successfully!")
            self.print_info(f"Output saved to: {self.output_file}")
            
            # Print statistics
            if TABULATE_AVAILABLE:
                stats_table = [
                    ["Total work items", output['metadata']['total_items']],
                    ["Requirements", output['metadata']['total_requirements']]
                ]
                print("\n📊 Statistics:")
                print(tabulate(stats_table, headers=["Metric", "Count"], tablefmt="grid"))
            else:
                print("\n📊 Statistics:")
                print(f"   - Total work items: {output['metadata']['total_items']}")
                print(f"   - Requirements: {output['metadata']['total_requirements']}")
            
            # Print category breakdown
            categories = {}
            for item in self.work_items:
                if item["type"] == "requirement":
                    cat = item["custom_fields"]["category"]
                    categories[cat] = categories.get(cat, 0) + 1
            
            if categories:
                print("\n📂 Requirements by Category:")
                if TABULATE_AVAILABLE:
                    cat_table = [[cat, count] for cat, count in sorted(categories.items())]
                    print(tabulate(cat_table, headers=["Category", "Count"], tablefmt="grid"))
                else:
                    for cat, count in sorted(categories.items()):
                        print(f"   - {cat}: {count}")
            
            # Print heading references used
            heading_refs = {}
            for item in self.work_items:
                if "links" in item:
                    for link in item["links"]:
                        if link["role"] == "has_parent":
                            heading_id = link["target_id"]
                            heading_refs[heading_id] = heading_refs.get(heading_id, 0) + 1
            
            print("\n🔗 Referenced Heading IDs:")
            if TABULATE_AVAILABLE:
                ref_table = [[hid, count] for hid, count in sorted(heading_refs.items())]
                print(tabulate(ref_table, headers=["Heading ID", "References"], tablefmt="grid"))
            else:
                for hid, count in sorted(heading_refs.items()):
                    print(f"   - {hid}: {count} references")
                        
        except FileNotFoundError as e:
            self.print_error(f"File not found: {e}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.print_error(f"Invalid JSON in input file: {e}")
            sys.exit(1)
        except Exception as e:
            self.print_error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert brake system requirements to Polarion format (work items only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This version creates only work items that link to existing headings in Polarion.
No heading work items are created - they must already exist in the document.

Examples:
  %(prog)s
  %(prog)s -i custom_input.json -o custom_output.json
  %(prog)s --heading-map heading_ids.json
  %(prog)s --validate-only
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        default="Docs/Input/brake_system_requirements_structured.json",
        help="Input JSON file path (default: Docs/Input/brake_system_requirements_structured.json)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="Docs/Output/brake_requirements_polarion_workitems.json",
        help="Output JSON file path (default: Docs/Output/brake_requirements_polarion_workitems.json)"
    )
    
    parser.add_argument(
        "--heading-map",
        help="JSON file with custom heading ID mappings"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate input file without converting"
    )
    
    args = parser.parse_args()
    
    converter = BrakeRequirementsConverter(args.input, args.output, args.heading_map)
    
    if args.validate_only:
        try:
            data = converter.load_structured_requirements()
            if converter.validate_input(data):
                converter.print_success("Input file is valid!")
            else:
                converter.print_error("Input file validation failed!")
                sys.exit(1)
        except Exception as e:
            converter.print_error(f"Error loading file: {e}")
            sys.exit(1)
    else:
        converter.convert()

if __name__ == "__main__":
    main()