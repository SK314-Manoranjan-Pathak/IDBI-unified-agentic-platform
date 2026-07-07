# Architecture & Flow Diagrams (Mermaid)

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        CBS[Core Banking System]
        AA[Account Aggregator<br/>Sahamati]
        UPI[UPI Transaction<br/>History]
        GST[GST Portal]
        EPFO[EPFO Data]
        UTIL[Utility Bills]
    end

    subgraph "ML Scoring Service<br/>(SageMaker / EC2 Mumbai)"
        FE[Feature Engineering<br/>Pipeline]
        TXE[Transaction<br/>Transformer<br/>Embeddings]
        PM[Propensity<br/>Model<br/>XGBoost]
        HM[Health Score<br/>Model<br/>Multi-output XGBoost]
        DM[Default Prediction<br/>Model<br/>Ensemble]
        LED[Life Event<br/>Detector]
    end

    subgraph "AWS Bedrock AgentCore<br/>(ap-south-1 Mumbai)"
        GW[AgentCore Gateway<br/>MCP Protocol]
        RT[AgentCore Runtime<br/>Serverless]
        MEM[AgentCore Memory<br/>Semantic + Episodic]
        ID[AgentCore Identity<br/>Credentials Vault]
        PE[Policy Engine<br/>Cedar Policies]
        OBS[AgentCore<br/>Observability]
    end

    subgraph "Strands Agents<br/>(Running in AgentCore Runtime)"
        SUP[Supervisor Agent]
        PA[Prospect Agent]
        HA[Health Agent]
        RA[Risk Agent]
        EA[Engagement Agent]
    end

    subgraph "Output Channels"
        DASH[RM Dashboard]
        PUSH[Push Notifications]
        SMS[SMS / WhatsApp]
        EMAIL[Email]
        INAPP[In-App Messages]
        RMCAL[RM Call List]
    end

    CBS --> FE
    AA --> FE
    UPI --> FE
    GST --> FE
    EPFO --> FE
    UTIL --> FE

    FE --> TXE
    TXE --> PM
    TXE --> HM
    TXE --> DM
    FE --> LED

    PM -->|Propensity Flags| GW
    HM -->|Health Signals| GW
    DM -->|Default Alerts| GW
    LED -->|Life Events| GW

    GW --> RT
    RT --> SUP
    SUP --> PA
    SUP --> HA
    SUP --> RA
    SUP --> EA

    PA --> MEM
    HA --> MEM
    RA --> MEM
    EA --> MEM

    ID --> GW
    PE --> RT
    OBS --> RT

    EA --> PUSH
    EA --> SMS
    EA --> EMAIL
    EA --> INAPP
    PA --> RMCAL
    RA --> DASH
    HA --> DASH
