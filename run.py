from web import SiteMap
import time

if __name__ == '__main__':
    domain = \
        raw_input('Enter the base URL you want to crawl (include "http://"): ')
    print 'Start crawling %s ...' % domain

    start_t = time.time()
    sitemap = SiteMap(domain)
    elapsed = time.time() - start_t

    print 'Done.'
    print sitemap
    print "Time elapsed (sec): %f" % elapsed
