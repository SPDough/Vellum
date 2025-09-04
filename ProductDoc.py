# 1) Create a new doc from template
python vellum_doc_tool.py init product-definition-otomeshon-vellum.md

# 2) Set front-matter values
python vellum_doc_tool.py set product-definition-otomeshon-vellum.md product_name "Otomeshon Vellum"
python vellum_doc_tool.py set product-definition-otomeshon-vellum.md owner "Your Name"
python vellum_doc_tool.py set product-definition-otomeshon-vellum.md version "0.1"

# 3) Append structured items
python vellum_doc_tool.py add-requirement product-definition-otomeshon-vellum.md FR-001 "Ingest custodian APIs"
python vellum_doc_tool.py add-nfr         product-definition-otomeshon-vellum.md NFR-001 "p95 < 3s for core queries"
python vellum_doc_tool.py add-persona     product-definition-otomeshon-vellum.md "Asset Owner Ops" "Ops Analyst" "Real-time reconciliation" "Manual matching delays"

# 4) Validate required front matter
python vellum_doc_tool.py validate product-definition-otomeshon-vellum.md

# 5) Export JSON for LLM ingestion (keeps raw markdown + extracted tables/lists/code blocks)
python vellum_doc_tool.py export-json product-definition-otomeshon-vellum.md -o product-definition-otomeshon-vellum.json

# or just write JSON next to the MD with same basename
python vellum_doc_tool.py sync product-definition-otomeshon-vellum.md
