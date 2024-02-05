import datetime
import OpenSSL
import ssl
from dataclasses import dataclass
import json


@dataclass
class SSLInfo:
  domain: str
  expiry: datetime.date
  daysleft: int


class SSLChecker:

  def __init__(self):
    self.db = self._read_db()

  def get_client(self, client_id):
    # Return next client from filtered condition or None
    client = next(filter(lambda client: client['id'] == client_id, self.db['clients']), None)
    return client

  def get_ssl_info(self, domain):
    cert = ssl.get_server_certificate((domain, 443))
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    bytes_data = x509.get_notAfter()
    ssl_timestamp = bytes_data.decode('utf-8')
    expirydate = datetime.datetime.strptime(ssl_timestamp, '%Y%m%d%H%M%S%z').date()
    deltadate = expirydate - datetime.date.today()
    return SSLInfo(domain=domain, expiry=expirydate, daysleft=deltadate.days)

  def save(self):
    self._write_db(self.db)

  def check_client(self, client_id):
    # Find client obj by client_id
    client = self.get_client(client_id)
    # No match for client_id
    if not client:
      return
    # Select filtered object
    for domain in client['domains']:
      # Get SSL information object for each client domain
      sslinfo = self.get_ssl_info(domain['url'])
      # Write domain expiry date to DB object
      domain['expiry'] = sslinfo.expiry.strftime('%d %b %Y')
    # Save check date to DB object 
    client['last_checked'] = datetime.date.today().strftime('%d %b %Y')
    # Save DB object update
    self.save()

  def check_all(self):
    for client in self.db['clients']: 
      self.check_client(client['id'])
    # Save check date to DB object 
    self.db['last_checked_all'] = datetime.date.today().strftime('%d %b %Y')
    # Save DB object update
    self.save()

  def _read_db(self):
    db = json.load(open('db.json', 'r'))
    return db

  def _write_db(self, new_db):
    json.dump(new_db, open('db.json', mode='w', encoding='utf-8'), indent=4)
