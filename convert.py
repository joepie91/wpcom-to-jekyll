import html2text, os, sys, email, urllib, re, shutil
from lxml import etree
from datetime import datetime

# https://gist.github.com/robertklep/2928188
def rfc822(timestamp):
	return datetime.fromtimestamp(email.Utils.mktime_tz(email.Utils.parsedate_tz(timestamp)))

def chomp_indent(text):
	return u"\n".join(line.lstrip() for line in text.split(u"\n"))

def markdownize(text):
	if "<p>" not in text:
		# Old-style posts, these don't have explicit HTML paragraph tags. Let's break it up into paragraphs.
		text = text.replace(u"\n<", u"\n\n<") # Add an extra newline before HTML tags at the start of a line, to prevent them from getting caught in a paragraph
		text = u"\n\n".join(u"<p>%s</p>" % paragraph for paragraph in re.split(u"\n{2,}", text))
	# Don't try to instantiate a single HTML2Text and use it for every post; it will break with a MemoryError
	htmlparser = html2text.HTML2Text()
	htmlparser.body_width = 0
	text = htmlparser.handle(text) # Parse HTML and convert to Markdown
	text = re.sub(u"(?<=\))\s*(.+?)(?=\[\/caption\])", u"\n\n*\\1*", text) # Replace captions with italicized text in a new paragraph... best-effort
	text = re.sub(u"\[caption [^\]]+\]", u"", text) # Remove WordPress [caption] prefix tags
	text = text.replace(u"[/caption]", u"") # ... and the postfix.
	return shift_headers(text) # Make every header one level lower, so as to fit in with the headers in the default Jekyll theme
	
def shift_headers(text):
	for x in xrange(6, 0, -1):
		text = text.replace(u"\n" + (u"#" * x) + u" ", u"\n" + (u"#" * (x + 2)) + u" ")
	return text

xml_path = sys.argv[1]

try:
	target_path = sys.argv[2]
	shutil.copy("_layouts/page.html", os.path.join(target_path, "_layouts"))
except IndexError, e:
	target_path = "."

drafts_path = os.path.join(target_path, "_drafts")
posts_path = os.path.join(target_path, "_posts")
attachments_path = os.path.join(target_path, "attachments")

for path in (posts_path, drafts_path, attachments_path):
	try:
		os.makedirs(path)
	except OSError, e:
		pass
	
with open(xml_path, "r") as xml_file:
	xml = etree.parse(xml_file)
	
xmlns = {
	"excerpt": "http://wordpress.org/export/1.2/excerpt/",
	"content": "http://purl.org/rss/1.0/modules/content/",
	"wfw": "http://wellformedweb.org/CommentAPI/",
	"dc": "http://purl.org/dc/elements/1.1/",
	"wp": "http://wordpress.org/export/1.2/",
}

draft_counter = 1
attachments = []
posts = []
pages = []

site_url = xml.xpath("/rss/channel/link/text()")[0]

print "Site URL: %s\n" % site_url

print "Parsing XML..."

for item in xml.xpath("/rss/channel/item"):
	post_type = item.xpath("wp:post_type/text()", namespaces=xmlns)[0]
	post_title = item.xpath("title/text()", namespaces=xmlns)[0]
	
	try:
		post_slug = item.xpath("wp:post_name/text()", namespaces=xmlns)[0]
	except IndexError, e:
		post_slug = "draft-%s" % str(draft_counter).zfill(3)  # Drafts do not have slugs...
		draft_counter += 1
	
	if post_type == "attachment":
		attachment_url = item.xpath("wp:attachment_url/text()", namespaces=xmlns)[0]
		
		attachments.append({
			"url": attachment_url,
			"filename": attachment_url.split("/")[-1].split("?")[0]
		})
		
		print "   attachment: %s" % attachment_url
	elif post_type == "page":
		post_body = markdownize(item.xpath("content:encoded/text()", namespaces=xmlns)[0])
		
		pages.append({
			"title": post_title,
			"body": post_body,
			"slug": post_slug
		})
		
		print "   page: %s" % post_title
	elif post_type == "post":
		post_status = item.xpath("wp:status/text()", namespaces=xmlns)[0]
		post_body = markdownize(item.xpath("content:encoded/text()", namespaces=xmlns)[0])
		post_date = rfc822(item.xpath("pubDate/text()", namespaces=xmlns)[0])
		post_tags = [tag for tag in item.xpath("category/text()") if tag != "Uncategorized"]
		if len(post_tags) == 0:
			post_tags = ["untagged"]
		
		posts.append({
			"title": post_title,
			"body": post_body,
			"slug": post_slug,
			"status": post_status,
			"date": post_date,
			"tags": post_tags
		})
		
		if post_status == "draft":
			print "   draft: %s (%s)" % (post_title, post_date)
		elif post_status == "publish":
			print "   post: %s (%s)" % (post_title, post_date)

print "Replacing image URLs..."

for post in posts + pages:
	for attachment in attachments:
		post["body"] = post["body"].replace(attachment["url"], os.path.join("{{ site.url }}/attachments", attachment["filename"]))

print "Fixing internal hyperlinks..."

for post in posts + pages:
	post["body"] = post["body"].replace(site_url, "../../../..")

print "Downloading attachments..."

for attachment in attachments:
	urllib.urlretrieve(attachment["url"], os.path.join(attachments_path, attachment["filename"]))
	print "   %s" % attachment["url"]
	
print "Generating Jekyll posts..."

for post in posts:
	if post["status"] == "publish":
		post_date = post["date"]
		
		with open(os.path.join(posts_path, "%s-%s-%s-%s.md" % (post_date.year, unicode(post_date.month).zfill(2), unicode(post_date.day).zfill(2), post["slug"])), "w") as f:
			f.write(chomp_indent(u"""---
				layout: post
				title: "%(title)s"
				permalink: %(year)s/%(month)s/%(day)s/%(slug)s
				postday: %(year)s/%(month)s/%(day)s
				posttime: %(hour)s_%(minute)s
				tags: %(tags)s
			---\n""" % {
				"title": post["title"],
				"slug": post["slug"],
				"tags": ", ".join(post["tags"]),
				"year": post_date.year,
				"month": unicode(post_date.month).zfill(2),
				"day": unicode(post_date.day).zfill(2),
				"hour": unicode(post_date.hour).zfill(2),
				"minute": unicode(post_date.minute).zfill(2)
			}).encode("utf-8"))
			f.write(post["body"].encode("utf-8"))
	elif post["status"] == "draft":
		post_date = post["date"]
		
		with open(os.path.join(drafts_path, "%s.md" % post["slug"]), "w") as f:
			f.write(chomp_indent(u"""---
				layout: post
				title: "%(title)s"
				tags: %(tags)s
			---\n""" % {
				"title": post["title"],
				"tags": ", ".join(post["tags"])
			}).encode("utf-8"))
			f.write(post["body"].encode("utf-8"))
			
print "Generating static pages..."

for page in pages:
	page_dir = os.path.join(target_path, page["slug"])
	
	try:
		os.makedirs(page_dir)
	except OSError, e:
		pass
		
	with open(os.path.join(page_dir, "index.md"), "w") as f:
		f.write(chomp_indent(u"""---
			layout: page
			title: "%(title)s"
		---\n""" % {
			"title": page["title"]
		}).encode("utf-8"))
		f.write(page["body"].encode("utf-8"))

print "Done!"
			
