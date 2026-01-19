# ⚙️ BEACON Technical Configuration Guide

This document consolidates all technical setup, configuration, and troubleshooting information.

## System Requirements

### Hardware Requirements
- **CPU**: 4+ cores (8+ recommended for Ollama)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 50GB+ free space
- **Network**: Stable internet for API calls

### Software Requirements
- **Python**: 3.12+
- **Node.js**: 18+
- **PostgreSQL**: 14+ with pgvector extension
- **Git**: Latest version

## Environment Configuration

### Core Environment Variables (.env)
```env
# Database Configuration
DATABASE_HOSTNAME=aws-1-ap-south-1.pooler.supabase.com
DATABASE_