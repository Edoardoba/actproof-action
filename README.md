# 🛡️ ActProof.ai - EU AI Act Compliance Scanner

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-ActProof.ai-blue?logo=github)](https://github.com/marketplace/actions/actproof-ai-eu-ai-act-compliance-scanner)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![EU AI Act](https://img.shields.io/badge/EU%20AI%20Act-Compliant-success)](https://artificialintelligenceact.eu/)

**Automated EU AI Act compliance scanning for AI/ML repositories**

ActProof.ai automatically scans your repository for AI/ML components, generates an AI Bill of Materials (AI-BOM), and evaluates compliance with EU AI Act requirements.

## 🚀 Quick Start

Add this to your workflow (`.github/workflows/compliance.yml`):

```yaml
name: EU AI Act Compliance

on: [push, pull_request]

jobs:
  compliance-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run ActProof.ai Compliance Scan
        uses: Edoardoba/actproof-action@v1
        id: scan
        
      - name: Display Results
        run: |
          echo "Compliance Score: ${{ steps.scan.outputs.compliance_score }}%"
          echo "Status: ${{ steps.scan.outputs.compliant }}"
          echo "Risk Level: ${{ steps.scan.outputs.risk_level }}"
```

**That's it!** 🎉 The action works out of the box with sensible defaults.

## ✨ Features

- 🔍 **AI/ML Detection**: Automatically detects AI models, datasets, and ML dependencies
- 📋 **AI-BOM Generation**: Creates SPDX-compliant AI Bill of Materials
- ⚖️ **Compliance Evaluation**: Evaluates against EU AI Act requirements
- 📊 **Risk Assessment**: Classifies systems per Annex III risk categories
- 📝 **Detailed Reports**: Generates JSON and HTML compliance reports
- 🔒 **Privacy First**: Local scan mode keeps your code on GitHub runners

## 📥 Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `scan_mode` | `local` (default) or `api` | `local` |
| `fail_on_non_compliant` | Fail workflow if non-compliant | `false` |
| `compliance_threshold` | Minimum score (0-100) to pass | `80` |
| `upload_artifacts` | Upload reports as artifacts | `true` |
| `create_issue` | Create issue on compliance gaps | `false` |
| `output_format` | Report format: `json`, `html`, `both` | `both` |

## 📤 Outputs

| Output | Description |
|--------|-------------|
| `compliance_score` | Overall compliance score (0-100) |
| `compliant` | Whether system is compliant (`true`/`false`) |
| `risk_level` | Risk level: `MINIMAL`, `LIMITED`, `HIGH`, `UNACCEPTABLE` |
| `critical_gaps_count` | Number of critical compliance gaps |
| `report_path` | Path to generated compliance report |

## 🔧 Advanced Usage

### Fail on Non-Compliance

```yaml
- uses: Edoardoba/actproof-action@v1
  with:
    fail_on_non_compliant: 'true'
    compliance_threshold: '90'
```

### Create Issue on Compliance Gaps

```yaml
- uses: Edoardoba/actproof-action@v1
  with:
    create_issue: 'true'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Use API Mode (for dashboard)

```yaml
- uses: Edoardoba/actproof-action@v1
  with:
    scan_mode: 'api'
    api_key: ${{ secrets.ACTPROOF_API_KEY }}
```

## 📊 What Gets Analyzed

ActProof.ai scans for:

- **AI Models**: TensorFlow, PyTorch, Scikit-learn, Hugging Face, OpenAI, etc.
- **Datasets**: Training data, validation sets, data pipelines
- **Dependencies**: ML libraries, frameworks, pre-trained models
- **Documentation**: Model cards, data sheets, risk assessments
- **Compliance Artifacts**: Technical documentation, logging mechanisms

## ⚖️ EU AI Act Coverage

The scanner evaluates compliance with key EU AI Act requirements:

| Article | Description | Coverage |
|---------|-------------|----------|
| Article 9 | Risk Management System | ✅ |
| Article 10 | Data Governance | ✅ |
| Article 11 | Technical Documentation | ✅ |
| Article 12 | Record-keeping & Logging | ✅ |
| Article 13 | Transparency | ✅ |
| Article 14 | Human Oversight | ✅ |
| Article 15 | Accuracy, Robustness, Cybersecurity | ✅ |
| Annex III | High-Risk Classification | ✅ |
| GPAI | General Purpose AI Requirements | ✅ |

## 💰 Pricing

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/month | Local scanning, basic reports, community support |
| **Pro** | Coming soon | API mode, dashboard, priority support |
| **Enterprise** | Contact us | Custom policies, SSO, dedicated support |

## 🔒 Privacy & Security

- **Local Mode**: All processing happens on GitHub runners - your code never leaves GitHub
- **API Mode**: Code is temporarily processed and immediately deleted
- **No Storage**: We don't permanently store your source code
- **Encryption**: All API communications use HTTPS

Read our full [Privacy Policy](PRIVACY_POLICY.md).

## 📞 Support

- **📧 Email**: support@actproof.ai
- **🐛 Issues**: [GitHub Issues](https://github.com/Edoardoba/actproof-action/issues)
- **📚 Docs**: [Documentation](https://app.actproof.ai/docs)
- **💬 Discussions**: [GitHub Discussions](https://github.com/Edoardoba/actproof-action/discussions)

For security vulnerabilities, please email security@actproof.ai.

## 📜 Legal

- [Terms of Service](TERMS_OF_SERVICE.md)
- [Privacy Policy](PRIVACY_POLICY.md)
- [License](LICENSE)

## 🏢 About ActProof.ai

ActProof.ai is an enterprise AI compliance platform helping organizations navigate EU AI Act requirements. We provide automated scanning, risk assessment, and compliance monitoring for AI systems.

**Contact:**
- Website: https://app.actproof.ai
- Email: info@actproof.ai
- Twitter: [@actproof_ai](https://twitter.com/actproof_ai)

---

## ⚠️ Disclaimer

ActProof.ai provides compliance guidance and recommendations. **Final compliance determination requires professional legal review.** We are not a law firm and do not provide legal advice.

---

© 2024-2025 ActProof.ai. All rights reserved.

Made with ❤️ for the AI community.

