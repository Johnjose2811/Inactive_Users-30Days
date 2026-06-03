# Configuration Guide

## Azure AD Setup

### Step 1: Create Azure AD Application

1. Sign in to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **+ New registration**
4. Enter application name: `Inactive Users Report`
5. Select **Accounts in this organizational directory only**
6. Click **Register**

### Step 2: Configure Application Permissions

1. In your app registration, go to **API permissions**
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Choose **Application permissions**
5. Search for and add: `Mail.Send`
6. Click **Grant admin consent**

### Step 3: Create Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **+ New client secret**
3. Set expiration (recommended: 24 months)
4. Copy the **Value** (not the ID)
5. Store securely in Azure Key Vault

### Step 4: Collect Credentials

Record the following from your app registration overview:
- **Application (client) ID**: `client_id`
- **Directory (tenant) ID**: `tenant_id`
- **Client secret value**: `client_secret`

## Script Configuration

Update the configuration section in `inactive_users_report.py`:

```python
# Azure AD Configuration
client_id = "YOUR_CLIENT_ID"
tenant_id = "YOUR_TENANT_ID"
client_secret = "YOUR_CLIENT_SECRET"
FROM_EMAIL = "analytics@company.com"
```

### Using Azure Key Vault (Recommended)

Instead of hardcoding credentials, use Azure Key Vault:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

vault_url = "https://your-vault.vault.azure.net/"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=vault_url, credential=credential)

client_id = client.get_secret("client-id").value
tenant_id = client.get_secret("tenant-id").value
client_secret = client.get_secret("client-secret").value
FROM_EMAIL = client.get_secret("from-email").value
```

## Database Configuration

### SQL Server Table Structure

#### ACTIVITY_TABLE
```sql
CREATE TABLE ACTIVITY_TABLE (
    USER_EMAIL NVARCHAR(255),
    Last_date_visit DATE,
    num_video_consumed_minutes INT,
    -- Add other columns as needed
)
```

#### EMPLOYEE_TABLE
```sql
CREATE TABLE EMPLOYEE_TABLE (
    EmployeeID NVARCHAR(50),
    EmpName NVARCHAR(255),
    Emailaddress NVARCHAR(255),
    Designation NVARCHAR(255),
    Department NVARCHAR(255),
    ReportingManager NVARCHAR(255),
    ReportingManagerEmailID NVARCHAR(255),
    -- Add other columns as needed
)
```

### Databricks Connection

Configure your Databricks cluster to connect to your data source:

1. Create a cluster with PySpark runtime
2. Install required libraries:
   ```bash
   %pip install msal azure-identity requests
   ```
3. Configure secrets scope:
   ```python
   dbutils.secrets.createScope("azure-creds")
   dbutils.secrets.put("azure-creds", "client-id", "YOUR_CLIENT_ID")
   dbutils.secrets.put("azure-creds", "tenant-id", "YOUR_TENANT_ID")
   dbutils.secrets.put("azure-creds", "client-secret", "YOUR_CLIENT_SECRET")
   ```

## Email Configuration

### Sender Email Setup

1. **Create Service Account** in Azure AD:
   - Email: analytics@company.com
   - License: Exchange Online Plan 2 (or required license)

2. **Enable Graph API Permissions**:
   - Ensure the service account has Mail.Send permission
   - May require admin approval in Azure AD

3. **Configure in Script**:
   ```python
   FROM_EMAIL = "analytics@company.com"
   ```

### Multiple Recipients

The script supports multiple recipients per manager:

```python
# Semicolon-separated
to_email = "manager1@company.com;manager2@company.com"

# Comma-separated
to_email = "manager1@company.com, manager2@company.com"
```

## Email Template Customization

### Modifying Email Content

Edit the `create_html_email()` function to customize:

```python
def create_html_email(data_df, manager_name):
    # Customize the HTML template
    html = f"""
    <html>
    <head>
        <style>
            /* Modify CSS styles here */
        </style>
    </head>
    <body>
        <!-- Customize HTML content -->
    </body>
    </html>
    """
    return html
```

### CSS Customization

Modify colors and styles:

```python
h2 {{
    color: #YOUR_COLOR;  # Change header color
    border-bottom: 3px solid #YOUR_COLOR;
}}

th {{
    background-color: #YOUR_COLOR;  # Change table header color
}}
```

## Databricks Job Scheduling

### Create a Scheduled Job

1. In Databricks workspace, click **Jobs**
2. Click **+ Create Job**
3. **Configure job**:
   - Name: `Inactive Users Report`
   - Cluster: Select your cluster
   - Notebook: Select `inactive_users_report.py`

4. **Set schedule**:
   - Click **Edit schedule**
   - Choose frequency (Daily, Weekly, Monthly)
   - Set timezone
   - Click **Save**

### Example: Daily at 9 AM

```
Frequency: Daily
Time: 09:00 AM
Timezone: Eastern Standard Time
```

## Monitoring and Logging

### View Job Runs

1. Go to your job in Databricks
2. Click **Runs**
3. Select a run to view logs

### Enable Detailed Logging

Add logging to script:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Starting inactive users report")
```

### Send Logs to Azure Log Analytics

```python
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry import logs

exporter = AzureMonitorLogExporter(
    connection_string="YOUR_CONNECTION_STRING"
)

# Configure logging to send to Azure
```

## Testing Configuration

### Test Authentication

```python
def test_authentication():
    """Test Azure AD authentication"""
    token = get_access_token()
    if token:
        print("✓ Authentication successful")
        return True
    else:
        print("✗ Authentication failed")
        return False

test_authentication()
```

### Test Email Sending

```python
def test_email():
    """Send test email"""
    token = get_access_token()
    result = send_email_with_html(
        access_token=token,
        to_email="test@company.com",
        subject="Test Email",
        html_content="<p>Test content</p>",
        manager_name="Test Manager"
    )
    return result

test_email()
```

### Test Data Query

```python
def test_query():
    """Test database query"""
    df = spark.sql("""
        SELECT COUNT(*) as total
        FROM ACTIVITY_TABLE
        WHERE Last_date_visit <= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
    """)
    df.show()

test_query()
```

## Performance Tuning

### Optimize PySpark Query

```python
# Enable broadcast join for large tables
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10485760")  # 10MB

# Increase partition count for better parallelism
spark.conf.set("spark.sql.shuffle.partitions", "200")
```

### Improve Email Sending

```python
# Use concurrent processing for multiple managers
from concurrent.futures import ThreadPoolExecutor

def send_emails_concurrent(managers, data_df, access_token, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for _, manager_row in managers.iterrows():
            future = executor.submit(send_to_manager, manager_row, data_df, access_token)
            futures.append(future)
        return [f.result() for f in futures]
```

## Troubleshooting

### Common Issues

**Issue**: `Authentication failed: Invalid client ID`
- **Solution**: Verify `client_id`, `tenant_id` are correct in Azure portal

**Issue**: `Mail.Send permission not granted`
- **Solution**: Admin consent required in Azure AD → Enterprise applications

**Issue**: `Table not found: ACTIVITY_TABLE`
- **Solution**: Verify table exists and user has SELECT permissions

**Issue**: Timeout on email sending
- **Solution**: Increase timeout from 120 to 300 seconds in `send_email_with_html()`

---

For additional help, contact your Azure/Databricks administrator.
