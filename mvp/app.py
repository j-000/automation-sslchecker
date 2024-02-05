from sslchecker import SSLChecker
import datetime
import os 

# Helper functions
def days_delta(domain):
    # Calculate difference in days between expiry date and today
    expiry = datetime.datetime.strptime(domain['expiry'], '%d %b %Y')
    today = datetime.datetime.today()
    return abs(expiry - today).days

def min_daysleft(client):
    # Calculate the number of days due for each domain.
    # Return the minimum (soonest/next due).
    return min(map(lambda domain: days_delta(domain), client['domains']))

def get_file_size_in_mb(file_path):
    try:
        # Get the file size in bytes
        size_in_bytes = os.stat(file_path).st_size
        # Convert bytes to megabytes (1 MB = 1024 * 1024 bytes)
        size_in_mb = size_in_bytes / (1024 * 1024)
        return size_in_mb
    except FileNotFoundError:
        return -1  # Indicate that the file was not found

#Main program
# Initiate program class
checker = SSLChecker()

# Start SSL check for all clients in db
checker.check_all()

# Filter clients based on condition 
# condition: next due in the next 30 days
due_in_30_days = filter(lambda client: min_daysleft(client) < 30 , checker.db['clients'])

# Create email HTML
html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SSL Check</title>
    <meta name="description" content="SSL Check report">
    <meta name="author" content="Joao Oliveira">
    <style>
        body {
            font-family: system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue","Noto Sans","Liberation Sans",Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji";
            font-size: 1rem;
        }
		table {
			border:1px solid #b3adad;
			border-collapse:collapse;
			padding:5px;
		}
		table th {
			border:1px solid #b3adad;
			padding:5px;
			background: #f0f0f0;
			color: #313030;
		}
		table td {
			border:1px solid #b3adad;
			text-align:center;
			padding:5px;
			color: #313030;
		}
        .table-warning{
            background-color: #fff3cd!important;
        }
	</style>
</head>
<body>
"""

for client in due_in_30_days:
    h2 = f"<h2>{client['name']}</h2>"
    domains_table = """
    <table class='table'>
        <thead>
            <th>Domain</th>
            <th>Expiry</th>
            <th>days left</th>
        </thead>
        <tbody>"""
    sorted_domains = sorted(client['domains'], key=lambda d: days_delta(d))
    for domain in sorted_domains:
        highlight_row = ''
        daysleft = days_delta(domain)
        if daysleft < 30:
            highlight_row = 'table-warning'
        domains_table += f"""
        <tr class='{highlight_row}'>
            <td>{domain['url']}</td>
            <td>{domain['expiry']}</td>
            <td>{daysleft} days</td>
        </tr>"""
    domains_table += "</tbody></table>"
    html += h2
    html += domains_table
html += "</body></html>"

filename = 'report.html'

# Write file locally
with open(filename, 'w') as f:
    f.write(html)

# Zip file if more than 20Mb
file_size_in_mb = get_file_size_in_mb(filename)
print(file_size_in_mb)
if file_size_in_mb > 20:    
    import zipfile
    with zipfile.ZipFile('d.html.zip', 'w') as zipf:
        zipf.write(filename, os.path.basename(filename))

# Send email alert

