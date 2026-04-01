#!/usr/bin/env python3
"""
vellum_doc_tool.py
Enhanced Product Documentation Tool for Otomeshon Platform

A zero-dependency CLI to create, update, and export Product Definition documents that are
both human-friendly (Markdown) and LLM-friendly (JSON). Enhanced with Otomeshon-specific
templates and integration capabilities.
"""

import re
import json
import argparse
import os
import sys
import datetime
from typing import Tuple, Dict, Any, List, Optional
from pathlib import Path

RE_FRONT_BLOCK = re.compile(r'(?s)^---\n(.*?)\n---\n(.*)')
RE_SECTION = re.compile(r'(?m)^#{1,6}\s+(.*)$')
RE_TABLE = re.compile(r'(?sm)^\|.*\|\s*$.*?(?=^\S|\Z)', re.MULTILINE)
RE_CODE_BLOCK = re.compile(r'```(\w+)?\s*\n(.*?)\n```', re.DOTALL)
RE_BULLET = re.compile(r'(?m)^\s*[-*+]\s+(.+)$')
RE_NUMBERED = re.compile(r'(?m)^\s*\d+\.\s+(.+)$')

MIN_REQUIRED_KEYS = [
    "product_name", "version", "status", "last_updated", "owner"
]

# Otomeshon-specific template sections
OTOMESHON_SECTIONS = [
    "1. Executive Summary",
    "2. Problem Statement", 
    "3. Goals and Non-Goals",
    "4. Personas",
    "5. User Journeys & Workflows",
    "6. Functional Requirements",
    "7. Non-Functional Requirements",
    "8. Data Model Overview",
    "9. Integration Points",
    "10. Security & Compliance",
    "11. Performance Requirements",
    "12. Open Questions",
    "13. Appendices"
]

def parse_front_matter(md_text: str) -> Tuple[Dict[str, Any], str]:
    """Parse front matter from markdown text."""
    m = RE_FRONT_BLOCK.match(md_text)
    if not m:
        return {}, md_text
    raw_front, rest = m.group(1), m.group(2)
    front = parse_mini_yaml(raw_front)
    return front, rest

def parse_mini_yaml(s: str) -> Dict[str, Any]:
    """Parse simplified YAML-like front matter."""
    data: Dict[str, Any] = {}
    current_key = None
    for line in s.splitlines():
        if not line.strip():
            continue
        if re.match(r'^\s*-\s+', line):
            if current_key is None:
                continue
            item = line.strip()[2:].strip()
            data.setdefault(current_key, [])
            data[current_key].append(_coerce(item))
            continue
        m = re.match(r'^(\w[\w_\-]*)\s*:\s*(.*)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            current_key = key
            if val == "":
                data[key] = []
            else:
                data[key] = _coerce(val)
    return data

def _coerce(val: str):
    """Coerce string values to appropriate types."""
    low = val.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "none"):
        return None
    try:
        if "." in val:
            return float(val)
        return int(val)
    except Exception:
        return val

def split_sections(md_body: str) -> Dict[str, str]:
    """Split markdown body into sections based on headers."""
    sections = {}
    headings = [(m.group(1).strip(), m.start()) for m in RE_SECTION.finditer(md_body)]
    if not headings:
        return {"__body__": md_body.strip()}
    for i, (title, start) in enumerate(headings):
        end = headings[i+1][1] if i+1 < len(headings) else len(md_body)
        section_md = md_body[start:end].strip()
        sections[title] = section_md
    return sections

