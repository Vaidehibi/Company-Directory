import http.client
import json
import csv
import time
import re
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

class CompanySearcher:
  def __init__(self, api_key):
      self.api_key = api_key

  def search_company(self, company_name):
      conn = http.client.HTTPSConnection("google.serper.dev")
      payload = json.dumps({
          "q": f"{company_name} AI company official website",
          "num": 10  # Increase the number of results
      })
      headers = {
          'X-API-KEY': self.api_key,
          'Content-Type': 'application/json'
      }
      conn.request("POST", "/search", payload, headers)
      res = conn.getresponse()
      data = res.read()
      return json.loads(data.decode("utf-8"))

class HomepageExtractor:
  def __init__(self):
      self.non_homepage_domains = [
          'www.bloomberg.com', 'www.linkedin.com', 'www.crunchbase.com', 'en.wikipedia.org',
          'twitter.com', 'www.facebook.com', 'www.instagram.com', 'pitchbook.com',
          'www.youtube.com', 'github.com', 'medium.com', 'techcrunch.com'
      ]

  def extract_homepage(self, search_results, company_name):
      if 'organic' not in search_results or len(search_results['organic']) == 0:
          return "N/A"
      
      # Special handling for Quora and Vilya
      if company_name.lower() == "quora":
          return "https://www.quora.com"
      elif company_name.lower() == "vilya":
          return "https://vilyatx.com"
      
      for result in search_results['organic']:
          link = result['link']
          title = result['title'].lower()
          snippet = result.get('snippet', '').lower()
          
          if self.is_likely_homepage(link, company_name, title, snippet):
              return self.clean_url(link)
      
      # If no suitable homepage found, return the first result that's not a known non-homepage
      for result in search_results['organic']:
          link = result['link']
          if not self.is_known_non_homepage(link):
              return self.clean_url(link)
      
      return "N/A"

  def is_likely_homepage(self, link, company_name, title, snippet):
      parsed_url = urlparse(link)
      
      # Check if the link is not to common non-homepage sites
      if self.is_known_non_homepage(link):
          return False
      
      # Remove common suffixes from company name for more flexible matching
      company_name_clean = re.sub(r'\s*(inc\.?|corp\.?|ltd\.?|llc\.?)$', '', company_name, flags=re.IGNORECASE).strip()
      
      # Check if any part of the company name is in the domain
      company_parts = company_name_clean.lower().split()
      if any(part in parsed_url.netloc.lower() for part in company_parts):
          return True
      
      # Check for common homepage indicators
      if parsed_url.path in ['', '/'] or re.search(r'^/(en|us)/?$', parsed_url.path):
          return True
      
      # Check if company name is in the title
      if company_name_clean.lower() in title:
          return True
      
      # Check for AI-related keywords
      ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'deep learning', 'neural network']
      if any(keyword in title or keyword in snippet for keyword in ai_keywords):
          return True
      
      return False

  def is_known_non_homepage(self, link):
      parsed_url = urlparse(link)
      return parsed_url.netloc in self.non_homepage_domains

  def clean_url(self, url):
      # Remove URL parameters and fragments
      parsed = urlparse(url)
      clean = parsed._replace(params='', query='', fragment='')
      return clean.geturl().rstrip('/')

def process_csv(input_file, output_file, searcher, extractor):
  with open(input_file, 'r', encoding='utf-8') as csvfile:
      reader = csv.DictReader(csvfile)
      fieldnames = reader.fieldnames + ['Homepage']
      
      with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
          writer = csv.DictWriter(outfile, fieldnames=fieldnames)
          writer.writeheader()
          
          for row in reader:
              company_name = row['Company Name']
              print(f"Searching for: {company_name}")
              
              search_results = searcher.search_company(company_name)
              homepage = extractor.extract_homepage(search_results, company_name)
              
              row['Homepage'] = homepage
              writer.writerow(row)
              
              # Add a delay to avoid hitting rate limits
              time.sleep(1)

def main():
  api_key = os.getenv('API_KEY')
  searcher = CompanySearcher(api_key)
  extractor = HomepageExtractor()
  
  input_file = 'company_list.csv'
  output_file = 'company_list_with_homepages.csv'
  process_csv(input_file, output_file, searcher, extractor)
  
  print(f"Process completed. Results saved to {output_file}")

if __name__ == "__main__":
  main()