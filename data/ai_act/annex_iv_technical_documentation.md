# Annex IV - Technical Documentation for High-Risk AI Systems

## Article 11 - Technical Documentation Requirements

High-risk AI systems must be accompanied by technical documentation demonstrating compliance with the requirements of the AI Act. The documentation must be kept up-to-date and available to national competent authorities.

## 1. General Description of the AI System

### 1.1 System Identification
- **Name and version** of the AI system
- **Type of AI system**: standalone, component, or integrated into a product
- **Intended purpose** and reasonably foreseeable misuse
- **Provider information**: name, address, contact details
- **Date of development** and deployment history

### 1.2 Functionality Overview
- Detailed description of system functions and capabilities
- Main features and operational characteristics
- Inputs accepted and outputs generated
- User interface and interaction mechanisms
- System dependencies and third-party components

## 2. Detailed System Description

### 2.1 Methods and Steps
A detailed description of:
- Development process and methodology
- Design specifications and system architecture
- Algorithms, techniques, and AI/ML models used
- Main design choices and trade-offs
- Assumptions made during development
- Development environment and tools

### 2.2 System Architecture
- Overall system structure and components
- Data flow diagrams
- Integration with external systems
- Hardware and software dependencies
- Network architecture (if applicable)

## 3. Context of Use

### 3.1 Intended Use Environment
- **Geographic scope**: regions where system will be deployed
- **Target users**: description of intended user groups
- **Use context**: physical and digital environments
- **Operational conditions**: temperature, lighting, connectivity, etc.
- **Time-related constraints**: operational hours, shift patterns

### 3.2 User Characteristics
- Expected user skills and training requirements
- User supervision requirements
- Accessibility considerations
- Language and cultural contexts

## 4. Detailed Description of System Elements

### 4.1 Data Description

#### 4.1.1 Training Data
- **Data sources**: origin and provenance of training datasets
- **Data volume**: size, number of samples, temporal coverage
- **Data characteristics**: features, labels, annotations
- **Data quality**: completeness, accuracy, consistency
- **Representativeness**: coverage of target population
- **Data protection measures**: GDPR compliance, anonymization
- **Bias assessment**: known biases and mitigation strategies

#### 4.1.2 Testing and Validation Data
- Separate datasets used for testing and validation
- Data splitting methodology
- Cross-validation strategies
- Test set characteristics and representativeness

#### 4.1.3 Input Data Specifications
- Expected input data format and structure
- Data preprocessing and normalization
- Missing data handling
- Input validation and sanitization

### 4.2 Pre-Processing and Feature Engineering
- Data cleaning procedures
- Feature extraction and selection methods
- Data augmentation techniques
- Dimensionality reduction
- Encoding of categorical variables

## 5. Technical Specifications

### 5.1 Computational Requirements
- **Hardware specifications**:
  - Processing units (CPU, GPU, TPU)
  - Memory requirements (RAM, storage)
  - Network bandwidth
  - Specialized hardware (sensors, accelerators)

- **Software specifications**:
  - Operating system and version
  - Runtime environments and dependencies
  - Libraries and frameworks with versions
  - Database systems
  - APIs and external services

### 5.2 Performance Specifications
- Response time requirements
- Throughput capacity
- Scalability characteristics
- Resource consumption (energy, compute)
- Availability and uptime requirements

## 6. Detailed Information on Training

### 6.1 Training Methodology
- Machine learning paradigm (supervised, unsupervised, reinforcement learning)
- Model architecture and hyperparameters
- Optimization algorithms and learning rates
- Training duration and computational resources
- Regularization techniques

### 6.2 Training Procedures
- Data splitting ratios (train/validation/test)
- Batch sizes and epochs
- Convergence criteria
- Early stopping strategies
- Model checkpointing

### 6.3 Model Selection and Validation
- Candidate models evaluated
- Selection criteria and metrics
- Validation methodology
- Cross-validation results
- Model comparison and justification of final choice

## 7. Accuracy, Robustness, and Cybersecurity

### 7.1 Accuracy Metrics (Article 15)
Documentation must include:

#### 7.1.1 Performance Metrics
- **Classification tasks**: Accuracy, precision, recall, F1-score, AUC-ROC
- **Regression tasks**: MAE, MSE, RMSE, R²
- **Object detection**: mAP, IoU
- **NLP tasks**: BLEU, ROUGE, perplexity
- **Overall performance**: confusion matrices, error distributions

