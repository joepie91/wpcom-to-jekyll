# WordPress.com-to-Jekyll converter

A simple converter. Export your (full) XML from your WordPress.com blog (Tools -> Export -> Export -> All Content), and run it through convert.py. The result will be Jekyll-compatible files.

Features:

* Processes WordPress HTML (including output from the older WordPress editors), including [caption] tags.
* Outputs all posts and pages as Markdown (*not HTML in a .md file!). Some post-processing is done to get a reasonable result.
* Downloads attachments and makes sure that all internal URLs (both for image attachments and links to other posts on the same blog) point to their new location on your Jekyll blog.
* "Shifts" headers, to make sure that post headers start at <h3>, so as to not mess up your Jekyll stylesheet.

The following are exported:

* Posts
* Drafts
* Pages
* All attachments for those posts and pages

This might also work with regular WordPress blogs, no idea. I've only tested it for WordPress.com.

## Usage

	python convert.py SOURCE [DESTINATION]

`SOURCE`: The source XML file to read your data from.
`DESTINATION`: *Optional.* Where to put the resulting files. Point this at your Jekyll project directory root, and it'll put everything in the right place.

## Result

Files in `_posts` and `_drafts` with, respectively, your posts and drafts and the appropriate metadata. Tags are included in the metadata, as a comma-separated list.

Creates a new directory with an index.html for each static page, so as to get clean URLs for them.

Stores all (image) attachments in the `attachments` directory, and rewrites all URLs for them.

A basic layout for a 'page' is already present in the `_layouts` directory in the repository; you should copy this, but it will overwrite any existing page.html layout (none in the default Jekyll project bootstrap).

## Caveats

* Be sure to manually check all your posts for any artifacts. The `html2text` library sometimes gets confused with styling, and it may misplace an underscore or asterisk.
* The converter can't deal with image floats. If you have floated images, you'll have to restore this with a custom stylesheet yourself.
* WordPress captions are placed as separate italicized paragraphs, directly under the corresponding images.
