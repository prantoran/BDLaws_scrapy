## BDLaws scrapy:
- scraping BDLaws site using scrapy

### Running the crawlers
- $ scrapy crawl t1_be -o output/task1.json
- $ scrapy crawl t2_be -o output/task2.json
- No need to create output folder, autogenerated
- be: Bangla & English versions


## https://doc.scrapy.org/en/latest/intro/tutorial.html#creating-a-project

`scrapy startproject tutorial`

`scrapy crawl quotes`

### scrapy shell:

`scrapy shell 'http://bdlaws.minlaw.gov.bd/pdf_part.php?id=300'`

### CSS Selectors:

- returns a SelectorList
`response.css('title')`

- extracts the text from the title
`response.css('title::text').extract()`

- extracts the first element
`response.css('title::text').extract_first()`

- Using regular expressions
-- Returns texts starting with 'Quotes'
`response.css('title::text').re(r'Quotes.*')`
-- Returns words starting with 'Q'
`response.css('title::text').re(r'Q\w+')`
--
`response.css('title::text').re(r'(\w+) to (\w+)')`


`view(response)`


### XPath Selectors:

`response.xpath('//title')`

`response.xpath('//title/text()').extract_first()`



----------------------

`response.css("div.quote")`
`quote = response.css("div.quote")[0]`
`title = quote.css("span.text::text").extract_first()`
`author = quote.css("small.author::text").extract_first()`
`tags = quote.css("div.tags a.tag::text").extract()`
`response.css('li.next a::attr(href)').extract_first()`
