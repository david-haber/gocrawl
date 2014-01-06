from bs4 import BeautifulSoup
import urllib3
from lxml import etree
from urlparse import urlsplit, urljoin, urlunsplit
from collections import deque

class Page(object):
    """
    Holds all the information needed for a single page
    """

    def __init__(self, domain, url, content):
        self.domain = domain
        self.domain_netloc = urlsplit(domain)[1]
        self.url = url
        
        self.assets = []
        self.internal_links = []

        self.crawl_page(content) # no need to store content for now

    def crawl_page(self, content):

        # find links
        for href_tag in content.find_all(href=True):
            href = href_tag['href'].lower() # all lowercase, just making sure

            scheme, netloc, path, _, fragment = urlsplit(href)

            if len(netloc) > 0 and netloc != self.domain_netloc:
                continue # ignore external links

            if len(scheme) > 0 and scheme in ('mailto', 'javascript', 'tel'):
                continue # ignore

            if len(fragment) > 0:
                continue # ignore links that contain fragment

            if href == self.url:
                continue # ignore links to self

            if len(path) == 0:
                continue # ignore links without path (to domain)

            if href_tag.name == 'a':
                self.internal_links.append(href) # record internal link
            elif href_tag.name == 'link':
                self.assets.append(href) # record asset

        # find statics
        for src_tag in content.find_all(src=True):
            src = src_tag['src'].lower()
            self.assets.append(src)


class SiteMap(object):
    """
    Represents the sitemap of a website
    """

    def __init__(self, domain):
        """
        @ domain (str): domain from which this sitemap should be created
        """
        self.domain = domain
        self.pages = {} # create dictionary for pages already crawled
        self.crawl_domain()

    def crawl_domain(self):

        http = urllib3.PoolManager()

        urls_to_crawl = deque(['/'])

        while urls_to_crawl:

            curr_path = urls_to_crawl.popleft()

            if curr_path in self.pages:
                print "Warning: page already exists, skipping"
                continue

            curr_url = urljoin(self.domain, curr_path)

            print "Current url: %s" % curr_url
            # make request
            try:
                response = http.request('GET', curr_url)
            except:
                print "Could not get response from URL '%s', skipping this URL." % curr_url
                continue

            if response.status == 200:
                soup = BeautifulSoup(response.data, "lxml")
                page = Page(self.domain, curr_path, soup)

                for next_link_to_crawl in page.internal_links:
                    if next_link_to_crawl in self.pages \
                        or next_link_to_crawl in urls_to_crawl:
                        continue # ignore if already visited
                    urls_to_crawl.append(next_link_to_crawl)

                self.pages[curr_path] = page
            else:
                print "Received response with status '%s' from URL '%s', skipping this URL." % (response.status, curr_url)

        print len(http.pools)

    def __str__(self):
        output_string = ['SiteMap (%d pages):\n' % len(self.pages)]
        for page in self.pages.itervalues():
            output_string.append('Page: %s\n' % page.url)
            output_string.append('-> Assets\n')
            for asset in page.assets:
                output_string.append('%s\n' % asset)
            output_string.append('\n')
        return ''.join(output_string)
