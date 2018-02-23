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

class QuotesSpider(scrapy.Spider):
    '''
    encapsulates scrapy functions
    '''
    name = "t1_be"

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

        title = response.css('title::text').extract_first()
        if isinstance(title, str):
            regex = re.compile(".*?\((.*?)\)")
            reglist = re.findall(regex, title)
            if reglist:
                act = reglist[0]
            title = re.sub(r'\([^)]*\)', '', title)

        preamble = []
        preamblebold = response.css('td.midium_title b::text').extract_first()
        preamblebold = cleanstring(preamblebold)
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

        if preamblebold is not None:
            preamblebold = cleanstring(preamblebold)
            preamble.append(preamblebold)
            if title is None:
                title = preamblebold
                # if title is none, setting title to bold text of plausible preamble
                regex = re.compile(".*?\((.*?)\)")
                reglist = re.findall(regex, preamblebold)
                if reglist:
                    act = reglist[0]
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
                else:
                    datesection = ''
        created_at = datesection

        sectionid = 0

        sectionblock = response.css('table tr td table tr')

        sections = []

        for item in sectionblock:
            stitle = item.css('td.small_bold::text').extract_first()
            if isinstance(stitle, str):
                stitle = cleanstring(stitle)
                stext = item.xpath('.//div[contains(@class,"small_title")]').extract_first()
                stext = cleanstring(stext)
                stext = re.sub('<div.*?>', '', stext)
                stext = re.sub('</div>', '', stext)
                stext = re.sub('<br>', '', stext)
                stext = re.sub('<a.*?>', '', stext)
                stext = re.sub('</a>', '', stext)
                stext = re.sub('<sup.*?>', '(ammendment: ', stext)
                stext = re.sub('</sup>', ')', stext)
                stext = re.sub('<b.*?>', '[', stext)
                stext = re.sub('</b>', ']', stext)

                if isinstance(stext, str):
                    stext = cleanstring(stext)
                    sectionid += 1

                    sections.append({
                        "id": sectionid,
                        "title": stitle,
                        "detail": stext
                    })

        ammendmentblock = response.xpath('//tr//td//div[contains(@style,"font-size:10px")]')
        alist = ammendmentblock.extract_first()
        alist = re.sub('<div.*?>', '', alist)
        alist = re.sub('</div>', '', alist)
        alist = re.sub('<sup.*?>', '[', alist)
        alist = re.sub('</sup>', ']', alist)
        alist = alist.split('<br>')

        ammendments = []
        amenid = 0
        for item in alist:
            if item == '':
                continue
            amenid += 1
            atags = re.findall('<a.*?>*?</a>', item)
            item = re.sub('<a.*?>', '', item)
            item = re.sub('</a>', '', item)
            ammendments.append({
                'id': amenid,
                'ammendment': item,
                'atags': atags
            })

        yield {
            'id': lawid,
            'title': title,
            'act': act,
            'created_at': created_at,
            'preamble': preamble,
            'sections': sections,
            'ammendments': ammendments
        }

