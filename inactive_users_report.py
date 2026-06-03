# %%
# Import required libraries
import logging.config
import concurrent.futures
import os, sys, json, logging, timeit, uuid, time, pytz
from pyspark.sql import SparkSession
from pyspark.sql.types import ArrayType, StructType, StructField, IntegerType, StringType, FloatType, BooleanType, DecimalType, LongType, DoubleType, TimestampType, DateType
from datetime import datetime, timedelta, date
import pyspark.sql.functions as F
from pyspark.sql.functions import *

# %%
# Install required packages in Databricks cluster or notebook
%pip install msal azure-identity requests

# %%
# Azure AD Configuration - Replace with your values
client_id = "your-client-id-here"
tenant_id = "your-tenant-id-here"
client_secret = "your-client-secret-here"
FROM_EMAIL = "sender-email@company.com"

# %%
import msal
import requests
import json
import pandas as pd

# %%
# FUNCTION: Get Access Token
def get_access_token():
    """Authenticate and get access token using client credentials flow"""
    
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Authenticating to Microsoft Graph...")
    
    try:
        response = requests.post(token_url, data=token_data, timeout=30)
        response.raise_for_status()
        
        token_response = response.json()
        access_token = token_response.get('access_token')
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Successfully authenticated")
        return access_token
        
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Authentication failed: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")
        return None

# %%
# FUNCTION: Send Email with HTML Body
def send_email_with_html(access_token, to_email, subject, html_content, manager_name):
    """Send email with HTML content via Microsoft Graph API"""
    
    # Handle multiple recipients if needed
    if ';' in to_email:
        email_list = [email.strip() for email in to_email.split(';') if email.strip()]
    elif ',' in to_email:
        email_list = [email.strip() for email in to_email.split(',') if email.strip()]
    else:
        email_list = [to_email.strip()]
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Recipients: {len(email_list)}")
    for email in email_list:
        print(f"  - {email}")
    
    # Build toRecipients array
    to_recipients = [
        {"emailAddress": {"address": email}}
        for email in email_list
    ]
    
    # Prepare email payload
    email_message = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_content
            },
            "toRecipients": to_recipients
        },
        "saveToSentItems": True
    }
    
    send_mail_url = f"https://graph.microsoft.com/v1.0/users/{FROM_EMAIL}/sendMail"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending email to {manager_name}...")
    
    try:
        response = requests.post(
            send_mail_url,
            headers=headers,
            data=json.dumps(email_message),
            timeout=120
        )
        
        if response.status_code == 202:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Email sent successfully!")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Failed to send: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")
        return False

