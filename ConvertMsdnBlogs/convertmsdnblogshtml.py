import datetime
from lxml import etree
import lxml.html
from markdownify import markdownify
import os
import requests
import shutil
import sys
import re
import urllib.request

def usage():
    print('Usage: %s path-to-folder-with-html-files output-path' % sys.argv[0])

def processDirectory(sourceDir, targetDir):
    filesProcessed=0
    print('Walking through %s' % sourceDir)
    for fileName in os.listdir(sourceDir):
        if fileName.endswith('.html'):
            processFile(fileName, sourceDir, targetDir)
            filesProcessed += 1
    print('\n****')
    print('Number of files processed: %d' % filesProcessed)
    return

def processFile(fileName, sourceDir, targetDir):
    print('Processing file %s' % fileName)
    fullFileName = os.path.join(sourceDir, fileName)
    # Note: had to use utf-8 encoding for being able to convert my files.
    # See this helpful post on Stackoverlfow:
    # https://stackoverflow.com/questions/49562499/how-to-fix-unicodedecodeerror-charmap-codec-cant-decode-byte-0x9d-in-posit
    with open(fullFileName, encoding='utf-8') as sourceFileStream:
        # Read the html
        html = sourceFileStream.read()
        htmlDoc = lxml.html.document_fromstring(html)
        # Extract the metadata for the pre-amble
        title, date = extractMetadata(htmlDoc)
        if date.year <= 2012:
            # Next convert the actual content to markdown
            mainContent = convertContent(htmlDoc)
            # Generate the filename from the tilte
            fileName = generateFileName(title, date.strftime('%Y-%m-%d'))
            # Finally, write the markdown output file
            print('-- %s\n-- %s\n-- %s' % (title, date, fileName))
            writeContents(targetDir, fileName, title, date, mainContent)
        else:
            print('-- Skipping all blogs after 2013 as they were cross-posts for the new blog!')
    return

def extractMetadata(htmlDoc):
    title = etree.tostring(htmlDoc.xpath('//h1[@class="entry-title"]')[0], method='text', encoding='utf-8').decode().strip()
    dateString = etree.tostring(htmlDoc.xpath('//time')[0], method='text', encoding='utf-8').strip().decode()
    dateFinal = datetime.datetime.strptime(dateString, '%m/%d/%Y %I:%M:%S %p')
    return title, dateFinal

def convertContent(htmlDoc):
    # Update links of which I have been able to backup media on GitHub before decommission of MSDN blogs.
    for someLink in htmlDoc.xpath('//a'):
        linkContent = someLink.attrib['href']
        linkContent = updateLink(linkContent)
        someLink.attrib['href'] = linkContent
        # Test the link
        # testLink(linkContent)
    
    # Also update image tags the same way
    for someImg in htmlDoc.xpath('//img'):
        imgSrc = someImg.attrib['src']
        imgSrc = updateLink(imgSrc)
        someImg.attrib['src'] = imgSrc
        # Test the link
        testLink(linkContent)

    content = etree.tostring(htmlDoc.xpath('//div[@id="content"]')[0], encoding='unicode')
    return markdownify(content)

def updateLink(linkContent):
    if linkContent.find('media/TNBlogsFS/') >= 0:
        # Replace the links that I've backed up images for on GitHub
        linkContent = linkContent.replace(
                        'media/TNBlogsFS/',
                        'https://github.com/mszcool/oldmsdnblogarchive/blob/master/media/TNBlogsFS/')
        linkContent = linkContent + '?raw=true'
    elif linkContent.find('media/MSDNBlogsFS/') >= 0:
        linkContent = linkContent.replace(
                        'media/MSDNBlogsFS/',
                        'https://github.com/mszcool/oldmsdnblogarchive/blob/master/media/MSDNBlogsFS/')
    else:
        return linkContent
    
    # Little hack to trick with GitHub raw file URL processing and URL Encoding/Decoding of file names containing %20 (uhm... hacky, but good enough)
    linkContent = linkContent + '?raw=true'
    linkContent = linkContent.replace('%20', '%2520')

    return linkContent

def testLink(linkContent):
    try:
        webUrl = urllib.request.urlopen(linkContent, timeout=10)
        respCode = webUrl.getcode()
        if respCode >= 200 and respCode < 400:
            return
        else:
            print('-- Found link returning none-success status code: %d %s' % (respCode, linkContent))
    except:
        print('-- Found link that lead to exception: %s' % linkContent)

def generateFileName(title, date):
    toRemove = ['&ndash;', '&gt;', '&lt;', '&le;', '&ge;', '...', '*', '@', '&', ';', ':', '-', '.', '/', ',', '?', '!', '"', '“', '”', '>', '<']
    for s in toRemove:
        title = title.replace(s, '')
    title = title.replace(' ', '-')
    title = title.replace('.', '-')
    return date + '-' +title.lower() + '.md'

def writeContents(targetDir, fileName, title, date, mainContent):
    # Generate the content string for the markdown
    post = '---\n'
    post += 'layout: post\n'
    post += 'title: %s\n' % title
    post += 'date: %s\n' % date
    post += 'categories: msdnblogarchive\n'
    post += 'tags: Archive MSDNBlog\n'
    post += '---\n\n%s' % mainContent

    # Write the new markdown file
    fullTargetName = os.path.join(targetDir, fileName)
    with open(fullTargetName, 'wb') as targetOut:
        targetOut.write(post.encode('utf-8'))
        print('-- converted %s' % fullTargetName)

    return

def main():
    # We need three arguments
    if len(sys.argv) != 3:
        usage()
        sys.exit(-1)

    # If the source path does not exist, print an error and exit
    source_directory = sys.argv[1]
    if not os.path.exists(source_directory):
        print('Source directory %s does not exist. Please choose a folder that exists and contains HTML files' % source_directory)
        sys.exit(-1)

    # If the target directory does not exist, create it
    target_directory = sys.argv[2]
    if not os.path.exists(target_directory):
        print('Target directory %s does not exist, creating it...' % target_directory)
        os.mkdir(target_directory)
    else:
        print('Target directory %s found, creating files there!' % target_directory)

    # Now process the directory and convert the files in it
    processDirectory(source_directory, target_directory)

    return

if __name__ == "__main__":
    main()