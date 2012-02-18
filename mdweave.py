import markdown
import argparse
import codecs
import sys
import re

parser = argparse.ArgumentParser(description='A Python script that will produce nicely formatted and printable documentation from a Markdown document as an HTML file.')
parser.add_argument('-i', '--input', required=True, help='The path to the input Markdown file.')
parser.add_argument('-f', '--format', default='html5', help='The output format (xhtml | xhtml1 | xhtml5 | html | html4 | html5).')
parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0', help='The version inforamtion.')
args = parser.parse_args()

file = codecs.open(args.input, 'r', 'utf-8')
text = file.read()
file.close()
html = markdown.markdown(text, output_format=args.format)
if sys.version_info.major >= 3:
  sys.stdout.buffer.write(html.encode('utf-8'))
else:
  sys.stdout.write(html.encode('utf-8'))

