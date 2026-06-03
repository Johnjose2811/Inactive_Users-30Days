# System Architecture

## Overview

The Inactive Users - 30 Days Report system is designed to automatically identify and notify managers about inactive employees using a distributed processing approach with PySpark and cloud services.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Source Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐        ┌──────────────────────┐      │
│  │  ACTIVITY_TABLE      │        │  EMPLOYEE_TABLE      │      │
│  │  - USER_EMAIL        │        │  - EmployeeID        │      │
│  │  - Last_date_visit   │        │  - EmpName           │      │
│  │  - Activity_minutes  │        │  - Department        │      │
│  │                      │        │  - Manager Email     │      │
│  └──────────────────────┘        └──────────────────────┘      │
└──────────────────┬─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│            Databricks/PySpark Processing Layer                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQL Query Execution                                     │  │
│  │  - Join ACTIVITY_TABLE & EMPLOYEE_TABLE                 │  │
│  │  - Filter: Last_date_visit <= (TODAY - 30 days)         │  │
│  │  - Spark DataFrame Output                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Transformation                                    │  │
│  │  - Convert Spark DF to Pandas                           │  │
│  │  - Group by ReportingManager                            │  │
│  │  - Prepare email data                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────┬─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│            Authentication & Authorization Layer                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Azure AD Authentication                                │  │
│  │  - Client ID, Tenant ID, Client Secret                  │  │
│  │  - OAuth 2.0 Client Credentials Flow                    │  │
│  │  - Get Access Token for Graph API                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────┬─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│            Report Generation Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  HTML Email Generation                                  │  │
│  │  - Personalized for each manager                        │  │
│  │  - Summary statistics                                   │  │
│  │  - Employee details table                               │  │
│  │  - Styled HTML with CSS                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────┬─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│            Email Delivery Layer                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Microsoft Graph API                                    │  │
│  │  - Authenticate with Bearer Token                       │  │
│  │  - Send mail endpoint (POST)                            │  │
│  │  - Handle responses (202 = success)                     │  │
│  │  - Error handling & logging                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────┬─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│             Notification/Output Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐        ┌──────────────────────┐      │
│  │  Manager Inbox       │        │  Console Logs        │      │
│  │  - HTML Email        │        │  - Execution status  │      │
│  │  - Inactive list     │        │  - Success/Failure   │      │
│  │  - Action items      │        │  - Metrics           │      │
│  └──────────────────────┘        └──────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Source Layer

**Purpose**: Provide employee activity and master data

**Components**:
- **ACTIVITY_TABLE**: Contains user activity metrics
  - USER_EMAIL: Employee identifier
  - Last_date_visit: Most recent activity date
  - num_video_consumed_minutes: Activity duration

- **EMPLOYEE_TABLE**: Contains employee master data
  - EmployeeID: Unique identifier
  - EmpName: Employee name
  - Department: Organizational unit
  - ReportingManager: Manager details

**Responsibilities**:
- Store and maintain data integrity
- Provide query performance
- Support join operations

### 2. Processing Layer

**Purpose**: Execute queries and transform data for report generation

**Key Functions**:
- `main_execution()`: Orchestrates the workflow
  - Executes SQL query to identify inactive employees
  - Converts distributed Spark DataFrame to Pandas
  - Groups data by reporting manager

**Performance Characteristics**:
- Handles millions of employee records
- Distributed across Spark cluster nodes
- Efficient join and filter operations

### 3. Authentication Layer

**Purpose**: Securely obtain credentials for Microsoft Graph API

**Key Function**: `get_access_token()`
- Uses OAuth 2.0 Client Credentials Flow
- Requests token from Azure AD
- Returns bearer token for API calls
- Error handling for failed authentication

**Security**:
- No user interaction required
- Service-to-service authentication
- Token cached during execution

### 4. Report Generation Layer

**Purpose**: Create formatted HTML content for email

**Key Function**: `create_html_email()`
- Generates personalized HTML template
- Includes summary statistics
- Formats employee data in table
- Applies CSS styling for professional appearance

**Features**:
- Responsive design
- Color-coded sections
- Sortable table (browser support)
- Professional branding

### 5. Email Delivery Layer

**Purpose**: Send generated reports to managers

**Key Function**: `send_email_with_html()`
- Prepares email payload (JSON)
- Calls Microsoft Graph API sendMail endpoint
- Handles multiple recipients
- Implements error handling and retry logic

**API Details**:
```
Endpoint: https://graph.microsoft.com/v1.0/users/{FROM_EMAIL}/sendMail
Method: POST
Auth: Bearer Token
Response: 202 (Accepted) = Success
```

### 6. Output/Notification Layer

**Purpose**: Deliver results to stakeholders

**Outputs**:
- **Manager Emails**: HTML formatted inactivity reports
- **Console Logs**: Real-time execution tracking
- **Execution Summary**: Success/failure metrics

## Data Flow

### Detailed Process Flow

