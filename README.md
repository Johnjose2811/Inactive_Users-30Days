# Inactive Users - 30 Days Report

A PySpark-based automated system that queries employee activity data, identifies inactive employees (30+ days), and sends personalized HTML email reports to their managers via Microsoft Graph API.

## Overview

This system automates the process of identifying and notifying managers about inactive employees. It integrates with:
- **PySpark** for distributed data processing
- **Databricks** for cluster management
- **Microsoft Graph API** for email delivery
- **Azure AD** for authentication

## Features

✨ **Key Capabilities:**
- Automated identification of employees inactive for 30+ days
- Personalized HTML email reports for each manager
- Integration with Microsoft Graph API for email delivery
- Batch processing using PySpark for scalability
- Comprehensive logging and error handling
- Support for multiple email recipients per manager

## Requirements

### Prerequisites
- Databricks cluster with PySpark
- Microsoft Azure AD credentials
- Access to employee activity and employee master tables

### Python Dependencies

Install the required packages in your Databricks cluster:

```bash
%pip install msal azure-identity requests
```

## Configuration

### Azure AD Setup

Update the following configuration variables in `inactive_users_report.py`:

```python
client_id = "your-client-id-here"           # Azure AD Application ID
tenant_id = "your-tenant-id-here"           # Azure AD Tenant ID
client_secret = "your-client-secret-here"   # Azure AD Client Secret
FROM_EMAIL = "sender-email@company.com"     # Sender email address
```

### Data Source

The script assumes two tables are available:

#### ACTIVITY_TABLE
- `USER_EMAIL`: Employee email address
- `Last_date_visit`: Date of last activity (DATE format)
- `num_video_consumed_minutes`: Minutes of activity

#### EMPLOYEE_TABLE
- `EmployeeID`: Unique employee identifier
- `EmpName`: Employee full name
- `Emailaddress`: Employee email
- `Designation`: Job title
- `Department`: Department name
- `ReportingManager`: Manager name
- `ReportingManagerEmailID`: Manager email address

## Usage

### Running the Script

Execute the script in your Databricks notebook:

```python
%run ./inactive_users_report.py
```

Or run directly in a Databricks cell:

```python
exec(open('inactive_users_report.py').read())
```

### Script Workflow

1. **Authentication**: Obtains access token from Microsoft Graph API
2. **Data Extraction**: Queries activity and employee data using SQL
3. **Processing**: Converts Spark DataFrame to Pandas for processing
4. **Grouping**: Groups inactive employees by reporting manager
5. **Report Generation**: Creates formatted HTML email content
6. **Email Distribution**: Sends personalized reports to each manager
7. **Logging**: Provides execution summary with success/failure counts

## Output

### Email Report Contains

| Field | Description |
|-------|-------------|
| Employee ID | Unique identifier |
| Employee Name | Full name |
| Email | Contact email |
| Designation | Job title |
| Department | Department name |
| Last Date Visit | Last activity date |
| Activity Minutes | Total minutes of activity |
| Manager | Reporting manager name |

### Console Output

The script provides real-time logging:
```
============================================================
[HH:MM:SS] INACTIVITY REPORT - STARTING
============================================================
[HH:MM:SS] Executing query...
[HH:MM:SS] ✓ Query executed
[HH:MM:SS] Total records: 150
[HH:MM:SS] Converting to Pandas...
[HH:MM:SS] Total Managers: 12
[HH:MM:SS] Authenticating to Microsoft Graph...
[HH:MM:SS] ✓ Successfully authenticated
...
[HH:MM:SS] COMPLETE!
Success: 12 | Failed: 0
============================================================
```

## Functions

### `get_access_token()`
Authenticates to Microsoft Graph API using client credentials flow.

**Returns**: Access token string or None on failure

### `send_email_with_html(access_token, to_email, subject, html_content, manager_name)`
Sends an email with HTML content via Microsoft Graph API.

**Parameters**:
- `access_token`: Bearer token for authentication
- `to_email`: Recipient email(s) (supports semicolon or comma-separated)
- `subject`: Email subject line
- `html_content`: HTML formatted email body
- `manager_name`: Manager name for logging

**Returns**: Boolean (True if status 202, False otherwise)

### `create_html_email(data_df, manager_name)`
Generates a formatted HTML email body from employee inactivity data.

**Parameters**:
- `data_df`: Pandas DataFrame with employee records
- `manager_name`: Manager name for personalization

**Returns**: HTML string

## Error Handling

The script includes robust error handling for:
- Authentication failures
- Network timeouts
- Invalid email formats
- API errors (non-202 responses)
- Missing data fields

## Performance

- **Scalability**: Uses PySpark for distributed processing
- **Batch Size**: Processes all managers in single execution
- **Timeout**: 120 seconds for email API calls
- **Concurrency**: Sequential processing of managers (can be optimized)

## Security Considerations

⚠️ **Important Security Notes**:
1. Never hardcode credentials in production
2. Use Azure Key Vault for credential management
3. Ensure client secrets are rotated regularly
4. Use appropriate access controls on Databricks notebooks
5. Monitor API usage for unauthorized access

## Troubleshooting

### Authentication Failed
```
[HH:MM:SS] ✗ Authentication failed
```
- Verify `client_id`, `tenant_id`, and `client_secret`
- Confirm Azure AD app has Mail.Send permissions
- Check network connectivity to Azure

### Email Send Failed (Status 403)
- Verify sender email account exists
- Check Mail.Send API permissions
- Confirm sender email is registered in Azure AD

### Query Execution Failed
- Verify table names match your schema
- Ensure date column is in correct format
- Check user has SELECT permissions on tables

## Scheduling

To run this report on a schedule:

1. **Databricks Jobs**: Create a job that runs the notebook on a schedule
2. **Azure Data Factory**: Orchestrate the Databricks job
3. **SQL Agent Jobs**: Schedule via SQL Server if using on-premises

## Future Enhancements

- [ ] Concurrent email processing for improved performance
- [ ] Email template customization
- [ ] Retry logic with exponential backoff
- [ ] Metrics and monitoring dashboard
- [ ] Configuration file support
- [ ] Logging to external systems (Cosmos DB, etc.)
- [ ] Support for Teams notifications

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please contact the Analytics Team.

---

**Last Updated**: June 2026