def parse_tables(section_md: str) -> List[Dict[str, Any]]:
    """Parse markdown tables in a section."""
    out = []
    for block in RE_TABLE.finditer(section_md):
        table_md = block.group(0).strip()
        lines = [ln.strip() for ln in table_md.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        header = [c.strip() for c in lines[0].strip("|").split("|")]
        rows = []
        for ln in lines[2:]:
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if len(cells) != len(header):
                continue
            rows.append(dict(zip(header, cells)))
        out.append({"header": header, "rows": rows, "raw": table_md})
    return out

def extract_bullets(section_md: str) -> Dict[str, List[str]]:
    """Extract bullet points and numbered lists from a section."""
    bullets = RE_BULLET.findall(section_md)
    nums = RE_NUMBERED.findall(section_md)
    return {"bullets": [b.strip() for b in bullets], "numbered": [n.strip() for n in nums]}

def extract_code_blocks(section_md: str) -> List[Dict[str, str]]:
    """Extract code blocks from a section."""
    blocks = []
    for m in RE_CODE_BLOCK.finditer(section_md):
        lang = (m.group(1) or "").strip().lower()
        code = m.group(2)
        blocks.append({"language": lang, "code": code})
    return blocks

def md_to_json(md_path: str) -> Dict[str, Any]:
    """Convert markdown file to structured JSON."""
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()
    front, body = parse_front_matter(md)
    sections = split_sections(body)
    j = {
        "source_path": md_path,
        "front_matter": front,
        "sections": {},
        "extracted_on": datetime.datetime.utcnow().isoformat() + "Z",
        "format_version": "1.0",
        "platform": "otomeshon",
    }
    for title, content in sections.items():
        j["sections"][title] = {
            "raw_markdown": content,
            "tables": parse_tables(content),
            "lists": extract_bullets(content),
            "code_blocks": extract_code_blocks(content),
        }
    return j

def create_otomeshon_template(product_name: str = "Otomeshon Feature", owner: str = "Development Team") -> str:
    """Create an Otomeshon-specific product definition template."""
    today = datetime.date.today().isoformat()
    
    template = f"""---
product_name: {product_name}
version: 0.1.0
status: Draft
last_updated: {today}
owner: {owner}
stakeholders: 
  - Product Management
  - Engineering Team
  - Business Operations
  - Compliance Team
target_users: 
  - Operations Analysts
  - Risk Managers
  - Compliance Officers
  - System Administrators
use_cases: 
  - Post-trade processing automation
  - Data analysis and reporting
  - Workflow orchestration
  - Real-time monitoring
primary_tech: 
  - FastAPI (Python 3.12)
  - React 18 + TypeScript
  - PostgreSQL + Neo4j
  - LangChain + AI workflows
  - Docker + Kubernetes
sla_requirements: 99.9% uptime, <3s response time
data_residency: On-premises / Azure
regulatory_considerations: 
  - SOX compliance
  - GDPR considerations
  - Banking regulations
  - Data privacy requirements
---

# Product Definition Document: {product_name}

## 1. Executive Summary
(Plain-language overview of the feature, 3–5 sentences. Focus on business value and technical approach.)

## 2. Problem Statement
1. 
2. 
3. 

## 3. Goals and Non-Goals
**Goals**
1. 
2. 
3. 

**Non-Goals**
- 
- 
- 

## 4. Personas
| Persona | Role | Needs | Pain Points |
|---------|------|-------|-------------|
| Operations Analyst | Daily operations | Real-time data access, automated workflows | Manual data entry, slow reporting |
| Risk Manager | Risk oversight | Risk metrics, alerts, compliance reporting | Delayed risk identification |
| Compliance Officer | Regulatory compliance | Audit trails, compliance checks | Manual compliance verification |
| System Administrator | Platform management | Monitoring, scaling, maintenance | Complex deployment, troubleshooting |

## 5. User Journeys & Workflows
**Journey 1 – Data Analysis Workflow**
1. User accesses Data Sandbox
2. Selects data source and applies filters
3. **DECISION:** Choose visualization or export format
4. Generate reports or export data

**Journey 2 – Workflow Automation**
1. User defines workflow parameters
2. System executes AI-powered workflow
3. **DECISION:** Review results or trigger next step
4. Store results in Data Sandbox

## 6. Functional Requirements
```yaml
FR-001: 
FR-002: 
FR-003: 
```

## 7. Non-Functional Requirements
```yaml
NFR-001: Response time < 3 seconds for core operations
NFR-002: Support for 1000+ concurrent users
NFR-003: 99.9% uptime SLA
NFR-004: Real-time data updates via WebSocket
```

## 8. Data Model Overview
| Entity | Attributes | Relationships |
|--------|------------|---------------|
| User | id, username, email, role | owns Workflows, accesses DataSandbox |
| Workflow | id, name, status, parameters | executed_by User, produces DataRecord |
| DataRecord | id, content, metadata, source | belongs_to DataSource, analyzed_by Agent |
| Agent | id, type, capabilities, status | monitors DataStream, executes Workflow |

## 9. Integration Points
- **Data Sources**: MCP servers, external APIs, file uploads
- **AI Services**: OpenAI, Anthropic, local LLM models
- **Databases**: PostgreSQL, Neo4j, Redis
- **Monitoring**: Prometheus, Grafana, Azure Monitor
- **Security**: Keycloak, Azure Key Vault

## 10. Security & Compliance
- **Authentication**: OAuth2 + JWT tokens
- **Authorization**: Role-based access control (RBAC)
- **Data Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Audit Logging**: Comprehensive activity logging
- **Compliance**: SOX, GDPR, banking regulations

## 11. Performance Requirements
- **Response Time**: < 3s for 95th percentile
- **Throughput**: 1000+ concurrent users
- **Scalability**: Auto-scaling based on demand
- **Availability**: 99.9% uptime target
- **Data Processing**: Handle 1M+ records per day

## 12. Open Questions
- 
- 

## 13. Appendices
- Glossary of Terms
- References and Links
- Related Documents
- API Specifications
- Database Schema
- Deployment Architecture
"""
    return template

def cmd_init(args):
    """Create a new markdown document from template."""
    if args.otomeshon:
        template = create_otomeshon_template(args.product_name, args.owner)
    else:
        template = create_otomeshon_template()
    
    with open(args.path, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"Created Otomeshon template: {args.path}")

def cmd_export_json(args):
    """Export markdown to JSON."""
    j = md_to_json(args.path)
    out = args.output or (os.path.splitext(args.path)[0] + ".json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=2)
    print(f"Wrote JSON: {out}")

def cmd_validate(args):
    """Validate required front matter keys."""
    with open(args.path, "r", encoding="utf-8") as f:
        md = f.read()
    front, _ = parse_front_matter(md)
    missing = [k for k in MIN_REQUIRED_KEYS if k not in front or not str(front[k]).strip()]
    if missing:
        print("Missing required front matter keys:", ", ".join(missing))
        sys.exit(1)
    print("Validation OK.")

def cmd_sync(args):
    """Sync markdown and JSON files."""
    md_path = args.path
    json_path = os.path.splitext(md_path)[0] + ".json"
    
    # Export markdown to JSON
    j = md_to_json(md_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=2)
    
    print(f"Synced: {md_path} -> {json_path}")

def cmd_list_sections(args):
    """List all sections in a markdown file."""
    with open(args.path, "r", encoding="utf-8") as f:
        md = f.read()
    _, body = parse_front_matter(md)
    sections = split_sections(body)
    
    print(f"Sections in {args.path}:")
    for title in sections.keys():
        if title != "__body__":
            print(f"  - {title}")

def build_parser():
    """Build command line argument parser."""
    p = argparse.ArgumentParser(
        description="Enhanced Product Documentation Tool for Otomeshon Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create new Otomeshon product doc
  python vellum_doc_tool.py init --otomeshon product-definition.md
  
  # Export to JSON for LLM ingestion
  python vellum_doc_tool.py export-json product-definition.md
  
  # Sync markdown and JSON
  python vellum_doc_tool.py sync product-definition.md
  
  # List all sections
  python vellum_doc_tool.py list-sections product-definition.md
        """
    )
    
    sub = p.add_subparsers(dest="cmd", required=True)

    # Init command
    sp = sub.add_parser("init", help="Create a new markdown document from template")
    sp.add_argument("path", help="Path to create the markdown file")
    sp.add_argument("--otomeshon", action="store_true", help="Use Otomeshon-specific template")
    sp.add_argument("--product-name", default="Otomeshon Feature", help="Product name for template")
    sp.add_argument("--owner", default="Development Team", help="Owner for template")
    sp.set_defaults(func=cmd_init)

    # Export JSON command
    sp = sub.add_parser("export-json", help="Export markdown to JSON")
    sp.add_argument("path", help="Path to markdown file")
    sp.add_argument("-o", "--output", help="Output JSON file path")
    sp.set_defaults(func=cmd_export_json)

    # Validate command
    sp = sub.add_parser("validate", help="Validate required front matter keys")
    sp.add_argument("path", help="Path to markdown file")
    sp.set_defaults(func=cmd_validate)

    # Sync command
    sp = sub.add_parser("sync", help="Sync markdown and JSON files")
    sp.add_argument("path", help="Path to markdown file")
    sp.set_defaults(func=cmd_sync)

    # List sections command
    sp = sub.add_parser("list-sections", help="List all sections in markdown file")
    sp.add_argument("path", help="Path to markdown file")
    sp.set_defaults(func=cmd_list_sections)

    return p

def main(argv=None):
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()