```


---

## 2. Agent Orchestration Flow (Functional)

```mermaid
flowchart TD
    A[ML Pipeline Generates Signal] --> B{Supervisor Agent}
    
    B -->|Propensity > 70| C[Prospect Agent]
    B -->|Health Delta < -15| D[Risk Agent]
    B -->|New Customer + Consent| E[Health Agent]
    B -->|Life Event Detected| F[Engagement Agent]
    B -->|PD > 30%| D
    
    C --> C1{Check Memory:<br/>Recent offer sent?}
    C1 -->|Yes, < 90 days| C2[SKIP - Don't repeat]
    C1 -->|No| C3[Qualify Lead]
    C3 --> C4[Match Product & Amount]
    C4 --> C5{Risk Check:<br/>Default PD < 15%?}
    C5 -->|Yes| C6[Generate Offer]
    C5 -->|No| C7[SKIP - Too risky]
    C6 --> C8[Route to Engagement Agent]
    C6 --> C9[Add to RM Call List]
    
    D --> D1[Pull Stress Timeline]
    D1 --> D2[SHAP Explanation]
    D2 --> D3{Severity Assessment}
    D3 -->|Level 1-2| D4[Add to Watch List]
    D3 -->|Level 3| D5[Alert RM + Contact Customer]
    D3 -->|Level 4| D6[Escalate to Risk Committee]
    D5 --> D7[Recommend Intervention]
    
    E --> E1[Pull AA Data with Consent]
    E1 --> E2[Pull GST + EPFO + Utility]
    E2 --> E3[Compute 6-Dimension Score]
    E3 --> E4[Generate Health Card]
    E4 --> E5[Send to Underwriter]
    
    F --> F1{Check Memory:<br/>Contact frequency OK?}
    F1 -->|Too frequent| F2[Schedule for Later]
    F1 -->|OK| F3[Determine Channel + Language]
    F3 --> F4[Generate Personalized Message]
    F4 --> F5[Send via Preferred Channel]
    F5 --> F6[Log to Memory + Schedule Follow-up]
```

---

## 3. Data Pipeline Flow

```mermaid
flowchart LR
    subgraph "Raw Data Ingestion"
        T1[Salary Credits]
        T2[UPI Payments]
        T3[EMI Debits]
        T4[Card Transactions]
        T5[Bill Payments]
        T6[Investment Debits]
    end

    subgraph "Feature Engineering"
        direction TB
        CF[Cash Flow Features<br/>surplus, volatility,<br/>min balance trend]
        BF[Behavioral Features<br/>categories, timing,<br/>merchant patterns]
        TF[Temporal Features<br/>Transformer embeddings,<br/>sequence patterns]
        IS[Intent Signals<br/>dealer visits,<br/>portal payments]
        SS[Stress Signals<br/>SIP stops, FD closure,<br/>cash advances]
        EF[External Features<br/>GST, EPFO,<br/>utility data]
    end

    subgraph "Model Inference"
        direction TB
        M1[Propensity Head<br/>Score: 0-100<br/>Product: Auto/Home/PL]
        M2[Health Head<br/>6 dimensions<br/>Score: 0-100 each]
        M3[Default Head<br/>PD: 0-100%<br/>12-month horizon]
        M4[Life Event Head<br/>Event type<br/>Confidence %]
    end

    subgraph "Signal Output"
        S1[High Propensity<br/>Alert]
        S2[Health Change<br/>Alert]
        S3[PD Spike<br/>Alert]
        S4[Life Event<br/>Alert]
    end

    T1 & T2 & T3 & T4 & T5 & T6 --> CF & BF & TF
    T2 --> IS
    T3 & T5 & T6 --> SS
    CF & BF & TF & IS --> M1
    CF & BF & TF & EF --> M2
    CF & BF & TF & SS --> M3
    BF & TF & IS --> M4

    M1 -->|score > 70| S1
    M2 -->|delta < -15| S2
    M3 -->|PD > 30%| S3
    M4 -->|confidence > 80%| S4
```

---

## 4. AgentCore Memory Architecture

```mermaid
graph TB
    subgraph "AgentCore Memory"
        subgraph "Semantic Memory<br/>(Long-term Knowledge)"
            SM1[Customer Financial Profile]
            SM2[Product Holdings & Preferences]
            SM3[Risk Assessment History]
            SM4[Life Events Detected]
        end
        
        subgraph "Episodic Memory<br/>(Interaction History)"
            EM1[Agent Actions Taken]
            EM2[Customer Responses]
            EM3[RM Conversation Summaries]
            EM4[Offer Acceptance/Rejection]
        end
        
        subgraph "User Preference Memory<br/>(Communication Style)"
            PM1[Preferred Language]
            PM2[Preferred Channel]
            PM3[Preferred Timing]
            PM4[Contact Frequency Limit]
        end
    end

    subgraph "Agents Read & Write"
        PA[Prospect Agent]
        HA[Health Agent]
        RA[Risk Agent]
        EA[Engagement Agent]
    end

    PA -->|Reads| SM1
    PA -->|Reads| EM4
    PA -->|Writes| EM1

    HA -->|Writes| SM1
    HA -->|Writes| SM3
    HA -->|Reads| SM4

    RA -->|Reads| SM3
    RA -->|Reads| EM1
    RA -->|Writes| EM1

    EA -->|Reads| PM1
    EA -->|Reads| PM2
    EA -->|Reads| PM3
    EA -->|Reads| PM4
    EA -->|Reads| EM1
    EA -->|Writes| EM2
```

---

## 5. Multi-Bank Deployment Architecture (Non-Functional)

```mermaid
graph TB
    subgraph "Bank A - IDBI"
        A_GW[Gateway<br/>IDBI CBS API<br/>IDBI Notification]
        A_RT[Runtime<br/>Same Agent Code]
        A_MEM[Memory<br/>IDBI Customers]
        A_ID[Identity<br/>IDBI Credentials]
        A_ML[ML Models<br/>Trained on IDBI Data]
    end

    subgraph "Bank B - SBI"
        B_GW[Gateway<br/>SBI YONO API<br/>SBI Notification]
        B_RT[Runtime<br/>Same Agent Code]
        B_MEM[Memory<br/>SBI Customers]
        B_ID[Identity<br/>SBI Credentials]
        B_ML[ML Models<br/>Trained on SBI Data]
    end

    subgraph "Bank C - PNB"
        C_GW[Gateway<br/>PNB CBS API<br/>PNB Notification]
        C_RT[Runtime<br/>Same Agent Code]
        C_MEM[Memory<br/>PNB Customers]
        C_ID[Identity<br/>PNB Credentials]
        C_ML[ML Models<br/>Trained on PNB Data]
    end

    subgraph "Shared Platform Code"
        SC[Strands Agent Code<br/>Supervisor + Sub-Agents]
        FE[Feature Engineering<br/>Pipeline Code]
        DASH[Dashboard<br/>Template]
    end

    SC --> A_RT
    SC --> B_RT
    SC --> C_RT
    FE --> A_ML
    FE --> B_ML
    FE --> C_ML
    DASH --> A_RT
    DASH --> B_RT
    DASH --> C_RT
```


---

## 6. Agent Autonomy Tiers (Governance Flow)

```mermaid
flowchart TD
    A[Agent Decides Action] --> B{Classify Risk Tier}
    
    B -->|Tier 1: Low Risk| T1[Execute Autonomously]
    B -->|Tier 2: Medium Risk| T2[Execute + Notify Human]
    B -->|Tier 3: High Risk| T3[Recommend + Wait for Approval]
    
    subgraph "Tier 1 — Full Autonomy"
        T1 --> T1A[Send informational nudge]
        T1 --> T1B[Add to RM call list]
        T1 --> T1C[Generate report]
        T1 --> T1D[Schedule follow-up reminder]
        T1 --> T1E[Update Memory]
    end
    
    subgraph "Tier 2 — Act + Notify"
        T2 --> T2A[Send pre-approved offer]
        T2 --> T2B[Flag account for review]
        T2 --> T2C[Initiate soft collection contact]
        T2 --> T2D[Adjust credit limit recommendation]
        T2 --> T2N[Notify: RM / Risk Team]
    end
    
    subgraph "Tier 3 — Human Decides"
        T3 --> T3A[Loan approval / rejection]
        T3 --> T3B[EMI restructuring]
        T3 --> T3C[Account recall]
        T3 --> T3D[Credit limit change]
        T3 --> T3W[Wait for Human Approval]
        T3W -->|Approved| T3E[Execute]
        T3W -->|Rejected| T3F[Log + Learn]
    end

    T1 --> LOG[Audit Log<br/>AgentCore Observability]
    T2 --> LOG
    T3E --> LOG
    T3F --> LOG
```

---

## 7. Customer Lifecycle Journey (Sequence Diagram)

```mermaid
sequenceDiagram
    participant C as Customer
    participant ML as ML Pipeline
    participant SUP as Supervisor Agent
    participant PA as Prospect Agent
    participant EA as Engagement Agent
    participant RM as Relationship Manager
    participant MEM as AgentCore Memory

    Note over ML: Daily/Hourly scoring cycle
    ML->>ML: Score all customers
    ML->>SUP: Signal: Propensity spike (Score: 87, Auto Loan)
    
    SUP->>MEM: Check recent actions for customer
    MEM-->>SUP: No recent contact (45 days ago)
    SUP->>MEM: Check default risk
    MEM-->>SUP: PD = 3% (healthy)
    
    SUP->>PA: Route: Qualify this prospect
    PA->>PA: Validate intent (3 dealer payments)
    PA->>PA: Calculate capacity (surplus ₹42K)
    PA->>PA: Size loan (₹10L @ 8.5%)
    PA->>PA: Generate pre-approved offer
    
    PA->>EA: Send personalized nudge to customer
    PA->>RM: Add to call list (Day+2 follow-up)
    
    EA->>MEM: Check preferences
    MEM-->>EA: English, Push, Evening
    EA->>C: Push notification (7:15 PM)
    EA->>MEM: Log: offer_sent, awaiting_response
    
    Note over C: Day+1: Customer views offer
    C->>C: Opens notification, explores details
    
    Note over RM: Day+2: RM follows up
    RM->>C: Call: "Noticed you might be car shopping..."
    C->>RM: "Yes! What's the max tenure?"
    RM->>C: Discusses details
    
    Note over C: Day+5: Loan sanctioned
    C->>C: Starts application
    
    PA->>MEM: Log: conversion_successful
    PA->>ML: Feedback: positive outcome → model learns
```

---

## 8. Early Warning Sequence (Default Prevention)

```mermaid
sequenceDiagram
    participant ML as ML Pipeline
    participant SUP as Supervisor Agent
    participant RA as Risk Agent
    participant EA as Engagement Agent
    participant RM as Relationship Manager
    participant RC as Risk Committee
    participant C as Customer
    participant MEM as AgentCore Memory

    Note over ML: Continuous monitoring
    ML->>ML: Day 15: PD rises 6% → 9% (SIP cancelled)
    ML->>SUP: Level 1 Watch signal
    SUP->>RA: Monitor - no action yet
    RA->>MEM: Log: watch_initiated

    ML->>ML: Day 30: PD rises to 18% (FD pre-closed)
    ML->>SUP: Level 2 Alert signal
    SUP->>RA: Assess and recommend

    RA->>RA: Pull stress timeline
    RA->>RA: SHAP analysis: salary_delay 35%, fd_closure 25%
    RA->>RA: Pattern match: "job transition" (not systematic)
    RA->>MEM: Check: any recent context?
    MEM-->>RA: No recent contact

    ML->>ML: Day 40: PD spikes to 38% (cash advances)
    ML->>SUP: Level 3 Action Required
    SUP->>RA: Act now - EMI due in 5 days

    RA->>RM: URGENT: Call today. Likely job transition.<br/>Offer moratorium. Context attached.
    RA->>EA: Send gentle message to customer
    EA->>C: "Need flexibility with upcoming EMI? We can help."
    RA->>MEM: Log: intervention_initiated

    RM->>C: Calls customer
    C->>RM: "Changed jobs. Gap between salaries."
    RM->>RM: Offer 2-month moratorium
    C->>RM: "That would be great!"

    RM->>RC: Moratorium request (prepared by RA)
    RC->>RC: Approve (Tier 3 human decision)
    
    Note over C: Day 60: New salary starts
    ML->>ML: PD drops to 8%
    RA->>MEM: Log: intervention_successful, account_saved
    RA->>ML: Feedback: pattern confirmed as temporary
```

---

## 9. Health Card Assessment Flow

```mermaid
flowchart TD
    A[NTC/NTB Customer<br/>Applies for Loan] --> B[Consent Request<br/>via Account Aggregator]
    B --> C{Customer<br/>Approves?}
    C -->|No| D[Cannot Assess<br/>Traditional Process]
    C -->|Yes| E[Health Agent Activated]
    
    E --> F[Pull AA Data<br/>12-month bank statements]
    E --> G[Pull GST Data<br/>Filing history + revenue]
    E --> H[Pull EPFO Data<br/>Contributions + employment]
    E --> I[Pull Utility Data<br/>Electricity + telecom]
    
    F & G & H & I --> J[Feature Extraction]
    
    J --> K[Income Stability<br/>Score]
    J --> L[Spending Discipline<br/>Score]
    J --> M[Cash Flow Adequacy<br/>Score]
    J --> N[Debt Management<br/>Score]
    J --> O[Growth Trajectory<br/>Score]
    J --> P[External Compliance<br/>Score]
    
    K & L & M & N & O & P --> Q[Composite Health Score<br/>0-100]
    
    Q --> R[Peer Benchmarking<br/>Compare vs segment]
    R --> S[Generate Visual<br/>Health Card]
    
    S --> T{Score > Threshold?}
    T -->|Yes ≥ 60| U[Recommend: APPROVE<br/>with conditions]
    T -->|Borderline 40-60| V[Recommend: REVIEW<br/>additional checks]
    T -->|No < 40| W[Recommend: DECLINE<br/>with reasons]
    
    U & V & W --> X[Send to Underwriter<br/>Tier 3: Human Decides]
    X --> Y[Underwriter Reviews<br/>Health Card + SHAP]
    Y --> Z[Final Decision]
```

---

## 10. Non-Functional Architecture (Scalability & Security)

```mermaid
graph TB
    subgraph "Security Boundary"
        subgraph "AWS Mumbai Region (ap-south-1)"
            subgraph "VPC - Private Subnet"
                ML_SVC[ML Scoring Service<br/>SageMaker Endpoint]
                DB[(PostgreSQL RDS<br/>Customer Data)]
                REDIS[(Redis ElastiCache<br/>Feature Store)]
            end
            
            subgraph "AgentCore (Managed)"
                AC_RT[Runtime<br/>Auto-scaling<br/>0 → N sessions]
                AC_GW[Gateway<br/>Rate limiting<br/>Auth: IAM/JWT]
                AC_MEM[Memory<br/>Encrypted at rest<br/>KMS managed]
                AC_ID[Identity<br/>Secrets Manager<br/>Credential rotation]
                AC_PE[Policy Engine<br/>Cedar: least privilege]
                AC_OBS[Observability<br/>Full audit trail<br/>CloudTrail integration]
            end
            
            subgraph "Event Processing"
                EB[EventBridge<br/>Real-time triggers]
                SQS[SQS Dead Letter<br/>Retry failed actions]
            end
            
            subgraph "External Integrations"
                AA_API[Account Aggregator<br/>mTLS + consent]
                SARVAM[Sarvam AI<br/>Indian servers]
                NOTIF[Notification Service<br/>SNS + SES]
            end
        end
    end

    subgraph "Compliance Controls"
        KMS[AWS KMS<br/>Encryption keys]
        CT[CloudTrail<br/>API audit]
        GD[GuardDuty<br/>Threat detection]
        WAFV2[WAF v2<br/>API protection]
    end

    AC_RT --> ML_SVC
    AC_RT --> DB
    AC_RT --> REDIS
    AC_GW --> AC_RT
    EB --> AC_GW
    AC_RT --> AA_API
    AC_RT --> SARVAM
    AC_RT --> NOTIF
    
    KMS --> AC_MEM
    KMS --> DB
    CT --> AC_OBS
    GD --> AC_RT
    WAFV2 --> AC_GW
```

---

## 11. Scalability Metrics (Non-Functional Requirements)

```mermaid
graph LR
    subgraph "Performance Targets"
        P1[ML Scoring<br/>< 200ms per customer]
        P2[Agent Decision<br/>< 2s per signal]
        P3[Notification Delivery<br/>< 5s end-to-end]
        P4[Health Card Generation<br/>< 30s with AA pull]
        P5[Dashboard Load<br/>< 1s for portfolio view]
    end

    subgraph "Scale Targets"
        S1[Customers: 10M+<br/>per bank deployment]
        S2[Daily Scoring<br/>Batch: 10M in < 2hrs]
        S3[Real-time Events<br/>10K signals/minute]
        S4[Concurrent Agents<br/>1000 sessions]
        S5[Memory Records<br/>100M+ per bank]
    end

    subgraph "Availability"
        A1[Agent Runtime: 99.9%<br/>AgentCore SLA]
        A2[ML Service: 99.5%<br/>SageMaker SLA]
        A3[Database: 99.99%<br/>RDS Multi-AZ]
        A4[Gateway: 99.9%<br/>Managed service]
    end

    subgraph "Security"
        SEC1[Data at rest:<br/>AES-256 via KMS]
        SEC2[Data in transit:<br/>TLS 1.3]
        SEC3[Access control:<br/>Cedar policies]
        SEC4[Credential rotation:<br/>Every 90 days]
        SEC5[PII handling:<br/>Tokenized in Memory]
    end
```

---

## 12. Event-Driven Architecture Flow

```mermaid
flowchart LR
    subgraph "Event Sources"
        TXN[New Transaction<br/>Arrives]
        BATCH[Daily Batch<br/>Scoring Complete]
        THRESH[Threshold<br/>Breach Detected]
        SCHED[Scheduled<br/>Check-in]
        USER[Customer<br/>App Activity]
    end

    subgraph "Event Bus (EventBridge)"
        EB[AWS EventBridge<br/>Rules Engine]
    end

    subgraph "Processing"
        ML[ML Pipeline<br/>Re-score if needed]
        AGT[Agent Invocation<br/>via AgentCore Gateway]
    end

    subgraph "Agent Actions"
        A1[Notify RM]
        A2[Send Customer Message]
        A3[Update Dashboard]
        A4[Escalate to Risk]
        A5[Generate Report]
        A6[Schedule Follow-up]
    end

    TXN -->|Rule: amount > ₹1L<br/>OR new merchant category| EB
    BATCH -->|Rule: any PD > threshold| EB
    THRESH -->|Rule: score change > delta| EB
    SCHED -->|Rule: daily 9AM portfolio check| EB
    USER -->|Rule: customer viewed offer| EB

    EB -->|Transform + Route| ML
    EB -->|Transform + Route| AGT

    ML -->|New scores| AGT
    AGT --> A1 & A2 & A3 & A4 & A5 & A6
```

---

## 13. Compliance & Audit Architecture

```mermaid
flowchart TD
    subgraph "Every Agent Action"
        AA[Agent Action Initiated]
        AA --> LOG[Log to AgentCore<br/>Observability]
        AA --> AUD[Write Audit Record<br/>to PostgreSQL]
        AA --> MEM_LOG[Update AgentCore<br/>Memory - Episodic]
    end

    subgraph "Audit Record Contents"
        AUD --> R1[Timestamp]
        AUD --> R2[Agent ID + Name]
        AUD --> R3[Customer ID]
        AUD --> R4[Action Type]
        AUD --> R5[Input Signal<br/>ML scores that triggered]
        AUD --> R6[Agent Reasoning<br/>Why this action was chosen]
        AUD --> R7[SHAP Explanation<br/>Model feature importance]
        AUD --> R8[Outcome<br/>Success/Failure/Pending]
        AUD --> R9[Human Override<br/>If any]
    end

    subgraph "RBI Compliance Checks"
        CHK1[Kill-Switch<br/>Disable agent in < 1min]
        CHK2[Human Override<br/>100% of Tier 3 decisions]
        CHK3[Explainability<br/>Every prediction has SHAP]
        CHK4[Model Inventory<br/>All models registered + versioned]
        CHK5[Drift Monitoring<br/>Weekly accuracy checks]
        CHK6[Data Lineage<br/>Source → Feature → Prediction → Action]
    end

    LOG --> DASH_INT[Internal Compliance<br/>Dashboard]
    AUD --> DASH_INT
    CHK1 & CHK2 & CHK3 & CHK4 & CHK5 & CHK6 --> DASH_INT
    DASH_INT --> RBI_REP[RBI Regulatory<br/>Reporting]
```

---

## 14. Customer Engagement Decision Tree

```mermaid
flowchart TD
    START[Signal Received:<br/>Customer Needs Contact] --> CHK1{Check Memory:<br/>Last contact < 48hrs?}
    
    CHK1 -->|Yes| WAIT[Schedule for later<br/>Respect frequency limit]
    CHK1 -->|No| CHK2{Check Memory:<br/>Customer in DND?}
    
    CHK2 -->|Yes| WAIT2[Wait until DND expires]
    CHK2 -->|No| CHK3{Check Time:<br/>Within preferred hours?}
    
    CHK3 -->|No| SCHED[Schedule for<br/>preferred time window]
    CHK3 -->|Yes| CHK4{Determine<br/>Channel Priority}
    
    CHK4 --> CH1{Preference:<br/>WhatsApp?}
    CH1 -->|Yes| WA[Send via WhatsApp]
    CH1 -->|No| CH2{Preference:<br/>Push?}
    CH2 -->|Yes| PUSH_N[Send Push Notification]
    CH2 -->|No| CH3{Preference:<br/>SMS?}
    CH3 -->|Yes| SMS_N[Send SMS]
    CH3 -->|No| EMAIL_N[Send Email]
    
    WA & PUSH_N & SMS_N & EMAIL_N --> LANG{Generate in<br/>Preferred Language}
    
    LANG -->|Hindi| SARVAM_HI[Sarvam: Hindi]
    LANG -->|Tamil| SARVAM_TA[Sarvam: Tamil]
    LANG -->|English| ENG[English Direct]
    LANG -->|Other| SARVAM_OT[Sarvam: Translate]
    
    SARVAM_HI & SARVAM_TA & ENG & SARVAM_OT --> SEND[Deliver Message]
    SEND --> LOG_M[Log to Memory:<br/>message_sent, timestamp,<br/>channel, content_hash]
    LOG_M --> FOLLOW[Schedule Follow-up<br/>Check response in 48hrs]
```
