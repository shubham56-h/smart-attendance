import os
from dotenv import load_dotenv

print("Before loading .env:")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'NOT SET')}")

load_dotenv()

print("\nAfter loading .env:")
database_url = os.environ.get('DATABASE_URL', 'NOT SET')
print(f"DATABASE_URL: {database_url}")

if database_url != 'NOT SET':
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    print(f"\nParsed URL:")
    print(f"  Scheme: {parsed.scheme}")
    print(f"  Username: {parsed.username}")
    print(f"  Password: {parsed.password}")
    print(f"  Hostname: {parsed.hostname}")
    print(f"  Port: {parsed.port}")
    print(f"  Database: {parsed.path[1:]}")
