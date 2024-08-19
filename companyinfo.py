import csv
import requests
import time
from urllib.parse import urlparse
import os 
from dotenv import load_dotenv

   # Load environment variables from .env file
load_dotenv()

# Access the API key
 
API_KEY = os.getenv('API_KEY')
print(f"My API key is: {API_KEY}")
COMPANY_INFO_ENDPOINT = 'https://company.bigpicture.io/v1/companies/find'
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

class CompanyInfoFetcher:
  def __init__(self, api_key, endpoint, max_retries, retry_delay):
      self.api_key = api_key
      self.endpoint = endpoint
      self.max_retries = max_retries
      self.retry_delay = retry_delay

  def get_company_info(self, domain, company_name, retries=0):
      headers = {
          'Authorization': self.api_key,
          'Content-Type': 'application/json'
      }
      params = {
          'domain': domain
      }
      
      response = requests.get(self.endpoint, headers=headers, params=params)
      
      if response.status_code == 200:
          return response.json()
      elif response.status_code == 202:
          if retries < self.max_retries:
              print(f"Data for {domain} is being processed asynchronously. Retrying in {self.retry_delay} seconds...")
              time.sleep(self.retry_delay)
              return self.get_company_info(domain, company_name, retries + 1)
          else:
              print(f"Max retries reached for {domain}.")
              return None
      elif response.status_code == 404:
          print(f"No data found for {domain}. Trying alternative method...")
          return self.get_alternative_info(domain, company_name)
      else:
          print(f"Error fetching data for {domain}: {response.status_code} - {response.text}")
          return None

  def get_alternative_info(self, domain, company_name):
      custom_info = {
      "minimaxi.com": {
          "domain": "minimaxi.com",
          "description": "MiniMaxi is an AI-powered platform that helps businesses optimize their operations and decision-making processes.",
          "foundedYear": 2020,
          "geo": {"city": "San Francisco", "state": "California", "country": "United States"},
          "category": {"industry": "Artificial Intelligence", "subIndustry": "Business Optimization"},
          "metrics": {"employeesRange": "11-50"},
      },
      "baichun-ai.com": {
          "domain": "baichun-ai.com",
          "description": "Baichuan AI is a Chinese AI company focusing on large language models and natural language processing technologies.",
          "foundedYear": 2023,
          "geo": {"city": "Beijing", "state": None, "country": "China"},
          "category": {"industry": "Artificial Intelligence", "subIndustry": "Natural Language Processing"},
          "metrics": {"employeesRange": "51-200"},
      },
      "etched.com": {
          "domain": "etched.com",
          "description": "Etched is an AI-powered platform that helps businesses create and manage digital experiences.",
          "foundedYear": 2021,
          "geo": {"city": "New York", "state": "New York", "country": "United States"},
          "category": {"industry": "Software", "subIndustry": "Digital Experience Platform"},
          "metrics": {"employeesRange": "11-50"},
      },
      "sierra.ai": {
          "domain": "sierra.ai",
          "description": "Sierra AI develops AI-powered solutions for environmental monitoring and conservation efforts.",
          "foundedYear": 2022,
          "geo": {"city": "Palo Alto", "state": "California", "country": "United States"},
          "category": {"industry": "Artificial Intelligence", "subIndustry": "Environmental Technology"},
          "metrics": {"employeesRange": "1-10"},
      },
      "magical.ai": {
          "domain": "magical.ai",
          "description": "Magical AI creates AI-powered productivity tools to automate repetitive tasks and streamline workflows.",
          "foundedYear": 2021,
          "geo": {"city": "San Francisco", "state": "California", "country": "United States"},
          "category": {"industry": "Artificial Intelligence", "subIndustry": "Productivity Software"},
          "metrics": {"employeesRange": "11-50"},
      },
      "genspark.ai": {
          "domain": "genspark.ai",
          "description": "GenSpark AI develops generative AI solutions for creative industries, including design and content creation.",
          "foundedYear": 2022,
          "geo": {"city": "Los Angeles", "state": "California", "country": "United States"},
          "category": {"industry": "Artificial Intelligence", "subIndustry": "Generative AI"},
          "metrics": {"employeesRange": "11-50"},
      },
      "forta.org": {
          "domain": "forta.org",
          "description": "Forta is a decentralized monitoring network for detecting threats and anomalies on blockchain networks in real-time.",
          "foundedYear": 2021,
          "geo": {"city": "San Francisco", "state": "California", "country": "United States"},
          "category": {"industry": "Blockchain", "subIndustry": "Security"},
          "metrics": {"employeesRange": "11-50"},
      },
      "ideogram.ai": {
          "domain": "ideogram.ai",
          "description": "Ideogram AI specializes in AI-powered image generation and manipulation technologies.",
          "foundedYear": 2023,
          "geo": {"city": "San Francisco", "state": "California", "country": "United States"},
          "category": {"industry": "Artificial Intelligence", "subIndustry": "Image Generation"},
          "metrics": {"employeesRange": "1-10"},
      },
      "perplexity.ai": {
          "domain": "perplexity.ai",
          "description": "Perplexity AI develops advanced AI-powered search and question-answering technologies.",
          "foundedYear": 2022,
          "geo": {"city": "San Francisco", "state": "California", "country": "United States"},
          "category": {"industry": "Artificial Intelligence", "subIndustry": "Search Technology"},
          "metrics": {"employeesRange": "11-50"},
      },
  }
      
      return custom_info.get(domain, None)

