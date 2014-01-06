from bs4 import BeautifulSoup
import urllib3
from lxml import etree
from urlparse import urlsplit, urljoin, urlunsplit
from collections import deque

class SiteMap(object):
    """
    Represents the sitemap of a website
    """

    def __init__(self, base_url, debug=False):
        """
        @ domain (str): domain from which this sitemap should be created
        """
        # Do some input validation
        url_split = urlsplit(base_url)
        if len(url_split[0]) > 0 and len(url_split[1]) > 0:
            # user entered http(s) and some domain
            self.base_url = base_url
        else:
            raise IOError("Wrong URL format, please enter 'http(s)://domain.com'")

        self.pages = {} # create dictionary for pages already crawled
        self.debug = debug
        self.crawl_domain()

    def crawl_domain(self):
        """
        Processes a single domain
        """
        http = urllib3.PoolManager()

        urls_to_crawl = deque(['/'])

        while urls_to_crawl:

            curr_path = urls_to_crawl.popleft()

            if curr_path in self.pages:
                print "Warning: page already exists, skipping"
                continue

            curr_url = urljoin(self.base_url, curr_path)
                
            if self.debug:
                print "Currently crawling: %s" % curr_url

            # make request
            try:
                response = http.request('GET', curr_url)
            except :
                print "Could not get response from URL '%s', skipping this URL." % curr_url
                continue

            if response.status == 200 and \
                    "text/html" in response.headers['content-type']:
                soup = BeautifulSoup(response.data, "lxml")
                page = Page(self.base_url, curr_path, soup)

                for next_link_to_crawl in page.internal_hrefs:
                    if next_link_to_crawl in self.pages \
                        or next_link_to_crawl in urls_to_crawl:
                        continue # ignore if already visited
                    urls_to_crawl.append(next_link_to_crawl)

                self.pages[curr_path] = page

    def __str__(self):
        output_string = ['SiteMap (%d pages):\n' % len(self.pages)]
        for page in self.pages.itervalues():
            output_string.append('Page: %s\n' % page.url)
            output_string.append('-> Assets\n')
            for asset in page.assets:
                output_string.append('%s\n' % asset)
            output_string.append('\n')
        return ''.join(output_string)

class Page(object):
    """
    Holds all the information needed for a single page
    """

    def __init__(self, domain, url, content):
        self.base_url = domain
        self.domain_netloc = urlsplit(domain)[1]
        self.url = url
        
        self.assets = []
        self.internal_hrefs = []

        self.crawl_page(content) # no need to store content for now

    def crawl_page(self, content):

        # find links
        for href_tag in content.find_all(href=True):
            href = href_tag['href'].lower() # all lowercase, just making sure

            scheme, netloc, path, _, _ = urlsplit(href)              
    
            if len(scheme) > 0 and scheme in ('mailto', 'javascript', 'tel'):
                continue # ignore

            if len(netloc) > 0 and netloc != self.domain_netloc:
                continue # ignore external links

            # make sure url has leading forward slash
            path = "/" + path.lstrip('/')

            # get path, removing query and fragments
            href = urlunsplit(('', '', path, '', ''))

            if href == self.url:
                continue # ignore links to self

            if len(path) == 0:
                continue # ignore links without path (to domain)

            if href_tag.name == 'a':
                self.internal_hrefs.append(href) # record internal link
            elif href_tag.name == 'link':
                self.assets.append(href) # record asset

        # find statics
        for src_tag in content.find_all(src=True):
            src = src_tag['src'].lower()
            self.assets.append(src)

