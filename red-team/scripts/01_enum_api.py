#!/usr/bin/env python3
"""
Red Team - API Enumeration Tool
Script: 01_enum_api.py
Purpose: Discover and map all API endpoints on OWASP Juice Shop
Features:
  - Brute force endpoint discovery
  - HTTP method testing (GET, POST, PUT, DELETE)
  - Authentication requirement detection
  - Response analysis and classification
  - CSV/JSON export of findings
  - Rate limiting bypass attempts
Version: 1.0
Author: Red Team
"""

import requests
import argparse
import json
import csv
import sys
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('enum_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class APIEnumerator:
    """Enumerate and test API endpoints"""
    
    def __init__(self, base_url, timeout=10, delay=0.1):
        """
        Initialize API Enumerator
        Args:
            base_url: Target application URL
            timeout: HTTP request timeout
            delay: Delay between requests (rate limiting)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Red-Team-API-Enumerator/1.0'
        })
        self.results = []
        self.endpoints_found = set()
        
    def test_endpoint(self, path, method='GET'):
        """
        Test a single endpoint with given HTTP method
        Args:
            path: API endpoint path
            method: HTTP method (GET, POST, PUT, DELETE)
        Returns:
            Response object or None
        """
        url = urljoin(self.base_url, path)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=self.timeout, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, timeout=self.timeout, headers=headers, json={})
            elif method == 'PUT':
                response = self.session.put(url, timeout=self.timeout, headers=headers, json={})
            elif method == 'DELETE':
                response = self.session.delete(url, timeout=self.timeout, headers=headers)
            else:
                return None
                
            return response
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"Error testing {path}: {str(e)}")
            return None
        finally:
            time.sleep(self.delay)
    
    def analyze_response(self, response, path, method):
        """
        Analyze response and extract relevant information
        Args:
            response: Response object
            path: Endpoint path
            method: HTTP method
        Returns:
            Dictionary with analysis
        """
        if not response:
            return None
        
        auth_required = False
        is_api = False
        content_type = response.headers.get('Content-Type', '')
        
        # Determine if authentication is required
        if response.status_code in [401, 403]:
            auth_required = True
        
        # Determine if it's an API endpoint
        if 'json' in content_type.lower() or 'application/json' in content_type:
            is_api = True
        
        try:
            if response.text:
                response.json()
                is_api = True
        except:
            pass
        
        data = {
            'path': path,
            'method': method,
            'status_code': response.status_code,
            'content-type': content_type,
            'content-length': len(response.content),
            'requires_auth': auth_required,
            'is_api': is_api,
            'response_time': response.elapsed.total_seconds()
        }
        
        return data
    
    def enumerate_common_endpoints(self):
        """Test common REST API endpoints"""
        logger.info("Starting enumeration of common endpoints...")
        
        common_paths = [
            # Admin endpoints
            '/rest/admin/application-configuration',
            '/rest/admin/users',
            '/rest/admin/products',
            '/rest/admin/settings',
            '/rest/admin/config',
            
            # User endpoints
            '/rest/user',
            '/rest/user/profile',
            '/rest/user/settings',
            '/rest/users',
            '/rest/users/',
            
            # Product endpoints
            '/rest/products',
            '/rest/products/',
            '/rest/product',
            '/rest/products/search',
            '/rest/products/1',
            '/rest/products/reviews',
            
            # Order endpoints
            '/rest/orders',
            '/rest/orders/',
            '/rest/order',
            '/rest/checkout',
            '/rest/basket',
            '/rest/basket/1',
            
            # Authentication endpoints
            '/rest/auth',
            '/rest/auth/login',
            '/rest/auth/register',
            '/rest/auth/logout',
            '/rest/auth/refresh',
            '/rest/login',
            '/rest/register',
            
            # General API paths
            '/rest/api',
            '/rest/v1',
            '/api/v1',
            '/api/users',
            '/api/products',
            '/api/orders',
            
            # Search/Feedback
            '/rest/search',
            '/rest/feedback',
            '/rest/reviews',
            '/rest/comments',
            
            # Challenge endpoints
            '/rest/challenges',
            '/rest/challenges/1',
            '/rest/scoreboard',
        ]
        
        methods = ['GET', 'POST', 'PUT', 'DELETE']
        
        for path in common_paths:
            for method in methods:
                response = self.test_endpoint(path, method)
                
                if response:
                    analysis = self.analyze_response(response, path, method)
                    if analysis:
                        self.results.append(analysis)
                        self.endpoints_found.add(f"{method} {path}")
                        
                        # Log findings
                        if response.status_code < 400:
                            logger.info(f"[{response.status_code}] {method:6} {path}")
                        elif response.status_code == 401:
                            logger.warning(f"[{response.status_code}] {method:6} {path} (Auth Required)")
                        elif response.status_code == 403:
                            logger.warning(f"[{response.status_code}] {method:6} {path} (Forbidden)")
    
    def test_authentication_bypass(self):
        """Test for authentication bypass on protected endpoints"""
        logger.info("\nTesting authentication bypass methods...")
        
        endpoints_to_test = [
            '/rest/admin/application-configuration',
            '/rest/admin/users',
            '/rest/user/profile',
        ]
        
        # Test with various auth bypass techniques
        bypass_techniques = [
            {},  # No auth
            {'Authorization': 'Bearer invalid'},
            {'Authorization': 'Bearer null'},
            {'X-Auth-Token': 'null'},
            {'Cookie': 'admin=1'},
            {'Cookie': 'authenticated=true'},
        ]
        
        for path in endpoints_to_test:
            for i, headers in enumerate(bypass_techniques):
                try:
                    url = urljoin(self.base_url, path)
                    response = requests.get(
                        url,
                        headers={**self.session.headers, **headers},
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        logger.warning(
                            f"BYPASS POSSIBLE: {path} - Technique {i} returned 200"
                        )
                        self.results.append({
                            'path': path,
                            'type': 'auth_bypass',
                            'technique': f'bypass_technique_{i}',
                            'status_code': response.status_code
                        })
                    
                    time.sleep(self.delay)
                    
                except Exception as e:
                    logger.debug(f"Bypass test error: {str(e)}")
    
    def test_http_methods(self):
        """Test support for various HTTP methods"""
        logger.info("\nTesting HTTP method support...")
        
        paths = [
            '/rest/admin/application-configuration',
            '/rest/products',
            '/rest/users',
        ]
        
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        
        for path in paths:
            for method in methods:
                response = self.test_endpoint(path, method)
                if response and response.status_code < 500:
                    logger.info(
                        f"[{response.status_code}] {method:7} {path}"
                    )
    
    def export_results(self, format_type='json'):
        """
        Export findings to file
        Args:
            format_type: 'json' or 'csv'
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == 'json':
            filename = f'api_enum_results_{timestamp}.json'
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results exported to {filename}")
            
        elif format_type == 'csv':
            filename = f'api_enum_results_{timestamp}.csv'
            if self.results:
                keys = self.results[0].keys()
                with open(filename, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(self.results)
                logger.info(f"Results exported to {filename}")
    
    def generate_report(self):
        """Generate and print summary report"""
        logger.info("\n" + "="*60)
        logger.info("API ENUMERATION REPORT")
        logger.info("="*60)
        logger.info(f"Target: {self.base_url}")
        logger.info(f"Total Endpoints Found: {len(self.endpoints_found)}")
        logger.info(f"Total Results: {len(self.results)}")
        
        # Categorize by status code
        status_codes = defaultdict(int)
        for result in self.results:
            if 'status_code' in result:
                status_codes[result['status_code']] += 1
        
        logger.info("\nStatus Code Distribution:")
        for code in sorted(status_codes.keys()):
            logger.info(f"  {code}: {status_codes[code]}")
        
        # API endpoints found
        api_endpoints = [r for r in self.results if r.get('is_api')]
        logger.info(f"\nAPI Endpoints: {len(api_endpoints)}")
        for ep in api_endpoints:
            logger.info(f"  {ep['method']:6} {ep['path']}")
        
        # Auth-required endpoints
        auth_endpoints = [r for r in self.results if r.get('requires_auth')]
        logger.info(f"\nAuthentication-Required Endpoints: {len(auth_endpoints)}")
        for ep in auth_endpoints:
            logger.info(f"  {ep['method']:6} {ep['path']}")
        
        logger.info("="*60)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Red Team API Enumeration Tool'
    )
    parser.add_argument(
        '-u', '--url',
        default='http://127.0.0.1:3000',
        help='Target URL (default: http://127.0.0.1:3000)'
    )
    parser.add_argument(
        '-t', '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds'
    )
    parser.add_argument(
        '-d', '--delay',
        type=float,
        default=0.1,
        help='Delay between requests in seconds'
    )
    parser.add_argument(
        '-e', '--export',
        choices=['json', 'csv', 'both'],
        default='json',
        help='Export format'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting API Enumeration...")
    logger.info(f"Target: {args.url}")
    
    enumerator = APIEnumerator(args.url, timeout=args.timeout, delay=args.delay)
    
    # Run enumeration
    enumerator.enumerate_common_endpoints()
    enumerator.test_authentication_bypass()
    enumerator.test_http_methods()
    
    # Export results
    if args.export in ['json', 'both']:
        enumerator.export_results('json')
    if args.export in ['csv', 'both']:
        enumerator.export_results('csv')
    
    # Generate report
    enumerator.generate_report()
    
    logger.info("Enumeration complete!")


if __name__ == '__main__':
    main()