# %%
# FUNCTION: Create HTML Email Content
def create_html_email(data_df, manager_name):
    """Create HTML email body from DataFrame"""
    
    if data_df.empty:
        return """
        <html>
        <body>
            <p>Hello,</p>
            <p>No inactive employees found for your team.</p>
            <br>
            <p>Best regards,<br>Analytics Team</p>
        </body>
        </html>
        """
    
    employee_count = len(data_df)
    
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                color: #333;
            }}
            h2 {{
                color: #2c3e50;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }}
            .summary {{
                background-color: #f8f9fa;
                padding: 15px;
                border-left: 4px solid #4CAF50;
                margin: 20px 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-top: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th {{
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                text-align: left;
                border: 1px solid #ddd;
                font-weight: bold;
            }}
            td {{
                padding: 10px;
                border: 1px solid #ddd;
                text-align: left;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            tr:hover {{
                background-color: #e8f5e9;
                transition: background-color 0.3s;
            }}
            .footer {{
                margin-top: 30px;
                padding: 15px;
                background-color: #f8f9fa;
                border-top: 2px solid #4CAF50;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <h2>Employee Inactivity Report - Last 30 Days</h2>
        
        <p>Dear {manager_name},</p>
        
        <div class="summary">
            <strong>Summary:</strong><br>
            Total employees with inactivity: <strong>{employee_count}</strong><br>
            Report generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
        
        <p>Below are the employees under your management who have been inactive for more than 30 days:</p>
        
        <table>
            <thead>
                <tr>
                    <th>Employee ID</th>
                    <th>Employee Name</th>
                    <th>Email</th>
                    <th>Designation</th>
                    <th>Department</th>
                    <th>Last Date Visit</th>
                    <th>Activity Minutes</th>
                    <th>Manager</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, row in data_df.iterrows():
        # Format date
        try:
            last_visit = pd.to_datetime(row['Last_date_visit']).strftime('%b %d, %Y')
        except:
            last_visit = 'N/A'
        
        # Format minutes
        try:
            minutes = f"{float(row['num_video_consumed_minutes']):.0f}"
        except:
            minutes = '0'
        
        html += f"""
            <tr>
                <td>{row['EmployeeID']}</td>
                <td>{row['EmpName']}</td>
                <td>{row['Emailaddress']}</td>
                <td>{row['Designation']}</td>
                <td>{row['Department']}</td>
                <td>{last_visit}</td>
                <td>{minutes}</td>
                <td>{row['ReportingManager']}</td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <div class="footer">
            <p><strong>Action Required:</strong> Please review the above list and follow up with inactive employees.</p>
            <p><i>This is an automated report.</i></p>
            <br>
            <p>Best regards,<br>Analytics Team</p>
        </div>
    </body>
    </html>
    """
    
    return html

# %%
# Main Execution
print("\n" + "="*60)
print(f"[{datetime.now().strftime('%H:%M:%S')}] INACTIVITY REPORT - STARTING")
print("="*60)

# Query data - Replace with your actual query
print(f"[{datetime.now().strftime('%H:%M:%S')}] Executing query...")

query = """
SELECT DISTINCT
    B.EmployeeID,
    B.EmpName,
    B.Emailaddress,
    B.Designation,
    B.Department,
    A.Last_date_visit,
    A.num_video_consumed_minutes,
    B.ReportingManager,
    B.ReportingManagerEmailID
FROM ACTIVITY_TABLE AS A
JOIN EMPLOYEE_TABLE AS B
    ON A.USER_EMAIL = B.EMAILADDRESS
WHERE A.Last_date_visit <= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
    AND B.ReportingManagerEmailID IS NOT NULL
"""
df = spark.sql(query)

print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Query executed")
print(f"[{datetime.now().strftime('%H:%M:%S')}] Total records: {df.count()}")

# Convert to Pandas
print(f"[{datetime.now().strftime('%H:%M:%S')}] Converting to Pandas...")
pdf = df.toPandas()

# Get unique managers
managers = pdf[['ReportingManagerEmailID', 'ReportingManager']].drop_duplicates()
total_managers = len(managers)

print(f"[{datetime.now().strftime('%H:%M:%S')}] Total Managers: {total_managers}")

# Get access token
access_token = get_access_token()

if access_token is None:
    print("Failed to authenticate. Exiting...")
    sys.exit(1)

# Process each manager
print("\n" + "="*60)
print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing Managers")
print("="*60)

success_count = 0
fail_count = 0

for idx, (_, manager_row) in enumerate(managers.iterrows(), 1):
    manager_email = manager_row['ReportingManagerEmailID']
    manager_name = manager_row['ReportingManager']
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === {idx}/{total_managers}: {manager_name} ===")
    start_time = time.time()
    
    # Filter data for this manager
    manager_data = pdf[pdf['ReportingManagerEmailID'] == manager_email].sort_values('EmployeeID')
    
    employee_count = len(manager_data)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Employees: {employee_count}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Creating HTML email...")
    
    # Create HTML content
    html_content = create_html_email(manager_data, manager_name)
    
    # Email subject
    subject = f"Employee Inactivity Report - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Send email
    result = send_email_with_html(
        access_token=access_token,
        to_email=manager_email,
        subject=subject,
        html_content=html_content,
        manager_name=manager_name
    )
    
    if result:
        success_count += 1
    else:
        fail_count += 1
    
    elapsed = time.time() - start_time
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Time: {elapsed:.1f}s | Progress: {idx}/{total_managers}")

# Final summary
print("\n" + "="*60)
print(f"[{datetime.now().strftime('%H:%M:%S')}] COMPLETE!")
print(f"Success: {success_count} | Failed: {fail_count}")
print("="*60)