```
1. START
   │
   ├─ Initialize PySpark Session
   ├─ Load configuration
   ├─ Authenticate to Azure AD
   │
2. QUERY EXECUTION
   ├─ Execute SQL to join tables
   ├─ Filter for Last_date_visit <= 30 days ago
   ├─ Get distinct managers
   │
3. DATA CONVERSION
   ├─ Convert Spark DF to Pandas
   ├─ Drop duplicates (manager records)
   │
4. MANAGER PROCESSING LOOP
   ├─ For each manager:
   │  ├─ Filter inactive employees for this manager
   │  ├─ Sort by EmployeeID
   │  ├─ Create personalized HTML email
   │  ├─ Send via Microsoft Graph API
   │  ├─ Record success/failure
   │  └─ Log timing metrics
   │
5. EXECUTION SUMMARY
   ├─ Print success count
   ├─ Print failure count
   │
6. END
```

## Error Handling Strategy

### Error Categories

| Category | Cause | Handler |
|----------|-------|---------|
| Authentication | Invalid credentials | Exit with error message |
| Network | Connection timeout | Retry with backoff |
| API Response | 4xx/5xx status | Log and skip manager |
| Data | Missing fields | Use default values |

### Recovery Mechanisms

1. **Authentication Failure**
   - Exit immediately (blocking issue)
   - Display error details

2. **Email Send Failure**
   - Continue to next manager
   - Increment failure counter
   - Log for manual review

3. **Data Quality Issues**
   - Handle missing dates as "N/A"
   - Handle null minutes as "0"

## Performance Characteristics

### Scalability

| Metric | Capacity | Notes |
|--------|----------|-------|
| Employees | 1,000,000+ | Via PySpark distribution |
| Managers | 10,000+ | Sequential processing |
| Email Recipients | Multiple per manager | Supports comma/semicolon |
| Execution Time | Depends on cluster | ~1-5 minutes typical |

### Optimization Opportunities

1. **Concurrent Email Sending**
   - Use ThreadPoolExecutor
   - Process multiple managers in parallel

2. **Incremental Processing**
   - Track processed managers
   - Skip previously sent reports

3. **Caching**
   - Cache employee-manager mapping
   - Reduce repeated queries

## Security Architecture

### Authentication Flow

```
┌─────────────┐
│  Databricks │
│  Notebook   │
└──────┬──────┘
       │
       │ POST /oauth2/v2.0/token
       │ (client_id, client_secret)
       │
       ▼
┌──────────────────┐
│   Azure AD       │
│  Token Endpoint  │
└──────┬───────────┘
       │
       │ Response: access_token
       │
       ▼
┌──────────────────┐
│ Microsoft Graph  │
│  API Endpoint    │
│ (sendMail)       │
└──────────────────┘
```

### Credential Management

**Best Practices**:
- Store in Azure Key Vault (not in code)
- Use Managed Identities when possible
- Rotate secrets regularly
- Audit access logs

### Data Privacy

- Emails sent via secure HTTPS
- No logs contain sensitive data
- Complies with data protection regulations

## Deployment Architecture

### Databricks Deployment

```
┌─────────────────────────────────────────┐
│        Databricks Workspace             │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐  │
│  │     Notebook / Job                │  │
│  │  inactive_users_report.py         │  │
│  └───────────────────────────────────┘  │
│                 │                        │
│                 ▼                        │
│  ┌───────────────────────────────────┐  │
│  │   Databricks Cluster              │  │
│  │   - PySpark runtime               │  │
│  │   - Python 3.x                    │  │
│  │   - Driver + Executors            │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
          │
          │ Queries
          ▼
    ┌──────────────┐
    │  SQL Server  │
    │  or Azure DB │
    └──────────────┘
```

### Scheduling

```
┌─────────────────────────────┐
│  Scheduler (Databricks Job)  │
├─────────────────────────────┤
│  Trigger: Daily at 9:00 AM   │
│  Timezone: EST               │
│  Retries: On failure         │
└─────────────────────────────┘
         │
         ▼
   Run notebook job
```

## Monitoring & Observability

### Key Metrics

1. **Execution Metrics**
   - Total records processed
   - Total managers processed
   - Success count
   - Failure count

2. **Performance Metrics**
   - Query execution time
   - Email send latency
   - Total runtime

3. **Error Metrics**
   - Authentication failures
   - API errors
   - Data quality issues

### Logging Strategy

- **Console Output**: Real-time execution tracking
- **Databricks Logs**: Job execution history
- **Application Logs**: Detailed operation logs

## Future Architecture Enhancements

1. **Distributed Email Sending**
   - Parallel processing with ThreadPoolExecutor
   - Improve throughput for many managers

2. **Real-time Reporting**
   - Stream processing with Spark Streaming
   - Immediate notification on inactivity

3. **Advanced Analytics**
   - Trend analysis for inactivity patterns
   - Predictive alerts

4. **Multi-channel Notifications**
   - Teams integration
   - Slack notifications
   - SMS alerts

5. **Report Customization**
   - Per-department templates
   - Custom metrics

---

**Architecture Version**: 1.0
**Last Updated**: June 2026
