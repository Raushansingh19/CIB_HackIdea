#!/bin/bash
# Quick script to run the ingestion pipeline
# Usage: ./run_ingest.sh

cd "$(dirname "$0")"
python -m rag.ingest

