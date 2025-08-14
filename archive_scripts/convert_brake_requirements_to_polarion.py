#!/usr/bin/env python3
"""
Convert brake_system_requirements_structured.json to Polarion-compatible format
This script transforms the hierarchical document structure into work items with proper linking
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
    def __init__(self, input_file: str, output_file: str):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.work_items = []
        self.heading_counter = 1000
        self.document_id = "Python/_default/Functional Concept - Brake System"
        
    def load_structured_requirements(self) -> Dict:
        """Load the structured brake requirements JSON"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_heading_id(self) -> str:
        """Generate a unique heading ID"""
        self.heading_counter += 1
        return f"Python/BR-HEAD-{self.heading_counter}"
    
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
    
    def create_heading_workitem(self, heading: str, level: int, parent_id: Optional[str] = None) -> Dict:
        """Create a heading work item"""
        heading_id = self.generate_heading_id()
        
        workitem = {
            "id": heading_id,
            "type": "heading",
            "title": heading,
            "description": {
                "type": "text/html",
                "value": f"<h{level}>{heading}</h{level}>"
            },
            "status": "approved",
            "priority": "100.0",
            "relationships": {
                "module": {
                    "data": {
                        "type": "documents",
                        "id": self.document_id
                    }
                }
            }
        }
        
        if parent_id:
            workitem["links"] = [{
                "target_id": parent_id,
                "role": "has_parent",
                "description": f"Links to parent heading"
            }]
        
        return workitem
    
    def create_requirement_workitem(self, req: Dict, parent_heading_id: str, outline_number: str) -> Dict:
        """Create a requirement work item with proper linking"""
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
                    "description": "Links to chapter heading"
                }
            ]
        }
        
        return workitem
    
    def process_chapter(self, chapter: Dict, chapter_num: int, parent_id: Optional[str] = None) -> List[Dict]:
        """Process a chapter and its contents"""
        items = []
        
        # Create heading for the chapter
        chapter_heading_id = self.generate_heading_id()
        chapter_heading = {
            "id": chapter_heading_id,
            "type": "heading",
            "title": chapter["heading"],
            "description": {
                "type": "text/html",
                "value": f"<h2>{chapter['heading']}</h2><p>{chapter.get('description', '')}</p>"
            },
            "status": "approved",
            "priority": "100.0",
            "relationships": {
                "module": {
                    "data": {
                        "type": "documents",
                        "id": self.document_id
                    }
                }
            },
            "outlineNumber": str(chapter_num)
        }
        
        if parent_id:
            chapter_heading["links"] = [{
                "target_id": parent_id,
                "role": "has_parent",
                "description": "Links to document root"
            }]
        
        items.append(chapter_heading)
        
        # Process direct work items in chapter
        if "workitems" in chapter and chapter["workitems"]:
            for idx, workitem in enumerate(chapter["workitems"], 1):
                outline = f"{chapter_num}.{idx}"
                items.append(self.create_requirement_workitem(workitem, chapter_heading_id, outline))
        
        # Process subchapters
        if "subchapters" in chapter:
            for sub_idx, subchapter in enumerate(chapter["subchapters"], 1):
                items.extend(self.process_subchapter(
                    subchapter, 
                    chapter_num, 
                    sub_idx, 
                    chapter_heading_id
                ))
        
        return items
    
    def process_subchapter(self, subchapter: Dict, chapter_num: int, sub_num: int, 
                          parent_heading_id: str) -> List[Dict]:
        """Process a subchapter and its work items"""
        items = []
        
        # Create heading for the subchapter
        subchapter_heading_id = self.generate_heading_id()
        subchapter_heading = {
            "id": subchapter_heading_id,
            "type": "heading",
            "title": subchapter["heading"],
            "description": {
                "type": "text/html",
                "value": f"<h3>{subchapter['heading']}</h3>"
            },
            "status": "approved",
            "priority": "95.0",
            "relationships": {
                "module": {
                    "data": {
                        "type": "documents",
                        "id": self.document_id
                    }
                }
            },
            "outlineNumber": f"{chapter_num}.{sub_num}",
            "links": [{
                "target_id": parent_heading_id,
                "role": "has_parent",
                "description": "Links to parent chapter"
            }]
        }
        
        items.append(subchapter_heading)
        
        # Process work items in subchapter
        if "workitems" in subchapter:
            for idx, workitem in enumerate(subchapter["workitems"], 1):
                outline = f"{chapter_num}.{sub_num}.{idx}"
                items.append(self.create_requirement_workitem(workitem, subchapter_heading_id, outline))
        
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
            
            # Create root document heading
            root_heading_id = self.generate_heading_id()
            root_heading = {
                "id": root_heading_id,
                "type": "heading", 
                "title": document["title"],
                "description": {
                    "type": "text/html",
                    "value": f"<h1>{document['title']}</h1><p>Version: {document['version']}</p><p>Created: {document['created']}</p>"
                },
                "status": "approved",
                "priority": "100.0",
                "relationships": {
                    "module": {
                        "data": {
                            "type": "documents",
                            "id": self.document_id
                        }
                    }
                },
                "outlineNumber": "1"
            }
            
            self.work_items.append(root_heading)
            
            # Process all chapters
            for chapter_num, chapter in enumerate(document["chapters"], 1):
                self.work_items.extend(self.process_chapter(chapter, chapter_num + 1, root_heading_id))
            
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
                    "total_headings": len([w for w in self.work_items if w["type"] == "heading"]),
                    "conversion_timestamp": self.timestamp
                }
            }
        
            # Save output
            self.print_info(f"Saving output to: {self.output_file}")
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            self.print_success("Conversion completed successfully!")
            self.print_info(f"Output saved to: {self.output_file}")
            
            # Print statistics
            if TABULATE_AVAILABLE:
                stats_table = [
                    ["Total items", output['metadata']['total_items']],
                    ["Requirements", output['metadata']['total_requirements']],
                    ["Headings", output['metadata']['total_headings']]
                ]
                print("\n📊 Statistics:")
                print(tabulate(stats_table, headers=["Metric", "Count"], tablefmt="grid"))
            else:
                print("\n📊 Statistics:")
                print(f"   - Total items: {output['metadata']['total_items']}")
                print(f"   - Requirements: {output['metadata']['total_requirements']}")
                print(f"   - Headings: {output['metadata']['total_headings']}")
            
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
        description="Convert brake system requirements to Polarion format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s -i custom_input.json -o custom_output.json
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
        default="Docs/Output/brake_requirements_polarion.json",
        help="Output JSON file path (default: Docs/Output/brake_requirements_polarion.json)"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate input file without converting"
    )
    
    args = parser.parse_args()
    
    converter = BrakeRequirementsConverter(args.input, args.output)
    
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