#### 7.1.2 Sub-Population Performance
- Performance breakdown by demographic groups
- Performance across different use contexts
- Worst-case performance analysis
- Performance degradation conditions

### 7.2 Robustness Assessment
- **Adversarial robustness**: resistance to adversarial examples
- **Data drift handling**: performance under distribution shift
- **Edge case behavior**: response to out-of-distribution inputs
- **Stress testing**: performance under extreme conditions
- **Noise tolerance**: sensitivity to input perturbations

### 7.3 Cybersecurity Measures
- **Threat model**: identified security threats and attack vectors
- **Security controls**: authentication, authorization, encryption
- **Data protection**: secure storage, transmission, processing
- **Access control**: user permissions and role-based access
- **Incident response**: procedures for security breaches
- **Security testing**: penetration testing, vulnerability assessment
- **Compliance**: relevant security standards (ISO 27001, etc.)

## 8. Risk Management System (Article 9)

### 8.1 Risk Identification
- **Foreseeable risks**: systematic identification of potential harms
- **Risk categories**: health, safety, fundamental rights
- **Severity assessment**: potential impact of each risk
- **Likelihood estimation**: probability of risk occurrence

### 8.2 Risk Analysis
- Risk prioritization matrix
- Vulnerable populations identification
- Context-specific risk factors
- Aggregated risk assessment

### 8.3 Risk Mitigation Measures
- **Technical measures**: design choices reducing risk
- **Organizational measures**: policies, training, oversight
- **Testing and validation**: verification of mitigation effectiveness
- **Residual risks**: remaining risks after mitigation
- **Continuous monitoring**: ongoing risk assessment procedures

## 9. Human Oversight (Article 14)

### 9.1 Human Oversight Measures
For high-risk systems, documentation must describe:

- **Human-in-the-loop**: human intervention in every decision
- **Human-on-the-loop**: human supervision during operation
- **Human-in-command**: human ability to override or shut down

### 9.2 Oversight Capabilities
- Understanding system outputs
- Interpreting system's operation
- Detecting anomalies and malfunctions
- Intervening and overriding decisions
- Emergency stop functionality

### 9.3 Oversight Procedures
- Roles and responsibilities of oversight personnel
- Training requirements for oversight
- Decision-making authority
- Escalation procedures
- Documentation of human interventions

## 10. Transparency and User Information (Article 13)

### 10.1 Instructions for Use
- Clear and comprehensible instructions
- Intended purpose and limitations
- Level of accuracy and known limitations
- Expected lifetime and maintenance
- Installation and setup procedures

### 10.2 Information to Users
- Nature and purpose of AI system
- Identity and contact details of provider
- Human oversight measures
- Expected accuracy and potential errors
- Obligations of the deployer

## 11. Quality Management System

### 11.1 Development Process
- Quality assurance procedures
- Code review and testing practices
- Version control and change management
- Documentation standards

### 11.2 Post-Market Monitoring
- Performance monitoring plan
- Incident reporting procedures
- Update and patch management
- End-of-life procedures

## 12. Conformity Assessment

### 12.1 Conformity Assessment Procedure
- Internal control or third-party assessment
- Standards and benchmarks used
- Test results and certifications
- Declaration of conformity

### 12.2 Compliance Evidence
- Mapping of requirements to implementation
- Test reports and validation results
- Certificates and approvals
- Ongoing compliance monitoring

## 13. Record-Keeping (Article 12)

### 13.1 Automatic Logging
Systems must automatically log:
- Operating period and timestamps
- Reference database(s) used
- Input data and preprocessing
- Identification of persons involved in verification
- Results and decisions made

### 13.2 Log Retention
- Retention period appropriate to intended purpose
- Security and integrity of logs
- Access controls for log data
- Log format and accessibility for authorities

## Documentation Maintenance

### Update Requirements
Technical documentation must be:
- Kept up-to-date throughout system lifecycle
- Updated when system is modified or retrained
- Reviewed periodically (at least annually)
- Available to competent authorities on request

### Version Control
- Documentation version matching system version
- Change log documenting all updates
- Traceability between documentation versions and system versions
- Archive of previous documentation versions

## Compliance References
- EU AI Act Article 11 (Technical Documentation)
- EU AI Act Article 9 (Risk Management)
- EU AI Act Article 14 (Human Oversight)
- EU AI Act Article 15 (Accuracy, Robustness, Cybersecurity)
- Harmonized Standards (when available)