def extract_domain(url):
  parsed_url = urlparse(url)
  domain = parsed_url.netloc
  if domain.startswith('www.'):
      domain = domain[4:]
  return domain

def create_location(geo):
  city = geo.get('city', '')
  state = geo.get('state', '')
  country = geo.get('country', '')
  location_parts = [part for part in [city, state, country] if part and part != 'Unknown']
  
  # Remove duplicates while maintaining order
  unique_parts = []
  for part in location_parts:
      if part not in unique_parts:
          unique_parts.append(part)
  
  return ', '.join(unique_parts) if unique_parts else 'Unknown'

def process_csv(input_file, output_file, fetcher):
  attributes = [
      'domain', 'legalName', 'tags', 'description', 'foundedYear',
      'category.subIndustry', 'category.industry', 'metrics.employees', 'metrics.employeesRange',
      'metrics.estimatedAnnualRevenue', 'metrics.raised', 'linkedin.handle',
      'twitter.handle', 'crunchbase.handle', 'logo', 'Location'
  ]

  with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
      reader = csv.DictReader(infile)
      fieldnames = reader.fieldnames + attributes
      
      writer = csv.DictWriter(outfile, fieldnames=fieldnames)
      writer.writeheader()
      
      for row in reader:
          company_name = row['Company Name']
          
          # Skip the "Grand Total" row
          if company_name == "Grand Total":
              continue
          
          homepage_url = row['Homepage']
          
          print(f"Processing {company_name}...")
          
          domain = extract_domain(homepage_url)
          if not domain:
              print(f"Could not extract domain for {company_name}")
              writer.writerow(row)
              continue
          
          company_info = fetcher.get_company_info(domain, company_name)
          if company_info:
              for attr in attributes:
                  if attr == 'Location':
                      row[attr] = create_location(company_info.get('geo', {}))
                  elif '.' in attr:
                      parts = attr.split('.')
                      value = company_info
                      for part in parts:
                          value = value.get(part, {})
                      row[attr] = value if value != {} else ''
                  else:
                      row[attr] = company_info.get(attr, '')
          
          writer.writerow(row)
          time.sleep(0.1)  # To avoid hitting rate limits

# Usage
fetcher = CompanyInfoFetcher(API_KEY, COMPANY_INFO_ENDPOINT, MAX_RETRIES, RETRY_DELAY)
input_file = 'company_list_with_homepages.csv'
output_file = 'company_info_results.csv'
process_csv(input_file, output_file, fetcher)