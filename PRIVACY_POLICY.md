# Privacy Policy

**Last updated: December 31, 2024**

## ActProof.ai EU AI Act Compliance Scanner - Privacy Policy

### 1. Introduction

ActProof.ai ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard information when you use our GitHub Action for EU AI Act compliance scanning.

### 2. Information We Collect

#### 2.1 Repository Information
When you use our GitHub Action, we may process:
- **Repository metadata**: Repository name, owner, branch, and commit SHA
- **Source code**: Code files are analyzed locally within GitHub Actions runners
- **AI/ML components**: Information about detected AI models, datasets, and dependencies


#### 2.2 What We Do NOT Collect
- We do **NOT** store your source code permanently
- We do **NOT** collect personal information beyond what GitHub provides
- We do **NOT** share your repository contents with third parties

### 3. How We Use Information
We use the collected information solely to:
- Perform EU AI Act compliance analysis
- Generate compliance reports
- Provide recommendations for improving compliance
- Display results on the ActProof.ai dashboard (if API mode is used)

### 4. Data Processing

#### 4.1 Local Mode (Default)
When using `scan_mode: local`:
- All processing occurs within the GitHub Actions runner
- No data is sent to external servers
- Reports are generated and stored as GitHub artifacts

#### 4.2 API Mode
When using `scan_mode: api`:
- Repository URL is sent to our API server
- Our server clones and analyzes the repository
- Results are stored for dashboard access
- Data is retained for 90 days unless you request deletion

### 5. Data Security

We implement appropriate security measures including:
- HTTPS encryption for all API communications
- Secure token-based authentication
- Regular security audits
- Data encryption at rest

### 6. Third-Party Services

Our service may integrate with:
- **GitHub**: For repository access and workflow execution
- **Supabase**: For user authentication and data storage (API mode only)

### 7. Your Rights

You have the right to:
- Access your compliance scan data
- Request deletion of your data
- Opt out of API mode by using local scanning
- Contact us with privacy concerns

### 8. Data Retention

- **Local mode**: No data retained by ActProof.ai
- **API mode**: Scan results retained for 90 days
- **User accounts**: Data retained until account deletion

### 9. Children's Privacy

Our service is not intended for users under 16 years of age.

### 10. Changes to This Policy

We may update this Privacy Policy periodically. Changes will be posted to this page with an updated revision date.

### 11. Contact Us

For privacy-related inquiries:

- **Email**: privacy@actproof.ai
- **Website**: https://app.actproof.ai
- **GitHub Issues**: https://github.com/Edoardoba/actproof-action/issues

### 12. EU Data Protection

For users in the European Union, we comply with GDPR requirements. Our legal basis for processing is:
- **Legitimate interest**: To provide EU AI Act compliance services
- **Contract**: When you use our service, you agree to our terms

---

© 2024-2025 ActProof.ai. All rights reserved.

