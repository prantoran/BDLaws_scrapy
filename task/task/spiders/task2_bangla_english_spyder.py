import scrapy
import re
import urllib.parse as urlparse
import json
import io

def cleanstring(dirtystr):
    '''
    encapsulates reused string cleaning using regex
    '''
    dirtystr = re.sub('\r', '', dirtystr)
    dirtystr = re.sub('\n+', '\n', dirtystr)
    dirtystr = re.sub('\t+', ' ', dirtystr)
    dirtystr = re.sub(' +', ' ', dirtystr)
    dirtystr = re.sub(' \n', '\n', dirtystr)
    dirtystr = re.sub('\s+', ' ', dirtystr)
    dirtystr = dirtystr.lstrip()
    dirtystr = dirtystr.rstrip()
    return dirtystr

def pickstring( reglist, substring):
    '''
    given reglist is a nonempty list of strings,
    returns the string that contains substring
    '''
    for u in reglist:
        if substring.lower() in u.lower():
            return u
    return None

class QuotesSpider(scrapy.Spider):
    name = "t2_be"

    def start_requests(self):
        urlprefix = 'http://bdlaws.minlaw.gov.bd/print_sections_all.php?id='

        for i in range(0, 1226):
            url = urlprefix + str(i)
            yield scrapy.Request(url=url, callback=self.parse)



    def parse(self, response):
        url = response.url
        parsed = urlparse.urlparse(url)

        lawid = ''
        try:
            lawid = urlparse.parse_qs(parsed.query)['id'][0]
        except IndexError:
            lawid = 'invalid'

        title = ''
        act = ''
        preamble = ''
        created_at = ''

        title = response.xpath('//title/text()').extract_first()
        
        if isinstance(title, str):
            regex = re.compile(".*?\((.*?)\)")
            reglist = re.findall(regex, title)
            if reglist:
                act = pickstring(reglist, "ACT")
            title = re.sub(r'\([^)]*\)', '', title)
        print("act:", act)

        preamble = []
        preamblebold = response.css('td.midium_title b::text').extract_first()
        if preamblebold is None or preamblebold == '':
            plist = response.css('center::text').extract()
            preamblebold = ''
            notfirst = False
            for a in plist:
                a = cleanstring(a)
                if notfirst:
                    preamble += ' '
                notfirst = True
                preamblebold += a
                preamblebold = cleanstring(preamblebold)

        if preamblebold is not None:
            preamblebold = cleanstring(preamblebold)
            preamble.append(preamblebold)
            if title is None:
                title = preamblebold
                # if title is none, setting title to bold text of plausible preamble
                regex = re.compile(".*?\((.*?)\)")
                reglist = re.findall(regex, preamblebold)
                if reglist:
                    act = pickstring(reglist, "ACT")
                    # pattern found

        preambledetail = response.css('td.midium_title div::text').extract_first()
        if preambledetail is not None:
            preambledetail = cleanstring(preambledetail)
            preamble.append(preambledetail)

        datesectionlist = response.css('body table tr td table tr td.small_title i::text')
        datesection = datesectionlist.extract_first()
        if datesection is None:
            if title != None:
                regex = re.compile("\d{4}")
                reglist = re.findall(regex, title)
                if reglist:
                    datesection = reglist[0]
        created_at = datesection

        sectionid = 0

        sectionblock = response.css('table tr td table tr')

        sections = []

        for item in sectionblock:
            stitle = item.css('td.small_bold::text').extract_first()
            if isinstance(stitle, str):
                stitle = re.sub('\n+', '\n', stitle)
                stitle = re.sub('\t+', ' ', stitle)
                stitle = re.sub(' +', ' ', stitle)
                stext = item.xpath('.//div[contains(@class,"small_title")]').extract_first()

                atags = item.xpath('.//a')
                citedlaws = []
                wholeatags = []

                for a in atags:
                    atext = a.xpath('./text()').extract_first()
                    href = a.xpath('./@href').extract_first()
                    hrefurlparsed = urlparse.urlparse(href)
                    hrefurlparsed = urlparse.urlsplit(href)
                    q = hrefurlparsed.query

                    #query parameters
                    qp = urlparse.parse_qsl(q)

                    for qh, val in qp:
                        if qh == 'id' and val != lawid:
                            citedlaws.append({
                                'cited_law_id': val
                            })
                            wholeatags.append({
                                'cited_law_id': val,
                                'atag': atext
                            })

                for a in wholeatags:
                    atag = a['atag']
                    citetag = ' <cite>%s</cite>' % a['cited_law_id']
                    reptext = citetag + ' ' + atag
                    stext = re.sub(atag, reptext, stext, 1)
                stext = cleanstring(stext)
                stext = re.sub('<div.*?>', '', stext)
                stext = re.sub('</div>', '', stext)
                stext = re.sub('<br>', '', stext)
                stext = re.sub('<sup.*?>', '(ammendment: ', stext)
                stext = re.sub('</sup>', ')', stext)
                stext = re.sub('<b.*?>', '[', stext)
                stext = re.sub('</b>', ']', stext)

                stext = re.sub('<a.*?>', '', stext)
                stext = re.sub('</a>', '', stext)

                if isinstance(stext, str):

                    sectionid += 1

                    if len(citedlaws) > 0:
                        sections.append({
                            'id'        : sectionid,
                            'title'     : stitle,
                            'detail'    : stext,
                            'cited_laws': citedlaws
                        })


        if len(sections) > 0:
            yield {
                'id': lawid,
                'title': title,
                'act': act,
                'created_at': created_at,
                'sections': sections,
            }
